/// Modelos de datos que reflejan el contrato `data/*.json` (plan §6).
library;

class FxRate {
  final double? usdArs;
  final String? date;
  final String? source;
  FxRate({this.usdArs, this.date, this.source});

  factory FxRate.fromJson(Map<String, dynamic> j) => FxRate(
        usdArs: (j['usd_ars'] as num?)?.toDouble(),
        date: j['date'] as String?,
        source: j['source'] as String?,
      );
}

class Product {
  final String id;
  final String name;
  final String? market;
  final String mode;
  final double? priceArs;
  final double? priceUsd;
  final String? priceDate;
  final String? quality;
  final double? change1d;
  final double? change30d;
  final double? low2yUsd;
  final String? low2yDate;
  final double? high2yUsd;
  final String? high2yDate;
  final double? avg2yUsd;
  final double? percentile;
  final double? distanceFromLow;
  final double? distanceFromHigh;
  final double? zscore;
  final double? rsi14;
  final double? ma50Usd;
  final double? ma200Usd;
  final int scoreBuy;
  final int scoreSell;
  final String signalBuy;
  final String signalSell;
  final String? explanation;
  final String? source;
  final String? sourceUrl;
  final String? updatedAt;

  Product({
    required this.id,
    required this.name,
    this.market,
    required this.mode,
    this.priceArs,
    this.priceUsd,
    this.priceDate,
    this.quality,
    this.change1d,
    this.change30d,
    this.low2yUsd,
    this.low2yDate,
    this.high2yUsd,
    this.high2yDate,
    this.avg2yUsd,
    this.percentile,
    this.distanceFromLow,
    this.distanceFromHigh,
    this.zscore,
    this.rsi14,
    this.ma50Usd,
    this.ma200Usd,
    required this.scoreBuy,
    required this.scoreSell,
    required this.signalBuy,
    required this.signalSell,
    this.explanation,
    this.source,
    this.sourceUrl,
    this.updatedAt,
  });

  factory Product.fromJson(Map<String, dynamic> j) => Product(
        id: j['id'] as String,
        name: j['name'] as String? ?? '',
        market: j['market'] as String?,
        mode: j['mode'] as String? ?? 'buy',
        priceArs: (j['price_ars'] as num?)?.toDouble(),
        priceUsd: (j['price_usd'] as num?)?.toDouble(),
        priceDate: j['price_date'] as String?,
        quality: j['quality'] as String?,
        change1d: (j['change_1d_pct'] as num?)?.toDouble(),
        change30d: (j['change_30d_pct'] as num?)?.toDouble(),
        low2yUsd: (j['low_2y_usd'] as num?)?.toDouble(),
        low2yDate: j['low_2y_date'] as String?,
        high2yUsd: (j['high_2y_usd'] as num?)?.toDouble(),
        high2yDate: j['high_2y_date'] as String?,
        avg2yUsd: (j['avg_2y_usd'] as num?)?.toDouble(),
        percentile: (j['percentile'] as num?)?.toDouble(),
        distanceFromLow: (j['distance_from_low_pct'] as num?)?.toDouble(),
        distanceFromHigh: (j['distance_from_high_pct'] as num?)?.toDouble(),
        zscore: (j['zscore'] as num?)?.toDouble(),
        rsi14: (j['rsi_14'] as num?)?.toDouble(),
        ma50Usd: (j['ma_50_usd'] as num?)?.toDouble(),
        ma200Usd: (j['ma_200_usd'] as num?)?.toDouble(),
        scoreBuy: (j['score_buy'] as num?)?.round() ?? 0,
        scoreSell: (j['score_sell'] as num?)?.round() ?? 0,
        signalBuy: j['signal_buy'] as String? ?? 'none',
        signalSell: j['signal_sell'] as String? ?? 'none',
        explanation: j['explanation'] as String?,
        source: j['source'] as String?,
        sourceUrl: j['source_url'] as String?,
        updatedAt: j['updated_at'] as String?,
      );
}

class LatestData {
  final int schemaVersion;
  final String? generatedAt;
  final FxRate fx;
  final List<Product> products;
  LatestData({required this.schemaVersion, this.generatedAt, required this.fx, required this.products});

