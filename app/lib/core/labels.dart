/// Textos en castellano claro para las señales (usuario final no técnico).
library;

/// Palabra corta para el badge de acción.
String actionWord(String signal, String mode) {
  final buy = mode == 'buy';
  switch (signal) {
    case 'strong':
    case 'buy':
    case 'sell':
      return buy ? 'Comprar' : 'Vender';
    case 'watch':
      return 'Atento';
    case 'insufficient_data':
      return 'Sin datos';
    default:
      return 'Esperar';
  }
}

/// Frase que explica qué hacer, sin jerga.
String recommendation(String signal, String mode) {
  final action = mode == 'buy' ? 'comprar' : 'vender';
  switch (signal) {
    case 'strong':
      return 'Muy buen momento para $action';
    case 'buy':
    case 'sell':
      return 'Buen momento para $action';
    case 'watch':
      return 'Puede convenir $action: estate atento';
    case 'insufficient_data':
      return 'Todavía no hay datos suficientes';
    default:
      return 'Todavía no es el mejor momento para $action';
  }
}

/// Explicación corta del puntaje (0-100).
String scoreHint(String mode) {
  final action = mode == 'buy' ? 'comprar' : 'vender';
  return 'El puntaje va de 0 a 100: cuanto más alto, mejor es el momento para $action.';
}
