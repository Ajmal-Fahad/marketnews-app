import React from "react";
import { Text } from "react-native";

type Props = { size?: number; name?: string; color?: string };
export const IconSymbol: React.FC<Props> = ({ size = 24, name = "?", color = "#000" }) => {
  return <Text style={{ fontSize: size, color }}>{String(name).charAt(0).toUpperCase()}</Text>;
};
export default IconSymbol;
