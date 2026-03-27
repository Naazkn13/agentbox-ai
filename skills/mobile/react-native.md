---
id: react-native
name: React Native Expert
category: mobile
level1: "For React Native apps — components, StyleSheet, React Navigation, Expo, platform-specific code"
platforms: [claude-code, cursor, codex]
priority: 1
---

<!-- LEVEL 1 START -->
**React Native Expert** — Activate for: React Native, Expo, mobile app, FlatList, StyleSheet, React Navigation, Platform.OS, native modules, metro bundler.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## React Native — Core Instructions

1. **All text must be inside a `<Text>` component.** Strings outside `<Text>` crash at runtime. No exceptions.
2. **Use `StyleSheet.create()` for all styles.** Plain objects work but StyleSheet gives better performance via ID-based lookup and validation in dev mode.
3. **`FlatList` over `ScrollView` for long lists.** `ScrollView` renders all items at once; `FlatList` virtualizes — critical for performance with 100+ items.
4. **Use `KeyboardAvoidingView` for forms.** Wrap input forms with `<KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>` to prevent keyboard from covering inputs.
5. **Test on both iOS and Android early.** Platform differences (shadows, fonts, status bar, safe areas) surface at the end if you ignore them — use `Platform.OS` or platform-specific files (`.ios.ts` / `.android.ts`).
6. **Use `SafeAreaView` or `useSafeAreaInsets`.** Notches, dynamic islands, and home indicators eat into your layout on modern devices.
7. **Prefer Expo managed workflow for new projects.** It handles native builds, OTA updates, and the majority of native APIs without touching Xcode/Android Studio.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## React Native — Full Reference

### Core Components

```tsx
import {
  View, Text, StyleSheet, Pressable, TextInput,
  FlatList, ScrollView, Image, ActivityIndicator,
  Platform, SafeAreaView,
} from 'react-native';

// Basic layout
export default function Screen() {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Hello</Text>
      <Pressable
        style={({ pressed }) => [styles.btn, pressed && styles.btnPressed]}
        onPress={() => console.log('pressed')}
      >
        <Text style={styles.btnText}>Tap me</Text>
      </Pressable>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  title:     { fontSize: 24, fontWeight: 'bold', margin: 16 },
  btn:       { backgroundColor: '#007AFF', padding: 12, borderRadius: 8, margin: 16 },
  btnPressed:{ opacity: 0.7 },
  btnText:   { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
```

### FlatList (virtualized list)

```tsx
<FlatList
  data={items}
  keyExtractor={(item) => item.id.toString()}
  renderItem={({ item }) => <ItemCard item={item} />}
  ListEmptyComponent={<Text>No items found</Text>}
  ListHeaderComponent={<Text style={styles.header}>Results</Text>}
  onEndReached={loadMore}
  onEndReachedThreshold={0.5}
  refreshing={isRefreshing}
  onRefresh={handleRefresh}
/>
```

### React Navigation

```tsx
// Install: npm install @react-navigation/native @react-navigation/native-stack

import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Stack = createNativeStackNavigator();
const Tab   = createBottomTabNavigator();

function HomeTabs() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Feed"    component={FeedScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home"   component={HomeTabs} options={{ headerShown: false }} />
        <Stack.Screen name="Detail" component={DetailScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

// Navigate + pass params
navigation.navigate('Detail', { id: item.id });
// Receive params
const { id } = route.params;
```

### Platform-Specific Code

```tsx
import { Platform } from 'react-native';

// Inline
const shadow = Platform.select({
  ios:     { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
  android: { elevation: 4 },
});

// File-based (.ios.ts / .android.ts)
// Button.ios.ts   → used on iOS
// Button.android.ts → used on Android
// import Button from './Button';  ← Metro picks the right one
```

### Expo APIs

```tsx
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Camera / gallery
const result = await ImagePicker.launchImageLibraryAsync({
  mediaTypes: ImagePicker.MediaTypeOptions.Images,
  quality: 0.8,
});
if (!result.canceled) setImage(result.assets[0].uri);

// Persistent storage
await AsyncStorage.setItem('user', JSON.stringify(userData));
const raw = await AsyncStorage.getItem('user');
const user = raw ? JSON.parse(raw) : null;
```

### Anti-patterns to Avoid
- Putting text strings directly in `<View>` — crashes in production
- `ScrollView` for long dynamic lists — use `FlatList`
- Inline styles in render — creates new objects every render, use `StyleSheet.create`
- Missing `keyExtractor` on FlatList — causes reconciliation bugs
- Not handling safe area insets — UI hidden behind notch/home indicator on newer phones
<!-- LEVEL 3 END -->
