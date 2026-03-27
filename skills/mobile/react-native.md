---
id: react-native
name: React Native Expert
category: mobile
level1: "For React Native apps — components, StyleSheet, React Navigation, Expo, platform-specific code"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**React Native Expert** — Activate for: React Native components, StyleSheet, FlatList, ScrollView, React Navigation, Expo managed/bare workflow, platform-specific code, AsyncStorage, debugging with Flipper, React Native gotchas.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## React Native Expert — Core Instructions

1. **All text must be inside a `<Text>` component** — React Native has no implicit text rendering. Any string outside `<Text>` will throw a runtime error. This is the #1 beginner mistake.
2. **Use `StyleSheet.create()`, never inline objects** — inline style objects are re-created on every render. `StyleSheet.create()` validates styles at creation time and is more performant.
3. **Use `FlatList` for any scrolling list, never `ScrollView` with `.map()`** — `ScrollView` renders all children at once; `FlatList` virtualizes and only renders visible rows. Use `ScrollView` only for short, static content.
4. **Handle platform differences with `Platform.OS`** — iOS and Android behave differently for shadows, fonts, status bar, and keyboard behavior. Always check before assuming cross-platform behavior.
5. **Use React Navigation for all navigation** — never build custom navigation stacks. React Navigation handles deep links, back button, and tab state correctly.
6. **Prefer Expo managed workflow unless you need native modules** — Expo handles build config, OTA updates, and native APIs. Switch to bare workflow only when you need a native module not in Expo SDK.
7. **Debug with Flipper or Reactotron, not just console.log** — `console.log` output is lost on device. Flipper gives network inspection, Redux DevTools, and React DevTools in one tool.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## React Native Expert — Full Reference

### Core Components

```jsx
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Pressable,
  FlatList,
  ScrollView,
  Image,
  ActivityIndicator,
  StyleSheet,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';

// View — basic layout container (like div in web)
// Text — required wrapper for ALL text strings
// FlatList — virtualized list for long data sets
// ScrollView — non-virtualized scroll (short static content only)
// TouchableOpacity — touchable with opacity feedback
// Pressable — modern touchable with more control over press states

function ProductCard({ item, onPress }) {
  return (
    <Pressable
      onPress={() => onPress(item.id)}
      style={({ pressed }) => [
        styles.card,
        pressed && styles.cardPressed,
      ]}
    >
      <Image source={{ uri: item.imageUrl }} style={styles.image} />
      <View style={styles.info}>
        <Text style={styles.title} numberOfLines={2}>{item.name}</Text>
        <Text style={styles.price}>${item.price.toFixed(2)}</Text>
      </View>
    </Pressable>
  );
}

// FlatList — always prefer over ScrollView + map for lists
function ProductList({ products }) {
  const renderItem = useCallback(({ item }) => (
    <ProductCard item={item} onPress={(id) => console.log('pressed', id)} />
  ), []);

  const keyExtractor = useCallback((item) => item.id.toString(), []);

  return (
    <FlatList
      data={products}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      numColumns={2}
      contentContainerStyle={styles.listContainer}
      ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
      ListEmptyComponent={<Text style={styles.empty}>No products found</Text>}
      ListHeaderComponent={<Text style={styles.header}>Products</Text>}
      onEndReachedThreshold={0.5}
      onEndReached={() => console.log('load more')}
    />
  );
}
```

### StyleSheet.create

```jsx
const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    // iOS shadow
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    // Android shadow
    elevation: 3,
  },
  cardPressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
  image: {
    width: '100%',
    height: 160,
    resizeMode: 'cover',
  },
  info: {
    padding: 12,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  price: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2563EB',
  },
  listContainer: {
    padding: 16,
    paddingBottom: 80,
  },
  header: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 16,
    color: '#111',
  },
  empty: {
    textAlign: 'center',
    color: '#666',
    marginTop: 40,
  },
});
```

### React Navigation

```jsx
// Installation:
// npx expo install @react-navigation/native @react-navigation/native-stack
// @react-navigation/bottom-tabs react-native-screens react-native-safe-area-context

import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Tab navigator (root)
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#2563EB',
        tabBarInactiveTintColor: '#9CA3AF',
        headerShown: false,
      }}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

// Stack navigator wraps tabs and adds detail/modal screens
function RootNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
        <Stack.Screen
          name="ProductDetail"
          component={ProductDetailScreen}
          options={({ route }) => ({ title: route.params.productName })}
        />
        <Stack.Screen
          name="Checkout"
          component={CheckoutScreen}
          options={{ presentation: 'modal' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

// Navigate and pass params
function HomeScreen({ navigation }) {
  return (
    <TouchableOpacity onPress={() => navigation.navigate('ProductDetail', {
      productId: '123',
      productName: 'Widget Pro',
    })}>
      <Text>Go to Product</Text>
    </TouchableOpacity>
  );
}

// Access params in destination
function ProductDetailScreen({ route, navigation }) {
  const { productId, productName } = route.params;
  return <Text>{productName}</Text>;
}
```

### Platform.OS for Platform-Specific Code

