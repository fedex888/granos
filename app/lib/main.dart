import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
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
}
