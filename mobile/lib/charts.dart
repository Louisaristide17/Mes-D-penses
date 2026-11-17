import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'format.dart';
import 'models.dart';
import 'theme.dart';

const _axisStyle = TextStyle(fontSize: 11, color: AppColors.muted);

void _drawText(Canvas canvas, String text, Offset Function(Size size) position) {
  final painter = TextPainter(
    text: TextSpan(text: text, style: _axisStyle),
    textDirection: TextDirection.ltr,
  )..layout();
  painter.paint(canvas, position(painter.size));
}

/// Arrondit le maximum à une valeur ronde pour graduer l'axe (87 000 devient 90 000).
int niceCeiling(int value) {
  if (value <= 0) return 1;
  final magnitude = math.pow(10, value.toString().length - 1).toInt();
  return (value / magnitude).ceil() * magnitude;
}

/// Histogramme des totaux mensuels. Le mois affiché est mis en avant.
class MonthlyBarChart extends StatelessWidget {
  const MonthlyBarChart({super.key, required this.data, required this.selected});

  final List<MonthTotal> data;
  final String selected;

  @override
  Widget build(BuildContext context) {
    final description = data.map((row) => '${monthLabel(row.month)} : ${formatAmount(row.total)}').join(', ');
    return Semantics(
      label: 'Dépenses par mois. $description',
      child: SizedBox(
        height: 200,
        width: double.infinity,
        child: CustomPaint(painter: _BarPainter(data, selected)),
      ),
    );
  }
}

class _BarPainter extends CustomPainter {
  _BarPainter(this.data, this.selected);

  final List<MonthTotal> data;
  final String selected;

  static const double _axisWidth = 40;
  static const double _labelHeight = 24;
  static const double _topPadding = 8;

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;
    final highest = data.fold<int>(0, (max, row) => math.max(max, row.total));
    final scaleMax = niceCeiling(highest);
    final chartHeight = size.height - _labelHeight - _topPadding;
    final chartWidth = size.width - _axisWidth;

    final grid = Paint()
      ..color = AppColors.border
      ..strokeWidth = 1;
    for (var step = 0; step <= 2; step++) {
      final y = _topPadding + chartHeight * (1 - step / 2);
      canvas.drawLine(Offset(_axisWidth, y), Offset(size.width, y), grid);
      final label = formatCompactAmount((scaleMax * step / 2).round());
      _drawText(canvas, label, (text) => Offset(_axisWidth - text.width - 8, y - text.height / 2));
    }

    final slot = chartWidth / data.length;
    final barWidth = math.min(slot * 0.62, 40.0);
    for (var i = 0; i < data.length; i++) {
      final row = data[i];
      final center = _axisWidth + slot * (i + 0.5);
      final height = chartHeight * row.total / scaleMax;
      if (height > 0) {
        final rect = RRect.fromRectAndCorners(
          Rect.fromLTWH(center - barWidth / 2, _topPadding + chartHeight - height, barWidth, height),
          topLeft: const Radius.circular(4),
          topRight: const Radius.circular(4),
        );
        final paint = Paint()..color = row.month == selected ? AppColors.primary : AppColors.primaryMuted;
        canvas.drawRRect(rect, paint);
      }
      _drawText(
        canvas,
        shortMonthLabel(row.month),
        (text) => Offset(center - text.width / 2, size.height - _labelHeight + 6),
      );
    }
  }

  @override
  bool shouldRepaint(_BarPainter oldDelegate) => oldDelegate.data != data || oldDelegate.selected != selected;
}

class DonutSlice {
  const DonutSlice({required this.name, required this.color, required this.share});

  final String name;
  final Color color;
  final double share;
}

/// Regroupe les plus petites catégories au-delà de [limit] pour garder la légende lisible.
List<DonutSlice> buildSlices(List<CategoryTotal> rows, {int limit = 6}) {
  final slices = rows
      .take(limit)
      .map((row) => DonutSlice(name: row.category.name, color: colorFromHex(row.category.color), share: row.share))
      .toList();
  if (rows.length > limit) {
    final rest = rows.skip(limit);
    slices.add(DonutSlice(
      name: '${rest.length} autres',
      color: const Color(0xFFC5CBC8),
      share: rest.fold<double>(0, (sum, row) => sum + row.share),
    ));
  }
  return slices;
}

/// Répartition par catégorie : anneau et légende.
class CategoryDonut extends StatelessWidget {
  const CategoryDonut({super.key, required this.rows});

  final List<CategoryTotal> rows;

  @override
  Widget build(BuildContext context) {
    final slices = buildSlices(rows);
    return Row(
      children: [
        SizedBox(width: 120, height: 120, child: CustomPaint(painter: _DonutPainter(slices))),
        const SizedBox(width: 20),
        Expanded(
          child: Column(
            children: [
              for (final slice in slices)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(color: slice.color, borderRadius: BorderRadius.circular(2)),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          slice.name,
                          style: const TextStyle(fontSize: 12),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Text(formatPercent(slice.share), style: AppText.small),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DonutPainter extends CustomPainter {
  _DonutPainter(this.slices);

  final List<DonutSlice> slices;

  static const double _thickness = 22;
  static const double _gap = 0.03;

  @override
  void paint(Canvas canvas, Size size) {
    final total = slices.fold<double>(0, (sum, slice) => sum + slice.share);
    if (total <= 0) return;
    final rect = Rect.fromCircle(
      center: size.center(Offset.zero),
      radius: (math.min(size.width, size.height) - _thickness) / 2,
    );
    var start = -math.pi / 2;
    for (final slice in slices) {
      final sweep = 2 * math.pi * slice.share / total;
      final paint = Paint()
        ..color = slice.color
        ..style = PaintingStyle.stroke
        ..strokeWidth = _thickness;
      // Un léger espace sépare les parts, sauf quand il n'y en a qu'une.
      final gap = slices.length > 1 ? math.min(_gap, sweep / 2) : 0.0;
      canvas.drawArc(rect, start + gap / 2, sweep - gap, false, paint);
      start += sweep;
    }
  }

  @override
  bool shouldRepaint(_DonutPainter oldDelegate) => oldDelegate.slices != slices;
}
