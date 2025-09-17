// marketnews-mobile/app/(tabs)/_layout.tsx
import { Tabs } from "expo-router";
import React from "react";

import { HapticTab } from "../components/haptic-tab";
import { IconSymbol } from "../components/ui/icon-symbol";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

/**
 * NOTE:
 * - The app/(tabs)/cards.tsx file should render the CardsList screen (or you can import the screen here).
 * - The CardsList screen file should be at: app/screens/CardsList.tsx (exact name & casing).
 */

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme ?? "light"].tint,
        headerShown: false,
        tabBarButton: HapticTab,
      }}
    >
      {/* Home Tab */}
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="house.fill" color={color} />
          ),
        }}
      />

      {/* Explore Tab */}
      <Tabs.Screen
        name="explore"
        options={{
          title: "Explore",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="paperplane.fill" color={color} />
          ),
        }}
      />

      {/* Cards Tab - the router will load app/(tabs)/cards.tsx or app/screens/CardsList.tsx */}
      <Tabs.Screen
        name="cards"
        options={{
          title: "Cards",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="rectangle.stack.fill" color={color} />
          ),
        }}
      />
    </Tabs>
  );
}