import React from "react";
import { View } from "react-native";

type Props = { style?: any; children?: React.ReactNode };
export const ThemedView: React.FC<Props> = ({ children, style }) => {
  return <View style={style}>{children}</View>;
};
export default ThemedView;
