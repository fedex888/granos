import 'package:material_ui/material_ui.dart';

/// Tema con letras grandes y alto contraste (UX para el usuario final, plan §9.6).
ThemeData buildTheme() {
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF2E7D32), // verde campo
      brightness: Brightness.light,
    ),
  );

  return base.copyWith(
    textTheme: base.textTheme.copyWith(
      // Letras base 18sp, títulos 24sp.
      bodyLarge: base.textTheme.bodyLarge?.copyWith(fontSize: 18),
      bodyMedium: base.textTheme.bodyMedium?.copyWith(fontSize: 18),
      bodySmall: base.textTheme.bodySmall?.copyWith(fontSize: 15),
      titleLarge:
          base.textTheme.titleLarge?.copyWith(fontSize: 24, fontWeight: FontWeight.bold),
      titleMedium:
          base.textTheme.titleMedium?.copyWith(fontSize: 20, fontWeight: FontWeight.w600),
      headlineMedium:
          base.textTheme.headlineMedium?.copyWith(fontSize: 26, fontWeight: FontWeight.bold),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(0, 52), // botones >= 48dp
        textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(0, 52),
        textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      ),
    ),
    snackBarTheme: const SnackBarThemeData(
      contentTextStyle: TextStyle(fontSize: 16),
    ),
  );
}

/// Colores de señal (compra = verde, venta = rojo).
Color signalColor(String? signal) {
  switch (signal) {
    case 'strong':
    case 'buy':
    case 'sell':
      return const Color(0xFF2E7D32);
    case 'watch':
      return const Color(0xFFF9A825);
    default:
      return Colors.grey;
  }
}
