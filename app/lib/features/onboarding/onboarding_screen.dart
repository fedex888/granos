import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../domain/providers.dart';

const String _disclaimer =
    'Esta aplicación es una herramienta de referencia. Los precios pueden estar '
    'desactualizados o contener errores. No constituye asesoramiento financiero, '
    'comercial ni de inversión. Verificá siempre con tu corredor, acopio o '
    'cooperativa antes de operar.';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _compraCtrl = TextEditingController();
  final _ventaCtrl = TextEditingController();

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
  }

  @override
  void dispose() {
    _compraCtrl.dispose();
    _ventaCtrl.dispose();
    super.dispose();
  }

  void _finish() {
    final controller = ref.read(settingsProvider.notifier);
    controller.setFlete(
      compra: double.tryParse(_compraCtrl.text.replaceAll(',', '.')) ?? 0,
      venta: double.tryParse(_ventaCtrl.text.replaceAll(',', '.')) ?? 0,
    );
    controller.setOnboarded();
    context.go('/');
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const SizedBox(height: 8),
            Text('Oportunidades de Granos',
                style: theme.textTheme.headlineMedium),
            const SizedBox(height: 8),
            Text(
              'Precios de referencia (Rosario) en pesos y dólares, comparados '
              'con los últimos 2 años.',
              style: theme.textTheme.bodyLarge,
            ),
            const SizedBox(height: 20),
            Text('¿Querés comprar o vender?', style: theme.textTheme.titleMedium),
            const SizedBox(height: 10),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'buy', label: Text('Comprar')),
                ButtonSegment(value: 'sell', label: Text('Vender')),
              ],
              selected: {settings.mode},
              onSelectionChanged: (s) =>
                  ref.read(settingsProvider.notifier).setMode(s.first),
              style: SegmentedButton.styleFrom(
                textStyle: const TextStyle(fontSize: 18),
              ),
            ),
            const SizedBox(height: 20),
            Text('¿Qué productos te interesan?',
                style: theme.textTheme.titleMedium),
            const SizedBox(height: 6),
            for (final (id, name) in _products)
              CheckboxListTile(
                value: settings.products.contains(id),
                onChanged: (_) =>
                    ref.read(settingsProvider.notifier).toggleProduct(id),
                title: Text(name, style: const TextStyle(fontSize: 18)),
                controlAffinity: ListTileControlAffinity.leading,
                contentPadding: EdgeInsets.zero,
              ),
            const SizedBox(height: 12),
            Text('Flete (opcional, USD/t)', style: theme.textTheme.titleMedium),
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _compraCtrl,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: [
                      FilteringTextInputFormatter.allow(RegExp(r'[\d.,]')),
                    ],
                    decoration: const InputDecoration(
                      labelText: 'Compra',
                      border: OutlineInputBorder(),
                    ),
                    style: const TextStyle(fontSize: 18),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _ventaCtrl,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: [
                      FilteringTextInputFormatter.allow(RegExp(r'[\d.,]')),
                    ],
                    decoration: const InputDecoration(
                      labelText: 'Venta',
                      border: OutlineInputBorder(),
                    ),
                    style: const TextStyle(fontSize: 18),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(_disclaimer, style: theme.textTheme.bodySmall),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _finish,
              child: const Text('Comenzar'),
            ),
          ],
        ),
      ),
    );
  }
}
