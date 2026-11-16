import 'dart:convert';

import 'package:dio/dio.dart';

import 'cache.dart';
import 'models.dart';

/// Datos públicos servidos por GitHub (repo `fedex888/granos`, rama `main`).
const String dataBaseUrl =
    'https://raw.githubusercontent.com/fedex888/granos/main/data/';

class Api {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: dataBaseUrl,
    connectTimeout: const Duration(seconds: 20),
    receiveTimeout: const Duration(seconds: 20),
  ));
  final FileCache cache = FileCache();

  Future<LatestData> fetchLatest() async {
    final data = await _getJson('latest.json', 'latest');
    return LatestData.fromJson(data);
  }

  Future<History> fetchHistory(String productId) async {
    final data = await _getJson('history/$productId.json', 'history_$productId');
    return History.fromJson(data);
  }

  Future<List<Alert>> fetchAlerts() async {
    final data = await _getJson('alerts/latest.json', 'alerts_latest');
    return ((data['alerts'] as List?) ?? [])
        .map((e) => Alert.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Status> fetchStatus() async {
    final data = await _getJson('status.json', 'status');
    return Status.fromJson(data);
  }

  Future<Map<String, dynamic>> _getJson(String path, String cacheKey) async {
    try {
      final resp = await _dio.get<String>(
        path,
        options: Options(responseType: ResponseType.plain),
      );
      final data = jsonDecode(resp.data!) as Map<String, dynamic>;
      await cache.write(cacheKey, jsonEncode(data));
      return data;
    } on Exception {
      // Fallback offline: usar la última respuesta cacheada.
      final cached = await cache.read(cacheKey);
      if (cached != null) {
        return jsonDecode(cached) as Map<String, dynamic>;
      }
      rethrow;
    }
  }
}
