import React from "react";
import { Text } from "react-native";

type Props = { style?: any; children?: React.ReactNode };
export const ThemedText: React.FC<Props> = ({ children, style }) => {
  return <Text style={style}>{children}</Text>;
};
export default ThemedText;
