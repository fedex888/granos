import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const List<String> kDefaultProducts = ['maiz', 'soja', 'trigo', 'girasol'];

class SettingsState {
  final bool onboarded;
  final String mode; // 'buy' | 'sell'
  final double fleteCompra; // USD/t
  final double fleteVenta; // USD/t
  final Set<String> products;
  final Map<String, double> overrides; // productId -> ARS/t manual

  const SettingsState({
    required this.onboarded,
    required this.mode,
    required this.fleteCompra,
    required this.fleteVenta,
    required this.products,
    required this.overrides,
  });

  SettingsState copyWith({
    bool? onboarded,
    String? mode,
    double? fleteCompra,
    double? fleteVenta,
    Set<String>? products,
    Map<String, double>? overrides,
  }) {
    return SettingsState(
      onboarded: onboarded ?? this.onboarded,
      mode: mode ?? this.mode,
      fleteCompra: fleteCompra ?? this.fleteCompra,
      fleteVenta: fleteVenta ?? this.fleteVenta,
      products: products ?? this.products,
      overrides: overrides ?? this.overrides,
    );
  }
}

class SettingsController extends StateNotifier<SettingsState> {
  final SharedPreferences _prefs;

  SettingsController(this._prefs)
      : super(SettingsState(
          onboarded: _prefs.getBool('onboarded') ?? false,
          mode: _prefs.getString('mode') ?? 'buy',
          fleteCompra: _prefs.getDouble('flete_compra') ?? 0,
          fleteVenta: _prefs.getDouble('flete_venta') ?? 0,
          products:
              (_prefs.getStringList('products') ?? kDefaultProducts).toSet(),
          overrides: _decodeOverrides(_prefs.getString('overrides')),
        ));

  static Map<String, double> _decodeOverrides(String? raw) {
    if (raw == null) return {};
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      return map.map((k, v) => MapEntry(k, (v as num).toDouble()));
    } catch (_) {
      return {};
    }
  }

  void _saveOverrides() {
    _prefs.setString('overrides', jsonEncode(state.overrides));
  }

  void setOnboarded() {
    _prefs.setBool('onboarded', true);
    state = state.copyWith(onboarded: true);
  }

  void setMode(String mode) {
    _prefs.setString('mode', mode);
    state = state.copyWith(mode: mode);
  }

  void setFlete({double? compra, double? venta}) {
    if (compra != null) _prefs.setDouble('flete_compra', compra);
    if (venta != null) _prefs.setDouble('flete_venta', venta);
    state = state.copyWith(fleteCompra: compra, fleteVenta: venta);
  }

  void toggleProduct(String id) {
    final set = Set<String>.from(state.products);
    if (!set.remove(id)) set.add(id);
    _prefs.setStringList('products', set.toList());
    state = state.copyWith(products: set);
  }

  void setOverride(String id, double? value) {
    final map = Map<String, double>.from(state.overrides);
    if (value == null) {
      map.remove(id);
    } else {
      map[id] = value;
    }
    _saveOverrides();
    state = state.copyWith(overrides: map);
  }
}
