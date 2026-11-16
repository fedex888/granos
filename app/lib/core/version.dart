/// Comparación simple de versiones "x.y.z" (devuelve true si `latest` > `current`).
bool isNewerVersion(String latest, String current) {
  final a = _parts(latest);
  final b = _parts(current);
  for (var i = 0; i < 3; i++) {
    final x = i < a.length ? a[i] : 0;
    final y = i < b.length ? b[i] : 0;
    if (x != y) return x > y;
  }
  return false;
}

List<int> _parts(String v) {
  return v.split('.').map((s) {
    final digits = RegExp(r'^\d+').stringMatch(s.trim());
    return int.tryParse(digits ?? '') ?? 0;
  }).toList();
}
