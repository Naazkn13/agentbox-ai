---
id: flutter
name: Flutter Expert
category: mobile
level1: "For Flutter apps — widgets, Riverpod/Bloc state, GoRouter, Dart async, pub.dev packages"
platforms: [claude-code, cursor, codex]
priority: 1
---

<!-- LEVEL 1 START -->
**Flutter Expert** — Activate for: Flutter, Dart, widget, StatelessWidget, StatefulWidget, Provider, Riverpod, Bloc, GoRouter, pubspec.yaml, hot reload, FutureBuilder, StreamBuilder.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Flutter — Core Instructions

1. **Prefer `StatelessWidget` + Riverpod over `StatefulWidget`.** `setState` couples UI to state logic — Riverpod providers are testable, composable, and auto-disposed.
2. **Never do async work in `build()`.** Build must be pure and fast. Use `FutureBuilder`, `StreamBuilder`, or a Riverpod `AsyncNotifier` to handle async state.
3. **Extract widgets early.** Large `build()` methods are hard to read. Extract into named `Widget` methods or separate classes when a section has 3+ levels of nesting.
4. **Use `const` constructors wherever possible.** `const Text('Hello')` skips rebuild — Flutter's diff algorithm skips subtrees rooted at `const` widgets.
5. **GoRouter for navigation in production apps.** It supports deep linking, guards, and URL-based routing — `Navigator.push` doesn't scale.
6. **Handle loading/error states in every async widget.** `AsyncValue` in Riverpod has `.when(data:, loading:, error:)` — always handle all three cases.
7. **Run `flutter analyze` before committing.** Dart's analyzer catches null safety issues, unused imports, and common mistakes that tests might miss.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Flutter — Full Reference

### Widget Basics

```dart
// StatelessWidget — for pure UI with no mutable state
class UserCard extends StatelessWidget {
  const UserCard({super.key, required this.user});
  final User user;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(backgroundImage: NetworkImage(user.avatarUrl)),
        title: Text(user.name),
        subtitle: Text(user.email),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}

// StatefulWidget — use sparingly (forms, animations)
class CounterWidget extends StatefulWidget {
  const CounterWidget({super.key});
  @override
  State<CounterWidget> createState() => _CounterWidgetState();
}

class _CounterWidgetState extends State<CounterWidget> {
  int _count = 0;
  @override
  Widget build(BuildContext context) => TextButton(
    onPressed: () => setState(() => _count++),
    child: Text('Count: $_count'),
  );
}
```

### Riverpod State Management

```dart
// pubspec.yaml: flutter_riverpod: ^2.x

import 'package:flutter_riverpod/flutter_riverpod.dart';

// Simple state provider
final counterProvider = StateProvider<int>((ref) => 0);

// Async provider (fetch from API)
final userProvider = FutureProvider.family<User, String>((ref, userId) async {
  final repo = ref.watch(userRepositoryProvider);
  return repo.fetchUser(userId);
});

// Notifier (complex state)
class CartNotifier extends AsyncNotifier<List<CartItem>> {
  @override
  Future<List<CartItem>> build() => ref.watch(cartRepositoryProvider).getItems();

  Future<void> addItem(Product product) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => ref.read(cartRepositoryProvider).addItem(product));
  }
}
final cartProvider = AsyncNotifierProvider<CartNotifier, List<CartItem>>(CartNotifier.new);

// Consume in widget
class CartScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cart = ref.watch(cartProvider);
    return cart.when(
      data:    (items) => ListView(children: items.map((i) => CartItemTile(item: i)).toList()),
      loading: () => const CircularProgressIndicator(),
      error:   (e, _) => Text('Error: $e'),
    );
  }
}
```

### GoRouter Navigation

```dart
// pubspec.yaml: go_router: ^13.x

final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (ctx, state) => const HomeScreen()),
    GoRoute(
      path: '/product/:id',
      builder: (ctx, state) => ProductScreen(id: state.pathParameters['id']!),
    ),
    ShellRoute(
      builder: (ctx, state, child) => ScaffoldWithNavBar(child: child),
      routes: [
        GoRoute(path: '/feed',    builder: (_, __) => const FeedScreen()),
        GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
      ],
    ),
  ],
  redirect: (ctx, state) {
    final isLoggedIn = ctx.read(authProvider).isLoggedIn;
    if (!isLoggedIn && state.matchedLocation != '/login') return '/login';
    return null;
  },
);

// Navigate
context.go('/product/42');       // replace stack
context.push('/product/42');     // push onto stack
context.pop();
```

### Dart Async Patterns

```dart
// Future
Future<User> fetchUser(String id) async {
  final response = await http.get(Uri.parse('/api/users/$id'));
  if (response.statusCode != 200) throw Exception('Failed: ${response.statusCode}');
  return User.fromJson(jsonDecode(response.body));
}

// Stream
Stream<List<Message>> watchMessages(String roomId) {
  return firestore.collection('rooms/$roomId/messages')
      .orderBy('createdAt')
      .snapshots()
      .map((snap) => snap.docs.map((d) => Message.fromDoc(d)).toList());
}

// FutureBuilder / StreamBuilder
StreamBuilder<List<Message>>(
  stream: watchMessages(roomId),
  builder: (context, snapshot) {
    if (snapshot.hasError)   return Text('Error: ${snapshot.error}');
    if (!snapshot.hasData)   return const CircularProgressIndicator();
    return MessageList(messages: snapshot.data!);
  },
)
```

### Anti-patterns to Avoid
- `setState` in large widget trees — causes full subtree rebuild; use Riverpod
- `Navigator.push` directly — bypasses route guards and deep link support; use GoRouter
- Async calls in `initState` without error handling — unhandled futures crash silently
- Missing `const` on immutable widgets — wastes rebuild cycles
- `pub.dev` packages with low pub points / no null safety — check scores before adding
<!-- LEVEL 3 END -->
