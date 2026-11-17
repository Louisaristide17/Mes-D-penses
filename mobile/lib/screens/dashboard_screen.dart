import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../charts.dart';
import '../format.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key, required this.onSeeAll});

  final VoidCallback onSeeAll;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  String _month = currentMonth();
  late Future<DashboardSummary> _summary;

  @override
  void initState() {
    super.initState();
    _summary = _load();
  }

  Future<DashboardSummary> _load() => context.read<ApiClient>().dashboard(_month);

  Future<void> _reload() async {
    final next = _load();
    setState(() => _summary = next);
    try {
      await next;
    } catch (_) {
      // L'erreur est affichée par le FutureBuilder.
    }
  }

  void _changeMonth(String month) {
    _month = month;
    _reload();
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _reload,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 24, 16, 96),
        children: [
          ScreenHeader(title: 'Tableau de bord', subtitle: 'Vos dépenses de ${monthLabel(_month).toLowerCase()}.'),
          const SizedBox(height: 16),
          MonthPicker(month: _month, onChanged: _changeMonth),
          const SizedBox(height: 16),
          FutureBuilder<DashboardSummary>(
            future: _summary,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) return const LoadingView();
              if (snapshot.hasError) {
                return ErrorView(message: snapshot.error.toString(), onRetry: _reload);
              }
              return _Content(summary: snapshot.data!, onSeeAll: widget.onSeeAll);
            },
          ),
        ],
      ),
    );
  }
}

class _Content extends StatelessWidget {
  const _Content({required this.summary, required this.onSeeAll});

  final DashboardSummary summary;
  final VoidCallback onSeeAll;

  @override
  Widget build(BuildContext context) {
    final top = summary.byCategory.isEmpty ? null : summary.byCategory.first;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Total du mois', style: AppText.label),
              const SizedBox(height: 8),
              Text(formatAmount(summary.total), style: AppText.stat),
              const SizedBox(height: 8),
              _Variation(variation: summary.variation),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _SmallStat(
                label: 'Dépenses',
                value: summary.count.toString(),
                note: summary.count > 0
                    ? '${formatAmount((summary.total / summary.count).round())} en moyenne'
                    : 'Aucune saisie',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _SmallStat(
                label: 'Premier poste',
                value: top?.category.name ?? 'Aucun',
                note: top == null ? 'Rien à afficher' : '${formatPercent(top.share)} du total',
              ),
            ),
          ],
        ),
        for (final alert in summary.alerts) ...[
          const SizedBox(height: 12),
          Notice(
            tone: alert.level == 'depasse' ? NoticeTone.error : NoticeTone.warning,
            text: alert.level == 'depasse'
                ? 'Budget ${alert.category.name} dépassé de ${formatAmount(-alert.remaining)}.'
                : 'Budget ${alert.category.name} consommé à ${formatPercent(alert.ratio)} : '
                    'il reste ${formatAmount(alert.remaining)}.',
          ),
        ],
        const SizedBox(height: 16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Évolution sur six mois', style: AppText.section),
              const SizedBox(height: 16),
              MonthlyBarChart(data: summary.monthly, selected: summary.month),
            ],
          ),
        ),
        const SizedBox(height: 16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Répartition par catégorie', style: AppText.section),
              const SizedBox(height: 16),
              if (summary.byCategory.isEmpty)
                Text('Aucune dépense à répartir pour ce mois.', style: AppText.body.copyWith(color: AppColors.muted))
              else
                CategoryDonut(rows: summary.byCategory),
            ],
          ),
        ),
        const SizedBox(height: 16),
        AppCard(
          padding: EdgeInsets.zero,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
                child: Row(
                  children: [
                    const Expanded(child: Text('Dernières dépenses', style: AppText.section)),
                    if (summary.recent.isNotEmpty)
                      TextButton(onPressed: onSeeAll, child: const Text('Tout voir'))
                    else
                      const SizedBox(height: 48),
                  ],
                ),
              ),
              const Divider(height: 1, color: AppColors.border),
              if (summary.recent.isEmpty)
                const EmptyState(
                  icon: Icons.receipt_long_outlined,
                  title: 'Aucune dépense ce mois-ci',
                  text: 'Ajoutez votre première dépense : le tableau de bord se remplira au fur et à mesure.',
                )
              else
                for (var i = 0; i < summary.recent.length; i++) ...[
                  if (i > 0) const Divider(height: 1, color: AppColors.border),
                  ExpenseRow(expense: summary.recent[i]),
                ],
            ],
          ),
        ),
      ],
    );
  }
}

class _Variation extends StatelessWidget {
  const _Variation({required this.variation});

  final double? variation;

  @override
  Widget build(BuildContext context) {
    final value = variation;
    if (value == null) {
      return const Text('Pas de dépense le mois précédent', style: AppText.small);
    }
    final rising = value > 0;
    // Une hausse des dépenses est signalée en rouge, une baisse en vert.
    final color = rising ? AppColors.danger : AppColors.success;
    return Row(
      children: [
        Icon(rising ? Icons.trending_up : Icons.trending_down, size: 16, color: color),
        const SizedBox(width: 4),
        Text(
          '${rising ? '+' : '-'}${formatPercent(value.abs())}',
          style: AppText.small.copyWith(color: color, fontWeight: FontWeight.w500),
        ),
        const SizedBox(width: 4),
        const Flexible(
          child: Text('par rapport au mois précédent', style: AppText.small, overflow: TextOverflow.ellipsis),
        ),
      ],
    );
  }
}

class _SmallStat extends StatelessWidget {
  const _SmallStat({required this.label, required this.value, required this.note});

  final String label;
  final String value;
  final String note;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppText.label),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600, height: 1.2),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 8),
          Text(note, style: AppText.small, maxLines: 1, overflow: TextOverflow.ellipsis),
        ],
      ),
    );
  }
}
