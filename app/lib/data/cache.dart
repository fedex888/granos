import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

/// Cache simple por archivos en el directorio de documentos de la app.
/// Guarda la respuesta JSON cruda de cada endpoint para el modo offline.
class FileCache {
  Future<Directory> _dir() async {
    final base = await getApplicationDocumentsDirectory();
    final dir = Directory('${base.path}/granos_cache');
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    return dir;
  }

  Future<void> write(String key, String value) async {
    final f = File('${(await _dir()).path}/$key.json');
    await f.writeAsString(value, encoding: utf8, flush: true);
  }

  Future<String?> read(String key) async {
    final f = File('${(await _dir()).path}/$key.json');
    if (await f.exists()) {
      return f.readAsString(encoding: utf8);
    }
    return null;
  }

  Future<void> clear() async {
    final dir = await _dir();
    if (await dir.exists()) {
      await dir.delete(recursive: true);
    }
  }
}
