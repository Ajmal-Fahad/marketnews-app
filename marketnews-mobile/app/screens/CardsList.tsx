// marketnews-mobile/app/screens/CardsList.tsx
import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView,
  Alert,
} from "react-native";
import CardModal from "../components/CardModal";

// default backend base (change if needed)
const DEFAULT_API_BASE = "http://10.249.74.1:8000";

type AnnFile = {
  filename: string;
  symbol: string;
  company?: string;
  download_url?: string;
  filename_date?: string;
};

export default function CardsListScreen() {
  const [loading, setLoading] = useState<boolean>(true);
  const [files, setFiles] = useState<AnnFile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AnnFile | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  // If you already set API_BASE elsewhere in your app, replace this with that constant import
  const API_BASE = (global as any).API_BASE ?? DEFAULT_API_BASE;

  useEffect(() => {
    fetchList();
  }, []);

  async function fetchList() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/announcements/list-enriched`);
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status} ${res.statusText} ${txt}`);
      }
      const json = await res.json();
      // ensure we have files array
      const filesArr: AnnFile[] = (json?.files || []).map((f: any) => ({
        filename: f.filename,
        symbol: (f.symbol || f.filename || "").toString().replace(/\.[^.]+$/, ""),
        company: f.company || null,
        download_url: f.download_url || null,
        filename_date: f.filename_date || null,
      }));
      setFiles(filesArr);
    } catch (err: any) {
      console.warn("Failed to load announcements:", err?.message ?? err);
      setError(String(err?.message ?? err));
    } finally {
      setLoading(false);
    }
  }

  function openItem(item: AnnFile) {
    setSelected(item);
    setModalVisible(true);
  }

  function renderRow({ item }: { item: AnnFile }) {
    const displayCompany = item.company ?? item.symbol ?? item.filename;
    // filename_date may be "no-date" or "2025-09-16"
    const date = item.filename_date && item.filename_date !== "no-date" ? item.filename_date : "—";
    // We don't yet parse headline from image; show filename (clean) as fallback
    const headline = item.filename?.replace(/\.[^.]+$/, "").replace(/_/g, " ") ?? "Announcement";

    return (
      <TouchableOpacity style={styles.row} onPress={() => openItem(item)}>
        <View style={{ flex: 1 }}>
          <Text style={styles.company}>{displayCompany}</Text>
          <Text style={styles.headline} numberOfLines={2}>
            {headline}
          </Text>
          <Text style={styles.date}>{date}</Text>
        </View>

        <View style={styles.caretWrap}>
          <Text style={styles.caret}>›</Text>
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Announcements</Text>
        <TouchableOpacity onPress={fetchList}>
          <Text style={styles.refresh}>Refresh</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={{ color: "red", marginBottom: 8 }}>Failed to load announcements</Text>
          <TouchableOpacity
            onPress={() => {
              fetchList();
            }}
            style={styles.reloadBtn}
          >
            <Text style={{ color: "#fff" }}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={files}
          keyExtractor={(i) => i.filename}
          renderItem={renderRow}
          ItemSeparatorComponent={() => <View style={styles.sep} />}
          ListEmptyComponent={() => (
            <View style={styles.center}>
              <Text>No recent announcements</Text>
            </View>
          )}
          contentContainerStyle={{ paddingBottom: 40 }}
        />
      )}

      {/* Modal for selected announcement */}
      {selected && (
        <CardModal
          visible={modalVisible}
          onClose={() => setModalVisible(false)}
          // pass ticker (symbol) and company and backend base so modal can fetch market data
          ticker={selected.symbol}
          company={selected.company}
          announcementDate={selected.filename_date}
          announcementHeadline={selected.filename?.replace(/\.[^.]+$/, "").replace(/_/g, " ")}
          backendBaseUrl={API_BASE}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#eee",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerTitle: { fontSize: 18, fontWeight: "700" },
  refresh: { color: "#007aff", fontWeight: "600" },
  row: { flexDirection: "row", padding: 14, alignItems: "center" },
  company: { fontSize: 16, fontWeight: "700", marginBottom: 4 },
  headline: { color: "#333", marginBottom: 6 },
  date: { color: "#888", fontSize: 12 },
  caretWrap: { width: 30, alignItems: "center", justifyContent: "center" },
  caret: { fontSize: 24, color: "#ccc" },
  sep: { height: StyleSheet.hairlineWidth, backgroundColor: "#eee" },
  center: { padding: 30, alignItems: "center" },
  reloadBtn: {
    backgroundColor: "#000",
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
});