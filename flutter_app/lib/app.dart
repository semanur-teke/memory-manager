import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'theme/app_theme.dart';
import 'theme/colors.dart';
import 'widgets/empty_state.dart';

// Screen imports — Phase 1'de hepsi placeholder
import 'screens/home_screen.dart';
import 'screens/search_screen.dart';
import 'screens/gallery_screen.dart';
import 'screens/photo_detail_screen.dart';
import 'screens/timeline_screen.dart';
import 'screens/events_screen.dart';
import 'screens/event_detail_screen.dart';
import 'screens/flashcards_screen.dart';
import 'screens/review_screen.dart';
import 'screens/import_screen.dart';
import 'screens/privacy_screen.dart';
import 'screens/settings_screen.dart';

/// go_router yapilandirmasi
final _router = GoRouter(
  initialLocation: '/',
  routes: [
    // Shell route — NavigationRail her sayfada gorunur
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
        GoRoute(path: '/search', builder: (_, __) => const SearchScreen()),
        GoRoute(path: '/gallery', builder: (_, __) => const GalleryScreen()),
        GoRoute(path: '/timeline', builder: (_, __) => const TimelineScreen()),
        GoRoute(path: '/events', builder: (_, __) => const EventsScreen()),
        GoRoute(path: '/flashcards', builder: (_, __) => const FlashcardsScreen()),
        GoRoute(path: '/import', builder: (_, __) => const ImportScreen()),
        GoRoute(path: '/privacy', builder: (_, __) => const PrivacyScreen()),
        GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
      ],
    ),
    // Shell disindaki sayfalar (detay sayfalari — NavigationRail gizlenir)
    GoRoute(
      path: '/gallery/:id',
      builder: (_, state) => PhotoDetailScreen(
        id: state.pathParameters['id']!,
      ),
    ),
    GoRoute(
      path: '/events/:id',
      builder: (_, state) => EventDetailScreen(
        id: state.pathParameters['id']!,
      ),
    ),
    GoRoute(
      path: '/review',
      builder: (_, __) => const ReviewScreen(),
    ),
  ],
);

/// Navigasyon route'lari ve index eslesmesi
const _navRoutes = [
  '/',          // 0 - Ana Sayfa
  '/search',    // 1 - Arama
  '/gallery',   // 2 - Galeri
  '/timeline',  // 3 - Timeline
  '/events',    // 4 - Olaylar
  '/flashcards',// 5 - Flashcard
  '/import',    // 6 - Import
  '/privacy',   // 7 - Gizlilik
  '/settings',  // 8 - Ayarlar
];

/// Ana uygulama widget'i
class MemoryManagerApp extends ConsumerWidget {
  const MemoryManagerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'Memory Manager',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme(),
      darkTheme: AppTheme.darkTheme(),
      themeMode: ThemeMode.light,
      routerConfig: _router,
    );
  }
}

/// App shell — NavigationRail + icerik alani
class AppShell extends StatelessWidget {
  final Widget child;
  const AppShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    // Mevcut route'a gore secili index'i bul
    final location = GoRouterState.of(context).uri.toString();
    int selectedIndex = _navRoutes.indexOf(location);
    if (selectedIndex < 0) selectedIndex = 0;

    return Scaffold(
      body: Row(
        children: [
          // Sol kenar menu
          NavigationRail(
            selectedIndex: selectedIndex,
            labelType: NavigationRailLabelType.all,
            onDestinationSelected: (index) {
              context.go(_navRoutes[index]);
            },
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Icon(
                Icons.memory,
                size: 32,
                color: AppColors.primary,
              ),
            ),
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.home_outlined),
                selectedIcon: Icon(Icons.home),
                label: Text('Ana Sayfa'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.search_outlined),
                selectedIcon: Icon(Icons.search),
                label: Text('Arama'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.photo_library_outlined),
                selectedIcon: Icon(Icons.photo_library),
                label: Text('Galeri'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.timeline_outlined),
                selectedIcon: Icon(Icons.timeline),
                label: Text('Timeline'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.event_outlined),
                selectedIcon: Icon(Icons.event),
                label: Text('Olaylar'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.quiz_outlined),
                selectedIcon: Icon(Icons.quiz),
                label: Text('Flashcard'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.upload_file_outlined),
                selectedIcon: Icon(Icons.upload_file),
                label: Text('Import'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.security_outlined),
                selectedIcon: Icon(Icons.security),
                label: Text('Gizlilik'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.settings_outlined),
                selectedIcon: Icon(Icons.settings),
                label: Text('Ayarlar'),
              ),
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1),
          // Icerik alani
          Expanded(child: child),
        ],
      ),
    );
  }
}
