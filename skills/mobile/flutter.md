---
id: flutter
name: Flutter Expert
category: mobile
level1: "For Flutter apps — widgets, state management (Riverpod/Bloc), GoRouter, Dart async, pub.dev"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Flutter Expert** — Activate for: Flutter widgets, StatelessWidget vs StatefulWidget, setState, Riverpod, Bloc, GoRouter navigation, Dart async/await/Stream, FutureBuilder, StreamBuilder, platform channels, pub.dev packages, widget testing, integration testing.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Flutter Expert — Core Instructions

1. **Prefer `StatelessWidget` by default; only use `StatefulWidget` when you must hold mutable local UI state** — excessive `StatefulWidget` use leads to scattered state and hard-to-test code. If state is shared across widgets, lift it to Riverpod or Bloc.
2. **Use Riverpod for app state, `setState` only for purely local ephemeral UI state** — Riverpod is compile-safe, testable, and does not require a BuildContext to read state. Bloc is preferred in teams that need strict separation of events and states.
3. **Never call async work inside `build()`** — `build()` is called on every frame. Call async work in `initState()`, event handlers, or Riverpod providers.
4. **Use GoRouter for all navigation** — Navigator 1.0 (`push`/`pop`) cannot handle deep links or web URLs. GoRouter handles both with declarative route definitions.
5. **Use `const` constructors wherever possible** — `const` widgets are never rebuilt if their inputs haven't changed. Adding `const` is the easiest Flutter performance win.
6. **Always await Futures; never `Future<void>` fire-and-forget in event handlers** — unhandled errors in unawaited Futures are silently swallowed. Use `unawaited()` from `package:meta` explicitly when intentional.
7. **Check pub.dev scores before adding a package** — look at likes, pub points (max 140), and popularity score. Avoid packages with no null safety, no maintenance in 2+ years, or pub points below 80.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Flutter Expert — Full Reference

### StatelessWidget vs StatefulWidget

```dart
// StatelessWidget — no mutable state; rebuild driven by parent
class ProductCard extends StatelessWidget {
  const ProductCard({
    super.key,
    required this.product,
    required this.onTap,
  });

  final Product product;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Image.network(product.imageUrl, fit: BoxFit.cover),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(product.name,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  Text('\$${product.price.toStringAsFixed(2)}',
                      style: const TextStyle(fontSize: 14, color: Colors.grey)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// StatefulWidget — use ONLY for local ephemeral UI state
// Good examples: expansion panel open/closed, text field focus, local animation
class ExpandableSection extends StatefulWidget {
  const ExpandableSection({super.key, required this.title, required this.child});
  final String title;
  final Widget child;

  @override
  State<ExpandableSection> createState() => _ExpandableSectionState();
}

class _ExpandableSectionState extends State<ExpandableSection> {
  bool _isExpanded = false;  // purely local UI state — fine to use setState

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        GestureDetector(
          onTap: () => setState(() => _isExpanded = !_isExpanded),
          child: Row(
            children: [
              Text(widget.title),
              Icon(_isExpanded ? Icons.expand_less : Icons.expand_more),
            ],
          ),
        ),
        if (_isExpanded) widget.child,
      ],
    );
  }
}
```

### Material and Cupertino Widgets

```dart
// Material widgets (cross-platform, Google design)
Scaffold(
  appBar: AppBar(title: const Text('Products')),
  body: ListView.builder(...),
  floatingActionButton: FloatingActionButton(
    onPressed: () {},
    child: const Icon(Icons.add),
  ),
  bottomNavigationBar: NavigationBar(
    selectedIndex: _selectedIndex,
    onDestinationSelected: (i) => setState(() => _selectedIndex = i),
    destinations: const [
      NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
      NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
    ],
  ),
);

// Cupertino widgets (iOS look and feel)
import 'package:flutter/cupertino.dart';

CupertinoPageScaffold(
  navigationBar: const CupertinoNavigationBar(middle: Text('Products')),
  child: CupertinoListSection.insetGrouped(
    children: [
      CupertinoListTile(title: const Text('Item 1')),
    ],
  ),
);

// Platform-adaptive pattern
Widget buildButton(BuildContext context) {
  if (Theme.of(context).platform == TargetPlatform.iOS) {
    return CupertinoButton(onPressed: () {}, child: const Text('Submit'));
  }
  return ElevatedButton(onPressed: () {}, child: const Text('Submit'));
}
```

### State Management: Riverpod

