import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../format.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets.dart';
import 'expense_form.dart';

const _accents = {
  'à': 'a', 'â': 'a', 'ä': 'a',
  'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
  'î': 'i', 'ï': 'i',
  'ô': 'o', 'ö': 'o',
  'ù': 'u', 'û': 'u', 'ü': 'u',
  'ç': 'c', 'œ': 'oe',
};

/// Met en minuscules et retire les accents, pour que "attieke" trouve "Attiéké".
String _normalize(String text) {
  final buffer = StringBuffer();
  for (final char in text.toLowerCase().split('')) {
    buffer.write(_accents[char] ?? char);
  }
  return buffer.toString();
}

/// Vrai si chaque mot de la recherche figure dans la note, la catégorie,
/// le montant ou la date de la dépense.
bool _matches(Expense expense, String query) {
  final words = _normalize(query).split(RegExp(r'\s+')).where((word) => word.isNotEmpty);
  if (words.isEmpty) return true;
  final haystack = _normalize(
    '${expense.note} ${expense.category.name} ${expense.amount} ${formatDate(expense.date)}',
  );
  return words.every((word) => haystack.contains(word));
}

class ExpensesScreen extends StatefulWidget {
  const ExpensesScreen({super.key});

  @override
  State<ExpensesScreen> createState() => _ExpensesScreenState();
}

class _ExpensesScreenState extends State<ExpensesScreen> {
  final _search = TextEditingController();
  String _month = currentMonth();
  String _query = '';
  late Future<ExpensePage> _page;

  @override
  void initState() {
    super.initState();
    _page = _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<ExpensePage> _load() {
    return context.read<ApiClient>().expenses(dateFrom: firstDayOf(_month), dateTo: lastDayOf(_month));
  }

  Future<void> _reload() async {
    final next = _load();
    setState(() => _page = next);
    try {
      await next;
    } catch (_) {
      // L'erreur est affichée par le FutureBuilder.
    }
  }

  void _clearSearch() {
    _search.clear();
    setState(() => _query = '');
  }

  Future<void> _edit(Expense expense) async {
    final changed = await showExpenseForm(context, expense: expense);
    if (changed && mounted) _reload();
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _reload,
      child: ListView(
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        padding: const EdgeInsets.fromLTRB(16, 24, 16, 96),
        children: [
          const ScreenHeader(title: 'Dépenses', subtitle: 'Touchez une dépense pour la modifier.'),
          const SizedBox(height: 16),
          MonthPicker(
            month: _month,
            onChanged: (month) {
              _month = month;
              _reload();
            },
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _search,
            // La liste du mois est déjà chargée : le filtre s'applique à chaque lettre, sans appel réseau.
            onChanged: (value) => setState(() => _query = value),
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => FocusScope.of(context).unfocus(),
            decoration: fieldDecoration(
              'Recherche',
              hint: 'Note, catégorie ou montant',
              prefixIcon: const Icon(Icons.search, size: 20),
            ).copyWith(
              suffixIcon: _query.isEmpty
                  ? null
                  : IconButton(
                      tooltip: 'Effacer la recherche',
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: _clearSearch,
                    ),
            ),
          ),
          const SizedBox(height: 16),
          FutureBuilder<ExpensePage>(
            future: _page,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) return const LoadingView();
              if (snapshot.hasError) {
                return ErrorView(message: snapshot.error.toString(), onRetry: _reload);
              }
              final page = snapshot.data!;
              return _List(
                items: page.items.where((expense) => _matches(expense, _query)).toList(),
                loaded: page.items.length,
                available: page.total,
                searching: _query.trim().isNotEmpty,
                onTap: _edit,
                onClearSearch: _clearSearch,
              );
            },
          ),
        ],
      ),
    );
  }
}

class _List extends StatelessWidget {
  const _List({
    required this.items,
    required this.loaded,
    required this.available,
    required this.searching,
    required this.onTap,
    required this.onClearSearch,
  });

  /// Dépenses à afficher, après application de la recherche.
  final List<Expense> items;

  /// Nombre de dépenses chargées pour le mois, et nombre total côté serveur.
  final int loaded;
  final int available;
  final bool searching;
  final ValueChanged<Expense> onTap;
  final VoidCallback onClearSearch;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return AppCard(
        padding: EdgeInsets.zero,
        child: EmptyState(
          icon: searching ? Icons.search_off : Icons.receipt_long_outlined,
          title: searching ? 'Aucun résultat' : 'Aucune dépense ce mois-ci',
          text: searching
              ? 'Aucune dépense de ce mois ne correspond à votre recherche.'
              : 'Utilisez le bouton Nouvelle dépense pour en ajouter une.',
          action: searching
              ? OutlinedButton(
                  style: secondaryButtonStyle(),
                  onPressed: onClearSearch,
                  child: const Text('Effacer la recherche'),
                )
              : null,
        ),
      );
    }
    final total = items.fold<int>(0, (sum, expense) => sum + expense.amount);
    final count = searching ? '${items.length} résultat(s) sur $loaded' : '${items.length} dépense(s)';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(count, style: AppText.small),
              Text('Total : ${formatAmount(total)}', style: AppText.small),
            ],
          ),
        ),
        AppCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              for (var i = 0; i < items.length; i++) ...[
                if (i > 0) const Divider(height: 1, color: AppColors.border),
                ExpenseRow(expense: items[i], onTap: () => onTap(items[i])),
              ],
            ],
          ),
        ),
        if (available > loaded)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(
              'Seules les $loaded dépenses les plus récentes du mois sont chargées, sur $available.',
              style: AppText.small,
              textAlign: TextAlign.center,
            ),
          ),
      ],
    );
  }
}
