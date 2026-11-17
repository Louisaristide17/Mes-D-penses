import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../format.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets.dart';

class BudgetsScreen extends StatefulWidget {
  const BudgetsScreen({super.key});

  @override
  State<BudgetsScreen> createState() => _BudgetsScreenState();
}

class _BudgetsScreenState extends State<BudgetsScreen> {
  String _month = currentMonth();
  late Future<List<BudgetStatus>> _statuses;

  @override
  void initState() {
    super.initState();
    _statuses = _load();
  }

  Future<List<BudgetStatus>> _load() => context.read<ApiClient>().budgetStatuses(_month);

  Future<void> _reload() async {
    final next = _load();
    setState(() => _statuses = next);
    try {
      await next;
    } catch (_) {
      // L'erreur est affichée par le FutureBuilder.
    }
  }

  Future<void> _openForm({BudgetStatus? budget, List<BudgetStatus> existing = const []}) async {
    final saved = await showDialog<bool>(
      context: context,
      builder: (_) => _BudgetDialog(month: _month, budget: budget, existing: existing),
    );
    if (saved == true && mounted) _reload();
  }

  Future<void> _delete(BudgetStatus status) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Supprimer le budget'),
        content: Text(
          'Le budget ${status.category.name} de ${monthLabel(_month).toLowerCase()} sera supprimé. '
          'Vos dépenses ne sont pas modifiées.',
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
    try {
      await context.read<ApiClient>().deleteBudget(status.budgetId);
      if (mounted) _reload();
    } on ApiException catch (failure) {
      if (mounted) showMessage(context, failure.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _reload,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 24, 16, 32),
        children: [
          const ScreenHeader(title: 'Budgets', subtitle: 'Un plafond mensuel par catégorie.'),
          const SizedBox(height: 16),
          MonthPicker(
            month: _month,
            allowFuture: true,
            onChanged: (month) {
              _month = month;
              _reload();
            },
          ),
          const SizedBox(height: 16),
          FutureBuilder<List<BudgetStatus>>(
            future: _statuses,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) return const LoadingView();
              if (snapshot.hasError) {
                return ErrorView(message: snapshot.error.toString(), onRetry: _reload);
              }
              final statuses = snapshot.data!;
              final addButton = FilledButton.icon(
                style: primaryButtonStyle(),
                onPressed: () => _openForm(existing: statuses),
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Nouveau budget'),
              );
              if (statuses.isEmpty) {
                return AppCard(
                  padding: EdgeInsets.zero,
                  child: EmptyState(
                    icon: Icons.track_changes_outlined,
                    title: 'Aucun budget pour ${monthLabel(_month).toLowerCase()}',
                    text: 'Vous êtes prévenu à 80 % du plafond, puis en cas de dépassement.',
                    action: addButton,
                  ),
                );
              }
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final status in statuses) ...[
                    _BudgetCard(
                      status: status,
                      onEdit: () => _openForm(budget: status),
                      onDelete: () => _delete(status),
                    ),
                    const SizedBox(height: 12),
                  ],
                  const SizedBox(height: 4),
                  addButton,
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

class _BudgetCard extends StatelessWidget {
  const _BudgetCard({required this.status, required this.onEdit, required this.onDelete});

  final BudgetStatus status;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    late final Color color;
    late final Color soft;
    late final Color badgeText;
    late final String label;
    switch (status.level) {
      case 'depasse':
        color = AppColors.danger;
        soft = AppColors.dangerSoft;
        badgeText = AppColors.danger;
        label = 'Dépassé';
      case 'attention':
        color = AppColors.warning;
        soft = AppColors.warningSoft;
        badgeText = AppColors.warningText;
        label = 'Bientôt atteint';
      default:
        color = AppColors.primary;
        soft = AppColors.successSoft;
        badgeText = AppColors.success;
        label = 'Dans le budget';
    }
    final over = status.remaining < 0;

    return AppCard(
      padding: const EdgeInsets.fromLTRB(16, 8, 4, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CategoryAvatar(category: status.category, size: 32),
              const SizedBox(width: 12),
              Expanded(
                child: Text(status.category.name, style: AppText.strong, overflow: TextOverflow.ellipsis),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: soft, borderRadius: BorderRadius.circular(11)),
                child: Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: badgeText)),
              ),
              PopupMenuButton<String>(
                tooltip: 'Actions',
                icon: const Icon(Icons.more_vert, size: 20, color: AppColors.muted),
                onSelected: (action) {
                  if (action == 'edit') {
                    onEdit();
                  } else {
                    onDelete();
                  }
                },
                itemBuilder: (_) => const [
                  PopupMenuItem<String>(value: 'edit', child: Text('Modifier le plafond')),
                  PopupMenuItem<String>(value: 'delete', child: Text('Supprimer')),
                ],
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: status.ratio.clamp(0.0, 1.0).toDouble(),
                    minHeight: 8,
                    backgroundColor: AppColors.bg,
                    valueColor: AlwaysStoppedAnimation<Color>(color),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '${formatAmount(status.spent)} sur ${formatAmount(status.ceiling)} (${formatPercent(status.ratio)})',
                  style: AppText.small,
                ),
                const SizedBox(height: 2),
                Text(
                  over
                      ? 'Dépassement de ${formatAmount(-status.remaining)}'
                      : 'Reste ${formatAmount(status.remaining)}',
                  style: AppText.small.copyWith(
                    color: over ? AppColors.danger : AppColors.text,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BudgetDialog extends StatefulWidget {
  const _BudgetDialog({required this.month, required this.budget, required this.existing});

  final String month;
  final BudgetStatus? budget;
  final List<BudgetStatus> existing;

  @override
  State<_BudgetDialog> createState() => _BudgetDialogState();
}

class _BudgetDialogState extends State<_BudgetDialog> {
  late final TextEditingController _ceiling;
  List<ExpenseCategory> _available = const [];
  int? _categoryId;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final budget = widget.budget;
    _ceiling = TextEditingController(text: budget == null ? '' : budget.ceiling.toString());
    if (budget != null) {
      _available = [budget.category];
      _categoryId = budget.category.id;
      _loading = false;
    } else {
      _loadCategories();
    }
  }

  @override
  void dispose() {
    _ceiling.dispose();
    super.dispose();
  }

  Future<void> _loadCategories() async {
    try {
      final categories = await context.read<ApiClient>().categories();
      final used = widget.existing.map((status) => status.category.id).toSet();
      final available = categories.where((category) => !used.contains(category.id)).toList();
      if (!mounted) return;
      setState(() {
        _available = available;
        _categoryId = available.isEmpty ? null : available.first.id;
        _loading = false;
      });
    } on ApiException catch (failure) {
      if (!mounted) return;
      setState(() {
        _error = failure.message;
        _loading = false;
      });
    }
  }

  Future<void> _save() async {
    final ceiling = parseAmount(_ceiling.text);
    final categoryId = _categoryId;
    if (categoryId == null) return;
    if (ceiling == null || ceiling <= 0) {
      setState(() => _error = 'Indiquez un plafond supérieur à zéro.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    final api = context.read<ApiClient>();
    final navigator = Navigator.of(context);
    try {
      await api.setBudget(categoryId: categoryId, month: widget.month, ceiling: ceiling);
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
    final editing = widget.budget != null;
    final nothingLeft = !_loading && _available.isEmpty;

    return AlertDialog(
      backgroundColor: AppColors.surface,
      surfaceTintColor: Colors.transparent,
      title: Text(editing ? 'Modifier le plafond' : 'Nouveau budget', style: AppText.section),
      content: SizedBox(
        width: 360,
        child: _loading
            ? const LoadingView()
            : Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_error != null) ...[Notice(text: _error!), const SizedBox(height: 16)],
                  if (nothingLeft)
                    const Text('Toutes vos catégories ont déjà un budget ce mois-ci.', style: AppText.body)
                  else ...[
                    DropdownButtonFormField<int>(
                      initialValue: _categoryId,
                      isExpanded: true,
                      decoration: fieldDecoration('Catégorie'),
                      items: [
                        for (final category in _available)
                          DropdownMenuItem<int>(value: category.id, child: Text(category.name)),
                      ],
                      onChanged: editing ? null : (value) => setState(() => _categoryId = value),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _ceiling,
                      autofocus: true,
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      onSubmitted: (_) => _save(),
                      decoration: fieldDecoration(
                        'Plafond pour ${monthLabel(widget.month).toLowerCase()}',
                        suffix: 'FCFA',
                      ),
                    ),
                  ],
                ],
              ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Annuler')),
        if (!nothingLeft)
          FilledButton(
            style: primaryButtonStyle(),
            onPressed: _saving || _loading ? null : _save,
            child: const Text('Enregistrer'),
          ),
      ],
    );
  }
}
