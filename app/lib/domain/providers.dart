import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/api.dart';
import '../data/models.dart';
import '../data/settings.dart';

/// Sobrescrito en `main()` con el controlador ya inicializado (SharedPreferences).
final settingsProvider =
    StateNotifierProvider<SettingsController, SettingsState>(
        (ref) => throw UnimplementedError('Se inyecta en main()'));

final apiProvider = Provider<Api>((ref) => Api());

final latestProvider = FutureProvider<LatestData>(
    (ref) => ref.watch(apiProvider).fetchLatest());

final statusProvider = FutureProvider<Status>(
    (ref) => ref.watch(apiProvider).fetchStatus());

final alertsProvider = FutureProvider<List<Alert>>(
    (ref) => ref.watch(apiProvider).fetchAlerts());

final historyProvider = FutureProvider.family<History, String>(
    (ref, productId) => ref.watch(apiProvider).fetchHistory(productId));

/// Producto activo según el toggle global comprar/vender y la selección.
List<Product> selectedProducts(WidgetRef ref, LatestData data) {
  final settings = ref.watch(settingsProvider);
  final active = data.products.where((p) => settings.products.contains(p.id));
  return active.toList()
    ..sort((a, b) {
      final sa = settings.mode == 'buy' ? a.scoreBuy : a.scoreSell;
      final sb = settings.mode == 'buy' ? b.scoreBuy : b.scoreSell;
      return sb.compareTo(sa);
    });
}
