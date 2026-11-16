import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/theme.dart';
import '../../domain/providers.dart';

class AlertsScreen extends ConsumerWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alerts = ref.watch(alertsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Alertas')),
      body: alerts.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => const Center(child: Text('No se pudieron cargar las alertas')),
        data: (list) {
          if (list.isEmpty) {
            return const Center(child: Text('No hay alertas recientes.'));
          }
          return ListView(
            padding: const EdgeInsets.all(12),
            children: [
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  'Las notificaciones push se habilitan en una etapa posterior. '
                  'Acá ves las señales recientes.',
                  style: theme.textTheme.bodySmall,
                ),
              ),
              for (final a in list) Card(child: _tile(context, a)),
            ],
          );
        },
      ),
    );
  }

  Widget _tile(BuildContext context, dynamic a) {
    final theme = Theme.of(context);
    final isBuy = a.direction == 'buy';
    final color = signalColor(a.tier);
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(12)),
                child: Text(
                  '${isBuy ? 'Compra' : 'Venta'} · ${_tier(a.tier)}',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              const Spacer(),
              Text(formatDate((a.createdAt ?? '').substring(0, 10)),
                  style: theme.textTheme.bodySmall),
            ],
          ),
          const SizedBox(height: 8),
          Text(a.message ?? '', style: theme.textTheme.bodyLarge),
          const SizedBox(height: 4),
          Text(formatUsd(a.priceUsd), style: theme.textTheme.bodySmall),
        ],
      ),
    );
  }

  String _tier(String tier) {
    switch (tier) {
      case 'strong':
        return 'Muy bueno';
      case 'buy':
        return 'Comprar';
      case 'sell':
        return 'Vender';
      case 'watch':
        return 'Atento';
      default:
        return tier;
    }
  }
}
