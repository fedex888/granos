import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'data/push.dart';
import 'data/settings.dart';
import 'domain/providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final controller = SettingsController(prefs);
  final router = buildRouter((prefs.getBool('onboarded') ?? false) ? '/' : '/onboarding');

  runApp(
    ProviderScope(
      overrides: [settingsProvider.overrideWith((ref) => controller)],
      child: App(router: router),
    ),
  );

  // FCM después del primer frame: no bloquea el arranque de la UI.
  WidgetsBinding.instance.addPostFrameCallback((_) async {
    try {
      await PushService(router).init();
    } catch (e) {
      debugPrint('Push init failed: $e');
    }
  });
}