```dart
// pubspec.yaml: flutter_riverpod: ^2.x, riverpod_annotation: ^2.x

import 'package:flutter_riverpod/flutter_riverpod.dart';

// Simple state provider
final counterProvider = StateProvider<int>((ref) => 0);

// Async provider — fetches data and caches it
final productsProvider = FutureProvider<List<Product>>((ref) async {
  final repo = ref.read(productRepositoryProvider);
  return repo.fetchProducts();
});

// Notifier — complex state with methods
@riverpod
class CartNotifier extends _$CartNotifier {
  @override
  List<CartItem> build() => [];  // initial state

  void addItem(Product product) {
    final existing = state.indexWhere((i) => i.productId == product.id);
    if (existing >= 0) {
      state = [
        ...state.sublist(0, existing),
        state[existing].copyWith(quantity: state[existing].quantity + 1),
        ...state.sublist(existing + 1),
      ];
    } else {
      state = [...state, CartItem(productId: product.id, quantity: 1)];
    }
  }

  void removeItem(String productId) {
    state = state.where((i) => i.productId != productId).toList();
  }
}

// ConsumerWidget — reads providers
class ProductListScreen extends ConsumerWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(productsProvider);

    return productsAsync.when(
      data: (products) => ListView.builder(
        itemCount: products.length,
        itemBuilder: (context, i) => ProductCard(
          product: products[i],
          onTap: () => ref.read(cartNotifierProvider.notifier).addItem(products[i]),
        ),
      ),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
    );
  }
}
```

### State Management: Bloc

```dart
// pubspec.yaml: flutter_bloc: ^8.x, bloc: ^8.x

// Events
abstract class CartEvent {}
class AddToCart extends CartEvent { final Product product; AddToCart(this.product); }
class RemoveFromCart extends CartEvent { final String productId; RemoveFromCart(this.productId); }

// State
class CartState {
  const CartState({this.items = const []});
  final List<CartItem> items;
  int get totalCount => items.fold(0, (sum, i) => sum + i.quantity);
  CartState copyWith({List<CartItem>? items}) => CartState(items: items ?? this.items);
}

// Bloc
class CartBloc extends Bloc<CartEvent, CartState> {
  CartBloc() : super(const CartState()) {
    on<AddToCart>((event, emit) {
      final existing = state.items.indexWhere((i) => i.productId == event.product.id);
      if (existing >= 0) {
        final updated = List<CartItem>.from(state.items);
        updated[existing] = updated[existing].copyWith(quantity: updated[existing].quantity + 1);
        emit(state.copyWith(items: updated));
      } else {
        emit(state.copyWith(items: [...state.items, CartItem(productId: event.product.id, quantity: 1)]));
      }
    });
    on<RemoveFromCart>((event, emit) {
      emit(state.copyWith(items: state.items.where((i) => i.productId != event.productId).toList()));
    });
  }
}

// Widget
BlocBuilder<CartBloc, CartState>(
  builder: (context, state) {
    return Text('Cart: ${state.totalCount} items');
  },
);
```

### GoRouter Navigation

```dart
// pubspec.yaml: go_router: ^13.x

import 'package:go_router/go_router.dart';

final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (ctx, state) => const HomeScreen()),
    GoRoute(
      path: '/product/:id',
      builder: (ctx, state) {
        final id = state.pathParameters['id']!;
        return ProductDetailScreen(productId: id);
      },
    ),
    GoRoute(
      path: '/checkout',
      pageBuilder: (ctx, state) => const MaterialPage(
        fullscreenDialog: true,
        child: CheckoutScreen(),
      ),
    ),
    ShellRoute(
      builder: (ctx, state, child) => MainShell(child: child),
      routes: [
        GoRoute(path: '/home', builder: (ctx, state) => const HomeTab()),
        GoRoute(path: '/search', builder: (ctx, state) => const SearchTab()),
        GoRoute(path: '/profile', builder: (ctx, state) => const ProfileTab()),
      ],
    ),
  ],
  errorBuilder: (ctx, state) => ErrorScreen(error: state.error),
);

// Navigate
context.go('/product/123');           // replace current route
context.push('/product/123');         // push onto stack
context.pop();                        // go back
context.goNamed('product', pathParameters: {'id': '123'});

// Wrap app
MaterialApp.router(routerConfig: router);
```

### Dart Async / Await / Stream

```dart
// Future — single async value
Future<List<Product>> fetchProducts() async {
  try {
    final response = await http.get(Uri.parse('https://api.example.com/products'));
    if (response.statusCode != 200) {
      throw HttpException('Failed: ${response.statusCode}');
    }
    final data = jsonDecode(response.body) as List;
    return data.map((e) => Product.fromJson(e)).toList();
  } on SocketException {
    throw NetworkException('No internet connection');
  }
}

// Stream — multiple values over time
Stream<int> countdown(int from) async* {
  for (int i = from; i >= 0; i--) {
    yield i;
    await Future.delayed(const Duration(seconds: 1));
  }
}

// Listen to a stream
final sub = countdown(10).listen(
  (count) => print(count),
  onError: (e) => print('Error: $e'),
  onDone: () => print('Done'),
);
await Future.delayed(const Duration(seconds: 15));
sub.cancel();
```

