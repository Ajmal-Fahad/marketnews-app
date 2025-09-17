import React from "react";
import { Text, TouchableOpacity } from "react-native";

export default function HapticTab({ title }: { title: string }) {
  return (
    <TouchableOpacity
      style={{ padding: 10, backgroundColor: "#eee", margin: 5, borderRadius: 8 }}
      onPress={() => console.log("HapticTab pressed:", title)}
    >
      <Text>{title}</Text>
    </TouchableOpacity>
  );
}
