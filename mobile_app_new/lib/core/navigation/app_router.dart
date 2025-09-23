import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../ui/screens/chat/chat_screen.dart';
import '../../ui/screens/settings/settings_screen.dart';
import '../../ui/screens/founder/founder_console_screen.dart';
import '../../ui/screens/splash/splash_screen.dart';
import '../../ui/screens/niche_radar/niche_radar_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    debugLogDiagnostics: true,
    routes: [
      // Splash Screen
      GoRoute(
        path: '/splash',
        name: 'splash',
        builder: (context, state) => const SplashScreen(),
      ),
      
      // Chat Screen (Main)
      GoRoute(
        path: '/chat',
        name: 'chat',
        builder: (context, state) => const ChatScreen(),
      ),
      
      // Settings Screen
      GoRoute(
        path: '/settings',
        name: 'settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      
      // Founder Console Screen
      GoRoute(
        path: '/founder',
        name: 'founder',
        builder: (context, state) => const FounderConsoleScreen(),
      ),
      
      // NicheRadar Screen
      GoRoute(
        path: '/niche-radar',
        name: 'niche-radar',
        builder: (context, state) => const NicheRadarScreen(),
      ),
    ],
    
    // Error handling
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.red,
            ),
            const SizedBox(height: 16),
            Text(
              'Page not found',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'The page you are looking for does not exist.',
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go('/chat'),
              child: const Text('Go to Chat'),
            ),
          ],
        ),
      ),
    ),
  );
});

// Navigation extensions for easier usage
extension AppRouterExtension on BuildContext {
  void goToChat() => go('/chat');
  void goToSettings() => go('/settings');
  void goToFounder() => go('/founder');
  void goToSplash() => go('/splash');
  void goToNicheRadar() => go('/niche-radar');
  
  void pushToSettings() => push('/settings');
  void pushToFounder() => push('/founder');
  void pushToNicheRadar() => push('/niche-radar');
}

// Route names for type safety
class AppRoutes {
  static const String splash = '/splash';
  static const String chat = '/chat';
  static const String settings = '/settings';
  static const String founder = '/founder';
  static const String nicheRadar = '/niche-radar';
}