### FutureBuilder and StreamBuilder

```dart
// FutureBuilder — for one-time async data
FutureBuilder<List<Product>>(
  future: fetchProducts(),  // call in initState or provider, not here
  builder: (context, snapshot) {
    if (snapshot.connectionState == ConnectionState.waiting) {
      return const CircularProgressIndicator();
    }
    if (snapshot.hasError) {
      return Text('Error: ${snapshot.error}');
    }
    final products = snapshot.data!;
    return ListView.builder(
      itemCount: products.length,
      itemBuilder: (ctx, i) => ProductCard(product: products[i], onTap: () {}),
    );
  },
);

// StreamBuilder — for real-time data (websocket, Firebase, etc.)
StreamBuilder<List<Message>>(
  stream: chatRepository.messagesStream(roomId),
  builder: (context, snapshot) {
    if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
    final messages = snapshot.data!;
    return ListView.builder(
      reverse: true,
      itemCount: messages.length,
      itemBuilder: (ctx, i) => MessageBubble(message: messages[i]),
    );
  },
);
```

### Platform Channels for Native Code

```dart
// Dart side
import 'package:flutter/services.dart';

class BatteryService {
  static const _channel = MethodChannel('com.example.app/battery');

  Future<int> getBatteryLevel() async {
    try {
      final level = await _channel.invokeMethod<int>('getBatteryLevel');
      return level ?? -1;
    } on PlatformException catch (e) {
      throw Exception('Failed to get battery: ${e.message}');
    }
  }
}
```

```kotlin
// Android side (MainActivity.kt)
MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "com.example.app/battery")
  .setMethodCallHandler { call, result ->
    if (call.method == "getBatteryLevel") {
      val batteryLevel = getBatteryLevel()
      if (batteryLevel != -1) result.success(batteryLevel)
      else result.error("UNAVAILABLE", "Battery not available", null)
    } else result.notImplemented()
  }
```

### Hot Reload vs Hot Restart

| Operation | What it Does | When to Use |
|---|---|---|
| Hot Reload (r) | Injects new code, preserves state | UI changes, widget edits |
| Hot Restart (R) | Restarts app, clears state | State class changes, new providers, initState changes |
| Full restart | Cold start from scratch | Native code changes, pubspec changes |

### pub.dev Package Hygiene

```yaml
# Good package checklist:
# - Pub points >= 110/140 (null safety, docs, platform support)
# - Likes >= 100 (community trust)
# - Last published < 6 months ago OR actively maintained
# - Supports your Flutter version (check "Versions" tab)

# pubspec.yaml — pin major versions, allow minor patches
dependencies:
  flutter_riverpod: ^2.5.0    # allows 2.5.x and 2.6.x etc
  go_router: ^13.0.0
  http: ^1.2.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  riverpod_generator: ^2.4.0
  build_runner: ^2.4.0

# After adding packages:
flutter pub get
dart pub outdated      # check for newer versions
dart pub upgrade --major-versions  # upgrade to latest majors
```

### Testing: Widget Tests and Integration Tests

```dart
// Widget test
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('ProductCard displays name and price', (WidgetTester tester) async {
    final product = Product(id: '1', name: 'Widget Pro', price: 29.99, imageUrl: '');

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ProductCard(product: product, onTap: () {}),
        ),
      ),
    );

    expect(find.text('Widget Pro'), findsOneWidget);
    expect(find.text('\$29.99'), findsOneWidget);
  });

  testWidgets('Counter increments when FAB is tapped', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: CounterScreen()));

    expect(find.text('0'), findsOneWidget);
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();
    expect(find.text('1'), findsOneWidget);
  });
}

// Integration test (runs on real device/emulator)
// test/integration_test/app_test.dart
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Full checkout flow', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('product-1')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Add to Cart'));
    await tester.pumpAndSettle();
    expect(find.text('Cart: 1 items'), findsOneWidget);
  });
}
```

### Anti-patterns to Avoid
- Calling async work inside `build()` — `build()` runs on every frame; move async calls to `initState()`, event handlers, or providers
- Using `StatefulWidget` when Riverpod or Bloc would share state across screens
- `Navigator.push()` instead of GoRouter — cannot handle deep links or web URLs
- Not using `const` constructors — missing `const` causes unnecessary widget rebuilds on every parent rebuild
- Blocking the UI thread with synchronous I/O or heavy computation — use `compute()` or `Isolate.run()` for CPU-intensive work
- Adding packages without checking pub points and last-published date — unmaintained packages break on Flutter updates
<!-- LEVEL 3 END -->
