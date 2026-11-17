import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../format.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets.dart';

/// Ouvre le formulaire d'ajout ou de modification. Renvoie true si une dépense
/// a été enregistrée ou supprimée.
Future<bool> showExpenseForm(BuildContext context, {Expense? expense}) async {
  final changed = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.surface,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
    builder: (_) => _ExpenseForm(expense: expense),
  );
  return changed ?? false;
}

class _ExpenseForm extends StatefulWidget {
  const _ExpenseForm({this.expense});

  final Expense? expense;

  @override
  State<_ExpenseForm> createState() => _ExpenseFormState();
}

class _ExpenseFormState extends State<_ExpenseForm> {
  late final TextEditingController _amount;
  late final TextEditingController _note;
  late DateTime _date;

  /// null signifie "Automatique" : la catégorie est choisie par l'API.
  int? _categoryId;

  List<ExpenseCategory> _categories = const [];
  Suggestion? _suggestion;
  Timer? _debounce;
  bool _saving = false;
  String? _error;

  bool get _editing => widget.expense != null;

  @override
  void initState() {
    super.initState();
    final expense = widget.expense;
    _amount = TextEditingController(text: expense == null ? '' : expense.amount.toString());
    _note = TextEditingController(text: expense?.note ?? '');
    _date = expense?.date ?? DateTime.now();
    _categoryId = expense?.category.id;
    _loadCategories();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _amount.dispose();
    _note.dispose();
    super.dispose();
  }

  Future<void> _loadCategories() async {
    try {
      final categories = await context.read<ApiClient>().categories();
      if (mounted) setState(() => _categories = categories);
    } on ApiException catch (failure) {
      if (mounted) setState(() => _error = failure.message);
    }
  }

  // La suggestion est demandée une fois la frappe interrompue, pas à chaque lettre.
  void _onNoteChanged(String value) {
    _debounce?.cancel();
    final text = value.trim();
    if (text.length < 3) {
      setState(() => _suggestion = null);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 350), () async {
      try {
        final suggestion = await context.read<ApiClient>().suggestCategory(text);
        if (mounted && _note.text.trim() == text) {
          setState(() => _suggestion = suggestion.category == null ? null : suggestion);
        }
      } on ApiException {
        if (mounted) setState(() => _suggestion = null);
      }
    });
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(now.year - 5),
      lastDate: DateTime(now.year + 1, 12, 31),
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _save() async {
    final amount = parseAmount(_amount.text);
    if (amount == null || amount <= 0) {
      setState(() => _error = 'Indiquez un montant supérieur à zéro.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    final api = context.read<ApiClient>();
    final navigator = Navigator.of(context);
    try {
      final expense = widget.expense;
      if (expense == null) {
        await api.createExpense(
          amount: amount,
          date: toIsoDay(_date),
          note: _note.text.trim(),
          categoryId: _categoryId,
        );
      } else {
        await api.updateExpense(
          expense.id,
          amount: amount,
          date: toIsoDay(_date),
          note: _note.text.trim(),
          categoryId: _categoryId ?? expense.category.id,
        );
      }
      navigator.pop(true);
    } on ApiException catch (failure) {
      if (!mounted) return;
      setState(() {
        _error = failure.message;
        _saving = false;
      });
    }
  }

  Future<void> _delete() async {
    final expense = widget.expense!;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Supprimer la dépense'),
        content: Text(
          'La dépense de ${formatAmount(expense.amount)} du ${formatDate(expense.date)} sera supprimée définitivement.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Annuler')),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppColors.danger),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _saving = true);
    final api = context.read<ApiClient>();
    final navigator = Navigator.of(context);
    try {
      await api.deleteExpense(expense.id);
      navigator.pop(true);
    } on ApiException catch (failure) {
      if (!mounted) return;
      setState(() {
        _error = failure.message;
        _saving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final suggested = _suggestion?.category;

    return Padding(
      // Le formulaire remonte au-dessus du clavier.
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(_editing ? 'Modifier la dépense' : 'Nouvelle dépense', style: AppText.section),
                  ),
                  IconButton(
                    tooltip: 'Fermer',
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => Navigator.of(context).pop(false),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (_error != null) ...[Notice(text: _error!), const SizedBox(height: 16)],
              TextField(
                controller: _amount,
                autofocus: !_editing,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                textInputAction: TextInputAction.next,
                style: AppText.amount.copyWith(fontSize: 16),
                decoration: fieldDecoration('Montant', suffix: 'FCFA'),
              ),
              const SizedBox(height: 16),
              InkWell(
                onTap: _pickDate,
                borderRadius: BorderRadius.circular(kRadius),
                child: InputDecorator(
                  decoration: fieldDecoration(
                    'Date',
                    prefixIcon: const Icon(Icons.calendar_today_outlined, size: 18),
                  ),
                  child: Text(formatDate(_date), style: AppText.body),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _note,
                maxLength: 255,
                textCapitalization: TextCapitalization.sentences,
                onChanged: _onNoteChanged,
                decoration: fieldDecoration('Note', hint: 'Taxi pour Cocody, facture CIE, marché...')
                    .copyWith(counterText: ''),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<int?>(
                // La clé force la reconstruction quand la valeur change depuis la suggestion.
                key: ValueKey('category-$_categoryId-${_categories.length}'),
                initialValue: _categories.any((category) => category.id == _categoryId) ? _categoryId : null,
                isExpanded: true,
                decoration: fieldDecoration(
                  'Catégorie',
                  helper: !_editing && _categoryId == null && suggested == null
                      ? 'Choisie pour vous à partir de la note.'
                      : null,
                ),
                items: [
                  if (!_editing) const DropdownMenuItem<int?>(value: null, child: Text('Automatique')),
                  for (final category in _categories)
                    DropdownMenuItem<int?>(value: category.id, child: Text(category.name)),
                ],
                onChanged: (value) => setState(() => _categoryId = value),
              ),
              if (suggested != null && suggested.id != _categoryId) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.only(left: 12),
                  decoration: BoxDecoration(
                    color: AppColors.primarySoft,
                    borderRadius: BorderRadius.circular(kRadius),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.sell_outlined, size: 16, color: AppColors.primary),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Catégorie suggérée : ${suggested.name} '
                          '(${formatPercent(_suggestion!.confidence)} de confiance)',
                          style: const TextStyle(fontSize: 12),
                        ),
                      ),
                      TextButton(
                        onPressed: () => setState(() => _categoryId = suggested.id),
                        child: const Text('Appliquer'),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 24),
              FilledButton(
                style: primaryButtonStyle(),
                onPressed: _saving ? null : _save,
                child: Text(_editing ? 'Enregistrer' : 'Ajouter la dépense'),
              ),
              if (_editing) ...[
                const SizedBox(height: 8),
                TextButton.icon(
                  onPressed: _saving ? null : _delete,
                  style: TextButton.styleFrom(foregroundColor: AppColors.danger, minimumSize: const Size(0, 48)),
                  icon: const Icon(Icons.delete_outline, size: 18),
                  label: const Text('Supprimer la dépense'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
