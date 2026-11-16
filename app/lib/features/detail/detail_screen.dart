import 'package:fl_chart/fl_chart.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/theme.dart';
import '../../data/models.dart';
import '../../data/settings.dart';
import '../../domain/providers.dart';

class DetailScreen extends ConsumerStatefulWidget {
  final String productId;
  const DetailScreen({super.key, required this.productId});

  @override
  ConsumerState<DetailScreen> createState() => _DetailScreenState();
}

class _DetailScreenState extends ConsumerState<DetailScreen> {
  int _rangeDays = 730; // 2 años por defecto

  @override
  Widget build(BuildContext context) {
    final latestAsync = ref.watch(latestProvider);
    final historyAsync = ref.watch(historyProvider(widget.productId));
    final settings = ref.watch(settingsProvider);

    return latestAsync.when(
      loading: () => _scaffold(context, const Center(child: CircularProgressIndicator())),
      error: (e, _) => _scaffold(context, Center(child: Text('Error: $e'))),
      data: (latest) {
        Product? product;
        for (final p in latest.products) {
          if (p.id == widget.productId) {
            product = p;
            break;
          }
        }
        if (product == null) {
          return _scaffold(context, const Center(child: Text('Producto no encontrado')));
        }
        return _scaffold(
          context,
          _buildBody(context, ref, product, latest, settings, historyAsync),
          title: product.name,
        );
      },
    );
  }

  Scaffold _scaffold(BuildContext context, Widget body, {String? title}) {
    return Scaffold(
      appBar: AppBar(title: Text(title ?? 'Detalle')),
      body: body,
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, Product product,
      LatestData latest, SettingsState settings, AsyncValue<History> historyAsync) {
    final theme = Theme.of(context);
    final fx = latest.fx.usdArs ?? 0;

    return ListView(
      padding: const EdgeInsets.only(bottom: 32),
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(formatArs(product.priceArs), style: theme.textTheme.headlineMedium),
              Text(
                '${formatUsd(product.priceUsd)}  ·  ${formatDate(product.priceDate ?? '')}'
                '${product.quality == 'estimated' ? '  ·  estimado' : ''}',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 6),
              Text(
                recommendation(
                  settings.mode == 'buy' ? product.signalBuy : product.signalSell,
                  settings.mode,
                ),
                style: theme.textTheme.titleMedium?.copyWith(
                  color: signalColor(
                    settings.mode == 'buy' ? product.signalBuy : product.signalSell,
                  ),
                ),
              ),
            ],
          ),
        ),
        // Gráfico
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 30, label: Text('1M')),
              ButtonSegment(value: 180, label: Text('6M')),
              ButtonSegment(value: 730, label: Text('2A')),
            ],
            selected: {_rangeDays},
            onSelectionChanged: (s) => setState(() => _rangeDays = s.first),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 220,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: historyAsync.when(
              data: (h) => _PriceChart(
                points: h.points,
                rangeDays: _rangeDays,
                low: product.low2yUsd,
                avg: product.avg2yUsd,
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => const Center(child: Text('Sin historial')),
            ),
          ),
        ),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Wrap(
            spacing: 16,
            children: [
              _Legend(color: Colors.green, label: 'Mín 2 años'),
              _Legend(color: Colors.orange, label: 'Prom 2 años'),
            ],
          ),
        ),
        const SizedBox(height: 8),
        // ¿Por qué?
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('¿Por qué?', style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                Text(product.explanation ?? '', style: theme.textTheme.bodyLarge),
                const SizedBox(height: 8),
                ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: EdgeInsets.zero,
                  title: const Text('Ver detalles técnicos'),
                  children: [
                    _MetricRow(label: 'Percentil', value: product.percentile?.toStringAsFixed(0) ?? '—'),
                    _MetricRow(label: 'Arriba del mínimo', value: formatPercent(product.distanceFromLow)),
                    _MetricRow(label: 'Debajo del máximo', value: formatPercent(product.distanceFromHigh)),
                    _MetricRow(label: 'Z-score', value: product.zscore?.toStringAsFixed(2) ?? '—'),
                    _MetricRow(label: 'RSI (14)', value: product.rsi14?.toStringAsFixed(0) ?? '—'),
                    _MetricRow(label: 'Media 50d', value: formatUsd(product.ma50Usd)),
                    _MetricRow(label: 'Media 200d', value: formatUsd(product.ma200Usd)),
                  ],
                ),
              ],
            ),
          ),
        ),
        // Mínimo y máximo de 2 años
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Últimos 2 años', style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                _MetricRow(
                  label: 'Mínimo',
                  value:
                      '${formatUsd(product.low2yUsd)}  (${formatDate(product.low2yDate ?? '')})',
                ),
                _MetricRow(
                  label: 'Máximo',
                  value:
                      '${formatUsd(product.high2yUsd)}  (${formatDate(product.high2yDate ?? '')})',
                ),
                _MetricRow(label: 'Promedio', value: formatUsd(product.avg2yUsd)),
              ],
            ),
          ),
        ),
        // Precio local
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Precio local (Chaco)', style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                _MetricRow(label: 'Rosario', value: formatUsd(product.priceUsd)),
                _MetricRow(label: 'Flete compra', value: formatUsd(settings.fleteCompra)),
                _MetricRow(label: 'Flete venta', value: formatUsd(settings.fleteVenta)),
                const Divider(height: 20),
                if (settings.overrides[product.id] != null)
                  _MetricRow(
                    label: 'Precio informado (manual)',
                    value: formatArs(settings.overrides[product.id]),
                  ),
                _MetricRow(
                  label: 'Local compra (est.)',
                  value: _local(fx, product.priceUsd, settings.fleteCompra, 1),
                ),
                _MetricRow(
                  label: 'Local venta (est.)',
                  value: _local(fx, product.priceUsd, settings.fleteVenta, -1),
                ),
                const SizedBox(height: 8),
                Text(
                  'Estimación sobre Rosario ± flete. No hay pizarra oficial local.',
                  style: theme.textTheme.bodySmall,
                ),
                TextButton(
                  onPressed: () => _editOverride(context, ref, product),
                  child: const Text('Cargar precio manual'),
                ),
              ],
            ),
          ),
        ),
        // Fuente y disclaimer
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Fuente: ${product.source ?? 'BCR'}',
                  style: theme.textTheme.bodySmall),
              const SizedBox(height: 4),
              Text(
                'Referencia, no es asesoramiento financiero. Verificá con tu '
                'corredor o cooperativa antes de operar.',
                style: theme.textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ],
    );
  }

  String _local(double fx, double? rosarioUsd, double flete, int sign) {
    if (rosarioUsd == null) return '—';
    final usd = rosarioUsd + sign * flete;
    final ars = usd * fx;
    return '${formatUsd(usd)}  ·  ${formatArs(ars)}';
  }

  Future<void> _editOverride(BuildContext context, WidgetRef ref, Product product) async {
    final controller = TextEditingController(
      text: ref.read(settingsProvider).overrides[product.id]?.toStringAsFixed(0) ?? '',
    );
    final value = await showDialog<double>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Precio local manual'),
        content: TextField(
          controller: controller,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(
            labelText: 'ARS/t',
            hintText: 'Ej. 280000',
          ),
          style: const TextStyle(fontSize: 18),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              final v = double.tryParse(controller.text.replaceAll(',', '.'));
              Navigator.pop(ctx, v);
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
    if (value != null) {
      ref.read(settingsProvider.notifier).setOverride(product.id, value);
    }
  }
}

