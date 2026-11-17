import 'package:flutter/material.dart';

import 'format.dart';
import 'models.dart';
import 'theme.dart';

class AppCard extends StatelessWidget {
  const AppCard({super.key, required this.child, this.padding = const EdgeInsets.all(16)});

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(kRadius),
        border: Border.all(color: AppColors.border),
        boxShadow: const [BoxShadow(color: Color(0x0D16201C), blurRadius: 2, offset: Offset(0, 1))],
      ),
      child: child,
    );
  }
}

enum NoticeTone { error, warning, success }

class Notice extends StatelessWidget {
  const Notice({super.key, required this.text, this.tone = NoticeTone.error});

  final String text;
  final NoticeTone tone;

  @override
  Widget build(BuildContext context) {
    late final Color background;
    late final Color foreground;
    late final IconData icon;
    switch (tone) {
      case NoticeTone.error:
        background = AppColors.dangerSoft;
        foreground = AppColors.danger;
        icon = Icons.error_outline;
      case NoticeTone.warning:
        background = AppColors.warningSoft;
        foreground = AppColors.warningText;
        icon = Icons.warning_amber_outlined;
      case NoticeTone.success:
        background = AppColors.successSoft;
        foreground = AppColors.success;
        icon = Icons.check_circle_outline;
    }
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: background, borderRadius: BorderRadius.circular(kRadius)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: foreground),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: AppText.body.copyWith(color: foreground))),
        ],
      ),
    );
  }
}

const Map<String, IconData> _categoryIcons = {
  'utensils': Icons.restaurant_outlined,
  'bus': Icons.directions_bus_outlined,
  'home': Icons.home_outlined,
  'receipt': Icons.receipt_long_outlined,
  'smartphone': Icons.smartphone_outlined,
  'heart-pulse': Icons.monitor_heart_outlined,
  'graduation-cap': Icons.school_outlined,
  'ticket': Icons.confirmation_number_outlined,
  'shirt': Icons.checkroom_outlined,
  'circle-ellipsis': Icons.more_horiz,
  'users': Icons.group_outlined,
  'gift': Icons.card_giftcard_outlined,
  'piggy-bank': Icons.savings_outlined,
  'briefcase': Icons.work_outline,
  'car': Icons.directions_car_outlined,
  'plane': Icons.flight_outlined,
  'tag': Icons.sell_outlined,
};

class CategoryAvatar extends StatelessWidget {
  const CategoryAvatar({super.key, required this.category, this.size = 36});

  final ExpenseCategory category;
  final double size;

  @override
  Widget build(BuildContext context) {
    final color = colorFromHex(category.color);
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(color: color.withAlpha(31), borderRadius: BorderRadius.circular(kRadius)),
      child: Icon(_categoryIcons[category.icon] ?? Icons.sell_outlined, size: size * 0.55, color: color),
    );
  }
}

class MonthPicker extends StatelessWidget {
  const MonthPicker({super.key, required this.month, required this.onChanged, this.allowFuture = false});

  final String month;
  final ValueChanged<String> onChanged;
  final bool allowFuture;

  @override
  Widget build(BuildContext context) {
    final atLimit = !allowFuture && month.compareTo(currentMonth()) >= 0;
    return Container(
      height: 44,
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(kRadius),
        border: Border.all(color: AppColors.borderStrong),
      ),
      child: Row(
        children: [
          IconButton(
            tooltip: 'Mois précédent',
            icon: const Icon(Icons.chevron_left, size: 20),
            onPressed: () => onChanged(shiftMonth(month, -1)),
          ),
          Expanded(child: Text(monthLabel(month), textAlign: TextAlign.center, style: AppText.strong)),
          IconButton(
            tooltip: 'Mois suivant',
            icon: const Icon(Icons.chevron_right, size: 20),
            onPressed: atLimit ? null : () => onChanged(shiftMonth(month, 1)),
          ),
        ],
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.icon, required this.title, required this.text, this.action});

  final IconData icon;
  final String title;
  final String text;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
      child: Column(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: const BoxDecoration(color: AppColors.bg, shape: BoxShape.circle),
            child: Icon(icon, color: AppColors.muted),
          ),
          const SizedBox(height: 16),
          Text(title, style: AppText.section, textAlign: TextAlign.center),
          const SizedBox(height: 8),
          Text(text, style: AppText.body.copyWith(color: AppColors.muted), textAlign: TextAlign.center),
          if (action != null) ...[const SizedBox(height: 16), action!],
        ],
      ),
    );
  }
}

class LoadingView extends StatelessWidget {
  const LoadingView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 64),
      child: Center(
        child: SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2.5)),
      ),
    );
  }
}

class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Notice(text: message),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          style: secondaryButtonStyle(),
          onPressed: onRetry,
          icon: const Icon(Icons.refresh, size: 18),
          label: const Text('Réessayer'),
        ),
      ],
    );
  }
}

/// Ligne d'une dépense : icône de catégorie, note, date et montant.
class ExpenseRow extends StatelessWidget {
  const ExpenseRow({super.key, required this.expense, this.onTap});

  final Expense expense;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            CategoryAvatar(category: expense.category),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    expense.note.isEmpty ? expense.category.name : expense.note,
                    style: AppText.strong,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text('${expense.category.name} · ${formatDate(expense.date)}', style: AppText.small),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Text(formatAmount(expense.amount), style: AppText.amount),
          ],
        ),
      ),
    );
  }
}

/// En-tête commun aux écrans : titre, sous-titre et action facultative.
class ScreenHeader extends StatelessWidget {
  const ScreenHeader({super.key, required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: AppText.title),
        const SizedBox(height: 4),
        Text(subtitle, style: AppText.body.copyWith(color: AppColors.muted)),
      ],
    );
  }
}

void showMessage(BuildContext context, String text) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(text), behavior: SnackBarBehavior.floating));
}
