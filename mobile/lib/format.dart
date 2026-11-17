const _months = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
];

const _shortMonths = [
  'janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
  'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.',
];

const _nbsp = ' ';

String _pad(int value) => value.toString().padLeft(2, '0');

String _groupThousands(int value) {
  final digits = value.abs().toString();
  final buffer = StringBuffer();
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) buffer.write(_nbsp);
    buffer.write(digits[i]);
  }
  return buffer.toString();
}

/// 1250000 devient "1 250 000 FCFA", avec des espaces insécables.
String formatAmount(int amount) {
  final sign = amount < 0 ? '-' : '';
  return '$sign${_groupThousands(amount)}${_nbsp}FCFA';
}

/// Forme abrégée pour les axes des graphiques : 45000 devient "45 k".
String formatCompactAmount(int amount) {
  if (amount >= 1000000) {
    return '${(amount / 1000000).toStringAsFixed(1).replaceAll('.', ',')} M';
  }
  if (amount >= 1000) return '${(amount / 1000).round()} k';
  return amount.toString();
}

String formatPercent(double ratio) => '${(ratio * 100).round()}$_nbsp%';

String formatDate(DateTime date) => '${date.day} ${_shortMonths[date.month - 1]} ${date.year}';

/// Ne garde que les chiffres d'une saisie. Renvoie null si elle n'en contient aucun.
int? parseAmount(String text) {
  final digits = text.replaceAll(RegExp(r'[^0-9]'), '');
  if (digits.isEmpty) return null;
  return int.tryParse(digits);
}

String toIsoDay(DateTime date) => '${date.year}-${_pad(date.month)}-${_pad(date.day)}';

String monthOf(DateTime date) => '${date.year}-${_pad(date.month)}';

String currentMonth() => monthOf(DateTime.now());

/// Décale un mois "AAAA-MM" de [offset] mois, en passant les années.
String shiftMonth(String month, int offset) {
  final year = int.parse(month.substring(0, 4));
  final number = int.parse(month.substring(5, 7));
  final index = year * 12 + (number - 1) + offset;
  return '${index ~/ 12}-${_pad(index % 12 + 1)}';
}

String firstDayOf(String month) => '$month-01';

String lastDayOf(String month) {
  final year = int.parse(month.substring(0, 4));
  final number = int.parse(month.substring(5, 7));
  // Le jour 0 du mois suivant est le dernier jour du mois demandé.
  return toIsoDay(DateTime(year, number + 1, 0));
}

String monthLabel(String month) {
  final name = _months[int.parse(month.substring(5, 7)) - 1];
  return '${name[0].toUpperCase()}${name.substring(1)} ${month.substring(0, 4)}';
}

String shortMonthLabel(String month) {
  return _shortMonths[int.parse(month.substring(5, 7)) - 1].replaceAll('.', '');
}
