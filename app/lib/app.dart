import 'package:material_ui/material_ui.dart';
import 'package:go_router/go_router.dart';

import 'core/theme.dart';
import 'features/alerts/alerts_screen.dart';
import 'features/detail/detail_screen.dart';
import 'features/home/home_screen.dart';
import 'features/onboarding/onboarding_screen.dart';
import 'features/settings/settings_screen.dart';

GoRouter buildRouter(String initialLocation) {
  return GoRouter(
    initialLocation: initialLocation,
    routes: [
      GoRoute(path: '/onboarding', builder: (c, s) => const OnboardingScreen()),
      GoRoute(path: '/', builder: (c, s) => const HomeScreen()),
      GoRoute(
        path: '/product/:id',
        builder: (c, s) => DetailScreen(productId: s.pathParameters['id']!),
      ),
      GoRoute(path: '/alerts', builder: (c, s) => const AlertsScreen()),
      GoRoute(path: '/settings', builder: (c, s) => const SettingsScreen()),
    ],
  );
}

class App extends StatelessWidget {
  final GoRouter router;
  const App({super.key, required this.router});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Oportunidades de Granos',
      theme: buildTheme(),
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
