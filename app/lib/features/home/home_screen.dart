import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/theme.dart';
import '../../core/version.dart';
import '../../data/models.dart';
import '../../domain/providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final latest = ref.watch(latestProvider);
    final status = ref.watch(statusProvider).asData?.value;

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
        data: (data) => _body(context, ref, data, settings.mode, status),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _error(context, ref),
      ),
    );
  }

  Widget _body(BuildContext context, WidgetRef ref, LatestData data, String mode,
      Status? status) {
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
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 2, 16, 6),
            child: Text(scoreHint(mode), style: theme.textTheme.bodySmall),
          ),
          if (status != null && _isStale(status.lastRunAt))
            Container(
              margin: const EdgeInsets.fromLTRB(12, 4, 12, 4),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: Colors.orange),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Datos desactualizados al '
                      '${formatDate(status.lastRunAt!.substring(0, 10))}. '
                      'El pipeline no actualizó en los últimos 3 días.',
                      style: const TextStyle(fontSize: 15),
                    ),
                  ),
                ],
              ),
            ),
          _UpdateBanner(),
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

  bool _isStale(String? iso) {
    if (iso == null) return false;
    final d = DateTime.tryParse(iso);
    if (d == null) return false;
    return DateTime.now().difference(d).inDays > 3;
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
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
                          '${formatDate(product.priceDate ?? '')}'
                          '${product.quality == 'estimated' ? '  ·  estimado' : ''}',
                          style: theme.textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text('$score/100', style: theme.textTheme.titleLarge),
                      Text('puntaje', style: theme.textTheme.bodySmall),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          actionWord(signal, mode),
                          style: const TextStyle(
                              color: Colors.white, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                recommendation(signal, mode),
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: color, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: score / 100,
                  minHeight: 6,
                  color: color,
                  backgroundColor: color.withValues(alpha: 0.15),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _UpdateBanner extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final version = ref.watch(versionProvider).asData?.value;
    final info = ref.watch(packageInfoProvider).asData?.value;
    if (version == null || info == null) return const SizedBox.shrink();
    if (!isNewerVersion(version.latest, info.version)) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: const EdgeInsets.fromLTRB(12, 4, 12, 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          const Icon(Icons.system_update, color: Colors.blue),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Nueva versión ${version.latest} disponible.',
              style: const TextStyle(fontSize: 15),
            ),
          ),
          TextButton(
            onPressed: () async {
              final url = version.url;
              if (url == null) return;
              final uri = Uri.tryParse(url);
              if (uri != null) {
                await launchUrl(uri, mode: LaunchMode.externalApplication);
              }
            },
            child: const Text('Actualizar'),
          ),
        ],
      ),
    );
  }
}