```jsx
import { Platform, StatusBar, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    // Android has a translucent status bar; iOS uses SafeAreaView
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  // Platform.select picks the right block at runtime
  shadow: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
    },
    android: {
      elevation: 4,
    },
  }),
});

// KeyboardAvoidingView — behavior differs per platform
<KeyboardAvoidingView
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
  style={{ flex: 1 }}
>
  <TextInput placeholder="Enter text" />
</KeyboardAvoidingView>

// Platform-specific component files (automatic resolution)
// Button.ios.js      → loaded on iOS
// Button.android.js  → loaded on Android
// import Button from './Button'  — RN picks the right file automatically
```

### Expo Managed vs Bare Workflow

| Feature | Managed | Bare |
|---|---|---|
| Setup | `npx create-expo-app` | `npx react-native init` |
| Native modules | Expo SDK only | Any npm native module |
| Build | EAS Build / Expo Go | Xcode + Android Studio |
| OTA updates | Expo Updates built-in | Manual setup |
| When to use | 90% of apps | Custom native code, Bluetooth, etc. |

```bash
# Managed workflow
npx create-expo-app MyApp
npx expo start           # start dev server
eas build --platform all  # EAS cloud build

# Eject to bare (one-way, irreversible)
npx expo prebuild        # generates ios/ and android/ native directories
```

### Hooks in React Native

```jsx
import { useState, useEffect, useCallback } from 'react';
import { AppState, Dimensions } from 'react-native';

// Track app foreground/background state
function useAppState() {
  const [appState, setAppState] = useState(AppState.currentState);
  useEffect(() => {
    const sub = AppState.addEventListener('change', setAppState);
    return () => sub.remove();
  }, []);
  return appState;
}

// Track screen dimensions (handles rotation)
function useDimensions() {
  const [dims, setDims] = useState(Dimensions.get('window'));
  useEffect(() => {
    const sub = Dimensions.addEventListener('change', ({ window }) => setDims(window));
    return () => sub.remove();
  }, []);
  return dims;
}

// Debounced search input
function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

### AsyncStorage

```jsx
// npx expo install @react-native-async-storage/async-storage
import AsyncStorage from '@react-native-async-storage/async-storage';

// Save and load
await AsyncStorage.setItem('user_token', token);
const token = await AsyncStorage.getItem('user_token');  // null if not set

// JSON values
await AsyncStorage.setItem('user_prefs', JSON.stringify({ theme: 'dark' }));
const prefs = JSON.parse(await AsyncStorage.getItem('user_prefs') ?? '{}');

// Remove
await AsyncStorage.removeItem('user_token');

// Persisted state hook
function usePersistedState(key, defaultValue) {
  const [value, setValue] = useState(defaultValue);

  useEffect(() => {
    AsyncStorage.getItem(key).then(stored => {
      if (stored !== null) setValue(JSON.parse(stored));
    });
  }, [key]);

  const setAndPersist = useCallback(async (newValue) => {
    setValue(newValue);
    await AsyncStorage.setItem(key, JSON.stringify(newValue));
  }, [key]);

  return [value, setAndPersist];
}
```

### Debugging with Flipper / Reactotron

```jsx
// Flipper — built into React Native 0.62+; open Flipper desktop app
// Plugins: React DevTools, Network Inspector, Redux DevTools, Crash Reporter

// Reactotron setup (alternative)
// npm install reactotron-react-native
if (__DEV__) {
  const Reactotron = require('reactotron-react-native').default;
  Reactotron
    .configure({ host: '192.168.1.x' })  // your machine's LAN IP
    .useReactNative()
    .connect();
  // Use console.tron.log() for structured output in Reactotron
}

// Chrome DevTools remote debugging
// Shake device → "Debug with Chrome" → opens DevTools in browser
// Or use standalone React Native Debugger app (preferred)
```

### Common Gotchas

| Gotcha | Problem | Fix |
|---|---|---|
| Text outside `<Text>` | Runtime crash on render | Always wrap strings in `<Text>` |
| `ScrollView` with large lists | Renders all items, slow/OOM | Use `FlatList` instead |
| No CSS floats | Web layout patterns don't work | Use Flexbox with `flexDirection` |
| Missing `key` prop in lists | React reconciliation warnings | Set `keyExtractor` in FlatList |
| Fonts not loading on Android | Font name differs from iOS | Use `expo-font` with exact PostScript name |
| Keyboard covers input | Input hidden by keyboard | Wrap in `KeyboardAvoidingView` |
| `elevation` ignored on iOS | Shadow system differs | Use `shadowColor/Offset/Opacity/Radius` for iOS |

### Anti-patterns to Avoid
- `ScrollView` wrapping a large `.map()` — always use `FlatList` with `keyExtractor`
- Inline style objects `style={{ color: 'red' }}` in render — use `StyleSheet.create()`
- Text strings directly in `<View>` — they must always be inside `<Text>`
- `console.log` as the only debugging tool on device — use Flipper or Reactotron
- Not memoizing `renderItem` and `keyExtractor` in FlatList — causes full list re-renders on every parent state change
- Using web CSS properties (float, display: flex shorthand, z-index without position) — not all CSS properties exist in RN
<!-- LEVEL 3 END -->