  factory LatestData.fromJson(Map<String, dynamic> j) => LatestData(
        schemaVersion: (j['schema_version'] as num?)?.toInt() ?? 1,
        generatedAt: j['generated_at'] as String?,
        fx: FxRate.fromJson((j['fx'] as Map<String, dynamic>?) ?? {}),
        products: ((j['products'] as List?) ?? [])
            .map((e) => Product.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class HistoryPoint {
  final DateTime date;
  final double? priceArs;
  final double? priceUsd;
  final double? fxUsdArs;
  final String? quality;
  final String? source;
  HistoryPoint({required this.date, this.priceArs, this.priceUsd, this.fxUsdArs, this.quality, this.source});

  factory HistoryPoint.fromJson(Map<String, dynamic> j) => HistoryPoint(
        date: DateTime.parse(j['date'] as String),
        priceArs: (j['price_ars'] as num?)?.toDouble(),
        priceUsd: (j['price_usd'] as num?)?.toDouble(),
        fxUsdArs: (j['fx_usd_ars'] as num?)?.toDouble(),
        quality: j['quality'] as String?,
        source: j['source'] as String?,
      );
}

class History {
  final String product;
  final String unit;
  final List<HistoryPoint> points;
  History({required this.product, required this.unit, required this.points});

  factory History.fromJson(Map<String, dynamic> j) => History(
        product: j['product'] as String? ?? '',
        unit: j['unit'] as String? ?? 'USD/t',
        points: ((j['points'] as List?) ?? [])
            .map((e) => HistoryPoint.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class Alert {
  final String id;
  final String product;
  final String direction;
  final String tier;
  final double? priceUsd;
  final double? priceArs;
  final int? score;
  final String? message;
  final String? createdAt;
  Alert({required this.id, required this.product, required this.direction, required this.tier, this.priceUsd, this.priceArs, this.score, this.message, this.createdAt});

  factory Alert.fromJson(Map<String, dynamic> j) => Alert(
        id: j['id'] as String? ?? '',
        product: j['product'] as String? ?? '',
        direction: j['direction'] as String? ?? '',
        tier: j['tier'] as String? ?? '',
        priceUsd: (j['price_usd'] as num?)?.toDouble(),
        priceArs: (j['price_ars'] as num?)?.toDouble(),
        score: (j['score'] as num?)?.toInt(),
        message: j['message'] as String?,
        createdAt: j['created_at'] as String?,
      );
}

class SourceStatus {
  final String name;
  final bool ok;
  final int? rows;
  final String? error;
  SourceStatus({required this.name, required this.ok, this.rows, this.error});

  factory SourceStatus.fromJson(Map<String, dynamic> j) => SourceStatus(
        name: j['name'] as String? ?? '',
        ok: j['ok'] as bool? ?? false,
        rows: (j['rows'] as num?)?.toInt(),
        error: j['error'] as String?,
      );
}

class Status {
  final String? lastRunAt;
  final String? status;
  final List<SourceStatus> sources;
  final int productsUpdated;
  final List<String> staleProducts;
  Status({this.lastRunAt, this.status, required this.sources, required this.productsUpdated, required this.staleProducts});

  factory Status.fromJson(Map<String, dynamic> j) => Status(
        lastRunAt: j['last_run_at'] as String?,
        status: j['status'] as String?,
        sources: ((j['sources'] as List?) ?? [])
            .map((e) => SourceStatus.fromJson(e as Map<String, dynamic>))
            .toList(),
        productsUpdated: (j['products_updated'] as num?)?.toInt() ?? 0,
        staleProducts: ((j['stale_products'] as List?) ?? []).map((e) => e.toString()).toList(),
      );
}

class VersionInfo {
  final String latest;
  final int build;
  final String? url;
  final String? notes;
  VersionInfo({required this.latest, this.build = 0, this.url, this.notes});

  factory VersionInfo.fromJson(Map<String, dynamic> j) => VersionInfo(
        latest: j['latest'] as String? ?? '0.0.0',
        build: (j['build'] as num?)?.toInt() ?? 0,
        url: j['url'] as String?,
        notes: j['notes'] as String?,
      );
}