class _MetricRow extends StatelessWidget {
  final String label;
  final String value;
  const _MetricRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: theme.textTheme.bodyMedium),
          Text(value, style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  final Color color;
  final String label;
  const _Legend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 20, height: 3, color: color),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(fontSize: 13)),
      ],
    );
  }
}

class _PriceChart extends StatelessWidget {
  final List<HistoryPoint> points;
  final int rangeDays;
  final double? low;
  final double? avg;

  const _PriceChart({required this.points, required this.rangeDays, this.low, this.avg});

  @override
  Widget build(BuildContext context) {
    final cutoff = DateTime.now().subtract(Duration(days: rangeDays));
    final data = points.where((p) => p.date.isAfter(cutoff)).toList();
    if (data.length < 2) {
      return const Center(child: Text('Pocos datos para graficar'));
    }

    final spots = <FlSpot>[
      for (var i = 0; i < data.length; i++)
        FlSpot(i.toDouble(), data[i].priceUsd ?? 0),
    ];
    final values = data.map((p) => p.priceUsd ?? 0).toList();
    final minY = values.reduce((a, b) => a < b ? a : b);
    final maxY = values.reduce((a, b) => a > b ? a : b);
    final pad = (maxY - minY) * 0.1 + 0.001;

    final horizontalLines = <HorizontalLine>[
      if (low != null && low! >= minY - pad && low! <= maxY + pad)
        HorizontalLine(y: low!, color: Colors.green, strokeWidth: 1.5, dashArray: [6, 4]),
      if (avg != null && avg! >= minY - pad && avg! <= maxY + pad)
        HorizontalLine(y: avg!, color: Colors.orange, strokeWidth: 1.5, dashArray: [6, 4]),
    ];

    return LineChart(
      LineChartData(
        minY: minY - pad,
        maxY: maxY + pad,
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: false,
            color: Colors.blue.shade700,
            barWidth: 2,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: Colors.blue.withValues(alpha: 0.08),
            ),
          ),
        ],
        extraLinesData: ExtraLinesData(horizontalLines: horizontalLines),
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        borderData: FlBorderData(show: false),
        titlesData: FlTitlesData(
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 46,
              getTitlesWidget: (v, meta) =>
                  Text(v.toStringAsFixed(0), style: const TextStyle(fontSize: 12)),
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              interval: (data.length / 4).floorToDouble().clamp(1, double.infinity),
              getTitlesWidget: (v, meta) {
                final idx = v.round();
                if (idx < 0 || idx >= data.length) return const SizedBox.shrink();
                final d = data[idx].date;
                return Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    '${d.day}/${d.month}',
                    style: const TextStyle(fontSize: 11),
                  ),
                );
              },
            ),
          ),
        ),
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touched) => touched.map((t) {
              final idx = t.x.round();
              final p = data[idx];
              return LineTooltipItem(
                '${p.date.day}/${p.date.month}  USD ${(p.priceUsd ?? 0).toStringAsFixed(2)}',
                const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
              );
            }).toList(),
          ),
        ),
      ),
    );
  }
}
