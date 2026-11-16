import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/theme.dart';
import '../../data/models.dart';
import '../../domain/providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final latest = ref.watch(latestProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Oportunidades'),
        actions: [
          IconButton(
            tooltip: 'Alertas',
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => context.go('/alerts'),
          ),
          IconButton(
            tooltip: 'Ajustes',
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => context.go('/settings'),
          ),
        ],
      ),
      body: latest.when(
        data: (data) => _body(context, ref, data, settings.mode),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _error(context, ref),
      ),
    );
  }

  Widget _body(BuildContext context, WidgetRef ref, LatestData data, String mode) {
    final products = selectedProducts(ref, data);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(latestProvider);
        await ref.read(latestProvider.future);
      },
      child: ListView(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (data.generatedAt != null)
                  Text('Actualizado: ${formatDate(data.generatedAt!.substring(0, 10))}',
                      style: theme.textTheme.bodySmall),
                const SizedBox(height: 10),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'buy', label: Text('Comprar')),
                    ButtonSegment(value: 'sell', label: Text('Vender')),
                  ],
                  selected: {mode},
                  onSelectionChanged: (s) =>
                      ref.read(settingsProvider.notifier).setMode(s.first),
                  style: SegmentedButton.styleFrom(
                      textStyle: const TextStyle(fontSize: 18)),
                ),
              ],
            ),
          ),
          if (products.isEmpty)
            Padding(
              padding: const EdgeInsets.all(32),
              child: Text(
                'No hay oportunidades claras hoy.',
                style: theme.textTheme.titleMedium,
                textAlign: TextAlign.center,
              ),
            ),
          for (final p in products) _ProductCard(product: p, mode: mode),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _error(BuildContext context, WidgetRef ref) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('No se pudo cargar los datos.',
                textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () => ref.invalidate(latestProvider),
              child: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  final Product product;
  final String mode;

  const _ProductCard({required this.product, required this.mode});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isBuy = mode == 'buy';
    final signal = isBuy ? product.signalBuy : product.signalSell;
    final score = isBuy ? product.scoreBuy : product.scoreSell;
    final color = signalColor(signal);

    return Card(
      child: InkWell(
        onTap: () => context.go('/product/${product.id}'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(product.name, style: theme.textTheme.titleLarge),
                    const SizedBox(height: 4),
                    Text(formatArs(product.priceArs),
                        style: theme.textTheme.headlineMedium),
                    Text(
                      '${formatUsd(product.priceUsd)}  ·  '
                      '${formatDate(product.priceDate ?? '')}',
                      style: theme.textTheme.bodySmall,
                    ),
                    if (product.quality == 'estimated')
                      const Text('(estimado)', style: TextStyle(fontSize: 13)),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('$score', style: theme.textTheme.headlineMedium),
                  Text('score', style: theme.textTheme.bodySmall),
                  const SizedBox(height: 6),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _signalLabel(signal),
                      style: const TextStyle(
                          color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _signalLabel(String signal) {
    switch (signal) {
      case 'strong':
        return 'Fuerte';
      case 'buy':
        return 'Comprar';
      case 'sell':
        return 'Vender';
      case 'watch':
        return 'Mirar';
      default:
        return 'Sin señal';
    }
  }
}
