import 'package:intl/intl.dart';

/// Formato numérico es_AR: separador de miles `.` y decimal `,`.
/// Se usa el locale `es` (los símbolos de `es_AR` no están incluidos por defecto
/// en `intl`, y `es` produce el mismo resultado para estos patrones).
final NumberFormat _int = NumberFormat('#,##0', 'es');
final NumberFormat _dec = NumberFormat('#,##0.00', 'es');
final DateFormat _date = DateFormat('dd/MM/yyyy');

String formatArs(double? v) {
  if (v == null) return '—';
  if (v == v.roundToDouble()) return '\$ ${_int.format(v)}';
  return '\$ ${_dec.format(v)}';
}

String formatUsd(double? v) {
  if (v == null) return '—';
  return 'USD ${_dec.format(v)}';
}

String formatDate(String iso) {
  final d = DateTime.tryParse(iso);
  return d == null ? iso : _date.format(d);
}

String formatPercent(double? v) {
  if (v == null) return '—';
  final sign = v > 0 ? '+' : '';
  return '$sign${v.toStringAsFixed(1).replaceAll('.', ',')}%';
}
