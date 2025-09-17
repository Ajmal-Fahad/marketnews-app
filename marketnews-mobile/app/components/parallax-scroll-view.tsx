import React from "react";
import { ScrollView, View } from "react-native";

/**
 * Minimal wrapper for parallax-like area used in the web demo.
 * This will just render children inside a ScrollView container.
 */
export const ParallaxScrollView: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  return (
    <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
      <View>{children}</View>
    </ScrollView>
  );
};
export default ParallaxScrollView;
