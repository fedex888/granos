import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../domain/providers.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _compraCtrl = TextEditingController();
  final _ventaCtrl = TextEditingController();
  String _version = '';

  static const _products = [
    ('maiz', 'Maíz'),
    ('soja', 'Soja'),
    ('trigo', 'Trigo pan'),
    ('girasol', 'Girasol'),
  ];

  @override
  void initState() {
    super.initState();
    final s = ref.read(settingsProvider);
    _compraCtrl.text = s.fleteCompra == 0 ? '' : s.fleteCompra.toStringAsFixed(0);
    _ventaCtrl.text = s.fleteVenta == 0 ? '' : s.fleteVenta.toStringAsFixed(0);
    PackageInfo.fromPlatform().then((info) {
      if (mounted) setState(() => _version = '${info.version}+${info.buildNumber}');
    });
  }

  @override
  void dispose() {
    _compraCtrl.dispose();
    _ventaCtrl.dispose();
    super.dispose();
  }

  void _saveFlete() {
    ref.read(settingsProvider.notifier).setFlete(
          compra: double.tryParse(_compraCtrl.text.replaceAll(',', '.')) ?? 0,
          venta: double.tryParse(_ventaCtrl.text.replaceAll(',', '.')) ?? 0,
        );
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Flete guardado')));
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Ajustes')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Modo', style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'buy', label: Text('Comprar')),
              ButtonSegment(value: 'sell', label: Text('Vender')),
            ],
            selected: {settings.mode},
            onSelectionChanged: (s) =>
                ref.read(settingsProvider.notifier).setMode(s.first),
            style: SegmentedButton.styleFrom(textStyle: const TextStyle(fontSize: 18)),
          ),
          const SizedBox(height: 6),
          Text('Elegí qué querés hacer para ver las oportunidades de ese lado.',
              style: theme.textTheme.bodySmall),
          const SizedBox(height: 24),
          Text('Flete (USD/t)', style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _compraCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[\d.,]')),
                  ],
                  decoration: const InputDecoration(
                      labelText: 'Compra', border: OutlineInputBorder()),
                  style: const TextStyle(fontSize: 18),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _ventaCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[\d.,]')),
                  ],
                  decoration: const InputDecoration(
                      labelText: 'Venta', border: OutlineInputBorder()),
                  style: const TextStyle(fontSize: 18),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          OutlinedButton(onPressed: _saveFlete, child: const Text('Guardar flete')),
          const SizedBox(height: 24),
          Text('Productos', style: theme.textTheme.titleMedium),
          for (final (id, name) in _products)
            CheckboxListTile(
              value: settings.products.contains(id),
              onChanged: (_) => ref.read(settingsProvider.notifier).toggleProduct(id),
              title: Text(name, style: const TextStyle(fontSize: 18)),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
            ),
          const Divider(height: 32),
          OutlinedButton(
            onPressed: () async {
              ref.invalidate(latestProvider);
              ref.invalidate(alertsProvider);
              ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Datos refrescados')));
            },
            child: const Text('Refrescar datos'),
          ),
          const SizedBox(height: 24),
          Text('Acerca de', style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            'Precios de referencia de la Cámara Arbitral de Cereales de Rosario '
            '(BCR), control cruzado con MAGyP. Cotización BNA vía ArgentinaDatos.',
            style: theme.textTheme.bodySmall,
          ),
          const SizedBox(height: 8),
          Text(
            'Esta app es una herramienta de referencia y no constituye '
            'asesoramiento financiero, comercial ni de inversión.',
            style: theme.textTheme.bodySmall,
          ),
          if (_version.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text('Versión $_version', style: theme.textTheme.bodySmall),
            ),
        ],
      ),
    );
  }
}
