import 'package:flutter_test/flutter_test.dart';
import 'package:mes_depenses/charts.dart';
import 'package:mes_depenses/format.dart';
import 'package:mes_depenses/models.dart';

void main() {
  group('formatAmount', () {
    test('sépare les milliers et ajoute la devise', () {
      expect(formatAmount(1250000), '1 250 000 FCFA');
      expect(formatAmount(500), '500 FCFA');
      expect(formatAmount(0), '0 FCFA');
      expect(formatAmount(-2000), '-2 000 FCFA');
    });
  });

  test('formatCompactAmount abrège les grands montants', () {
    expect(formatCompactAmount(950), '950');
    expect(formatCompactAmount(45000), '45 k');
    expect(formatCompactAmount(1300000), '1,3 M');
  });

  test('parseAmount ne garde que les chiffres', () {
    expect(parseAmount('12 500 FCFA'), 12500);
    expect(parseAmount(''), isNull);
    expect(parseAmount('abc'), isNull);
  });

  group('mois', () {
    test('shiftMonth passe les années', () {
      expect(shiftMonth('2026-01', -1), '2025-12');
      expect(shiftMonth('2026-12', 1), '2027-01');
      expect(shiftMonth('2026-11', -6), '2026-05');
    });

    test('premier et dernier jour', () {
      expect(firstDayOf('2026-11'), '2026-11-01');
      expect(lastDayOf('2026-11'), '2026-11-30');
      expect(lastDayOf('2026-12'), '2026-12-31');
      expect(lastDayOf('2028-02'), '2028-02-29');
    });

    test('libellés', () {
      expect(monthLabel('2026-11'), 'Novembre 2026');
      expect(shortMonthLabel('2026-02'), 'févr');
    });
  });

  test('formatDate et formatPercent', () {
    expect(formatDate(DateTime(2026, 11, 3)), '3 nov. 2026');
    expect(formatPercent(0.826), '83 %');
  });

  test('niceCeiling arrondit à une valeur ronde', () {
    expect(niceCeiling(0), 1);
    expect(niceCeiling(87000), 90000);
    expect(niceCeiling(326400), 400000);
    expect(niceCeiling(100000), 100000);
  });

  test('buildSlices regroupe les petites catégories', () {
    final rows = [
      for (var i = 0; i < 8; i++)
        CategoryTotal(
          category: ExpenseCategory(id: i, name: 'C$i', color: '#0F5D4A', icon: 'tag', isDefault: true),
          total: 100,
          share: 0.125,
        ),
    ];
    final slices = buildSlices(rows);
    expect(slices.length, 7);
    expect(slices.last.name, '2 autres');
    expect(slices.last.share, closeTo(0.25, 0.0001));
  });

  test('DashboardSummary lit la réponse de l’API', () {
    final summary = DashboardSummary.fromJson({
      'month': '2026-11',
      'total': 1500,
      'count': 1,
      'previous_total': 0,
      'variation': null,
      'by_category': [
        {
          'category': {'id': 1, 'name': 'Transport', 'color': '#2F6FB0', 'icon': 'bus', 'is_default': true},
          'total': 1500,
          'share': 1,
        },
      ],
      'monthly': [
        {'month': '2026-11', 'total': 1500},
      ],
      'daily': [],
      'alerts': [],
      'recent': [
        {
          'id': 7,
          'amount': 1500,
          'date': '2026-11-10',
          'note': 'Taxi',
          'source': 'manuel',
          'category': {'id': 1, 'name': 'Transport', 'color': '#2F6FB0', 'icon': 'bus', 'is_default': true},
          'created_at': '2026-11-10T09:00:00Z',
        },
      ],
    });
    expect(summary.variation, isNull);
    expect(summary.byCategory.single.share, 1.0);
    expect(summary.recent.single.date, DateTime(2026, 11, 10));
  });
}
