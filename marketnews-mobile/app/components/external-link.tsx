import React from "react";
import { Linking, Text, TouchableOpacity } from "react-native";

type Props = { href?: string; children?: React.ReactNode };
export const ExternalLink: React.FC<Props> = ({ href, children }) => {
  return (
    <TouchableOpacity onPress={() => href && Linking.openURL(href)}>
      <Text style={{ color: "#1e88e5" }}>{children}</Text>
    </TouchableOpacity>
  );
};
export default ExternalLink;
