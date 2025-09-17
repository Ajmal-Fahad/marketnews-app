// marketnews-mobile/app/components/CardModal.tsx
import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView,
  Linking,
  Dimensions,
  Alert,
} from "react-native";

type Props = {
  visible: boolean;
  onClose: () => void;
  ticker?: string; // symbol like INFY or LT
  company?: string | null;
  announcementDate?: string | null; // filename_date if present
  announcementHeadline?: string | null;
  backendBaseUrl?: string; // e.g. http://10.249.74.1:8000
};

const DEFAULT_API_BASE = "http://10.249.74.1:8000";

export default function CardModal({
  visible,
  onClose,
  ticker,
  company,
  announcementDate,
  announcementHeadline,
  backendBaseUrl,
}: Props) {
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const API_BASE = backendBaseUrl || (global as any).API_BASE || DEFAULT_API_BASE;

  useEffect(() => {
    if (visible && ticker) {
      fetchMarket();
    } else {
      setData(null);
      setError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, ticker]);

  async function fetchMarket() {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const url = `${API_BASE}/market/summary/${encodeURIComponent(String(ticker).toUpperCase())}`;
      const res = await fetch(url);
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status} ${res.statusText} ${txt}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      console.warn("Failed to fetch market data for", ticker, err?.message ?? err);
      setError(String(err?.message ?? err));
    } finally {
      setLoading(false);
    }
  }

  function formatEodDate(csvFilename?: string, eodDate?: string | null) {
    // prefer eodDate from backend; else try parse filename like 2025-09-16
    const candidate = eodDate || csvFilename || announcementDate;
    if (!candidate) return "|EOD|";
    // if candidate is YYYY-MM-DD return formatted
    const m = String(candidate).match(/(20[0-9]{2})[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12][0-9]|3[01])/);
    if (m) {
      const yy = m[1].slice(2);
      const mm = parseInt(m[2], 10);
      const dd = m[3];
      const date = new Date(Number(m[1]), mm - 1, Number(dd));
      const mon = date.toLocaleString("en-US", { month: "short" });
      return `|EOD, ${dd}-${mon}-${yy}|`;
    }
    // fallback: print candidate directly
    return `|EOD, ${candidate}|`;
  }

  function colorForSignedValue(raw?: any) {
    const n = parseFloat(String(raw ?? ""));
    if (Number.isFinite(n)) {
      if (n > 0) return styles.valuePositive;
      if (n < 0) return styles.valueNegative;
    }
    return styles.valueNeutral;
  }

  function colorForRelVol(raw?: any) {
    const n = parseFloat(String(raw ?? ""));
    if (Number.isFinite(n)) {
      if (n > 1) return styles.valuePositive;
      if (n < 1) return styles.valueNegative;
    }
    return styles.valueNeutral;
  }

  function openChart() {
    // prefer chart_url returned in data, else tradingview by NSE-<TICKER>
    const chartUrl =
      data?.chart_url ??
      data?.tradingview ??
      (ticker ? `https://www.tradingview.com/symbols/NSE-${encodeURIComponent(String(ticker))}/` : null);

    if (!chartUrl) {
      Alert.alert("No chart URL", "Chart URL is not available for this ticker.");
      return;
    }
    Linking.openURL(chartUrl).catch(() => Alert.alert("Failed", "Unable to open chart URL"));
  }

  // display safe values:
  const priceDisplay = data?.price_display ?? data?.price ? `₹${Number(data.price).toFixed(2)}` : "—";
  const ch1 = data?.change_1d_display ?? data?.change_1d_pct ?? data?.change_1d ?? null;
  const ch7 = data?.change_1w_display ?? data?.change_1w_pct ?? data?.change_1w ?? null;

  return (
    <Modal visible={!!visible} animationType="slide" transparent={false} onRequestClose={onClose}>
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>
            {(ticker ?? "—").toString().toUpperCase()} • {company ?? "—"}
          </Text>
          <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
            <Text style={styles.closeText}>CLOSE</Text>
          </TouchableOpacity>
        </View>

        {/* TOP 30% area - intentionally left as neutral block (no image). */}
        <View style={styles.topBlock}>
          <Text style={styles.topTicker}>{(ticker ?? "—").toString().toUpperCase()}</Text>
          {/* We intentionally do not show the announcement image here */}
        </View>

        {/* BOTTOM 70% area - market + announcement info */}
        <View style={styles.content}>
          {/* Announcement meta */}
          <Text style={styles.sectionTitle}>
            Announcement: {announcementHeadline ?? "—"}
          </Text>
          <Text style={styles.metaSmall}>
            Date: {announcementDate ?? "—"}
          </Text>

          {/* Market Snapshot header */}
          <Text style={[styles.sectionTitle, { marginTop: 14 }]}>
            Market Snapshot: {formatEodDate(data?.csv_filename ?? data?.eod_date ?? announcementDate)}
          </Text>

          {/* Market fields */}
          {loading ? (
            <View style={{ padding: 18 }}>
              <ActivityIndicator size="small" />
              <Text style={{ marginTop: 8 }}>Loading market snapshot...</Text>
            </View>
          ) : error ? (
            <View style={{ padding: 18 }}>
              <Text style={{ color: "red" }}>{error}</Text>
            </View>
          ) : (
            <View style={{ paddingVertical: 8 }}>
              <View style={styles.row}>
                <Text style={styles.rowLabel}>Price:</Text>
                <View style={styles.rowRight}>
                  <Text style={styles.rowValueBold}>{priceDisplay}</Text>
                  <Text style={{ marginLeft: 12 }}>
                    <Text style={colorForSignedValue(ch1)}>{String(ch1 ?? "—")}{String(ch1)?.includes("%") ? "" : "%"}</Text>
                    <Text style={styles.grey}> {" (1D) | "}</Text>
                    <Text style={colorForSignedValue(ch7)}>{String(ch7 ?? "—")}{String(ch7)?.includes("%") ? "" : "%"}</Text>
                    <Text style={styles.grey}> {" (1W)"}</Text>
                  </Text>
                </View>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Volume (24 Hrs):</Text>
                <Text style={styles.rowValue}>{data?.volume_24h_display ?? data?.volume_24h_raw ?? "—"}</Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Mcap:</Text>
                <Text style={styles.rowValue}>{data?.mcap_display ?? "—"} {" | "} Rank: {data?.rank ?? "—"}</Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>VWAP:</Text>
                <Text style={styles.rowValue}>{data?.vwap_display ?? (data?.vwap != null ? Number(data.vwap).toFixed(2) : "—")}</Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>ATR(14D):</Text>
                <Text style={styles.rowValue}>{data?.atr14_display ?? (data?.atr14 != null ? `${Number(data.atr14).toFixed(2)}%` : "—")}</Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Relative Vol:</Text>
                <Text style={[styles.rowValue, colorForRelVol(data?.relative_vol)]}>
                  {data?.relative_vol != null ? Number(data.relative_vol).toFixed(2) : "—"}
                </Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Vol Change:</Text>
                <Text style={[styles.rowValue, colorForSignedValue(data?.vol_change)]}>
                  {data?.vol_change != null ? (String(data.vol_change).includes("%") ? data.vol_change : `${Number(data.vol_change).toFixed(2)}%`) : "—"}
                </Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Volatility:</Text>
                <Text style={[styles.rowValue, colorForRelVol(data?.volatility)]}>
                  {data?.volatility != null ? (String(data.volatility).includes("%") ? data.volatility : `${Number(data.volatility).toFixed(2)}%`) : "—"}
                </Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Beta:</Text>
                <Text style={styles.rowValue}>{data?.beta ?? "—"}</Text>
              </View>
            </View>
          )}

          <View style={{ alignItems: "center", marginTop: 16 }}>
            <TouchableOpacity style={styles.chartButton} onPress={openChart}>
              <Text style={styles.chartButtonText}>Open Chart</Text>
            </TouchableOpacity>
          </View>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const { width } = Dimensions.get("window");

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  header: {
    flexDirection: "row",
    paddingHorizontal: 16,
    paddingVertical: 12,
    alignItems: "center",
    justifyContent: "space-between",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#ddd",
  },
  title: { fontSize: 18, fontWeight: "700" },
  closeBtn: {
    backgroundColor: "#0a84ff",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  closeText: { color: "#fff", fontWeight: "700" },

  topBlock: {
    height: "30%",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f4f4f4",
  },
  topTicker: { fontSize: 28, color: "#999", fontWeight: "700" },

  content: {
    flex: 1,
    paddingHorizontal: 18,
    paddingTop: 12,
  },
  sectionTitle: { fontSize: 16, fontWeight: "700", marginBottom: 6 },
  metaSmall: { color: "#666", marginBottom: 8 },

  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#eee",
  },
  rowLabel: { width: "40%", fontWeight: "700" },
  rowValue: { width: "60%", textAlign: "right" },
  rowRight: { width: "60%", flexDirection: "row", alignItems: "center", justifyContent: "flex-end" },
  rowValueBold: { fontWeight: "800", fontSize: 16 },

  chartButton: {
    backgroundColor: "#000",
    paddingVertical: 14,
    paddingHorizontal: 30,
    borderRadius: 12,
    width: width * 0.7,
    alignItems: "center",
  },
  chartButtonText: { color: "#fff", fontWeight: "700" },

  valuePositive: { color: "#0A9D44", fontWeight: "700" }, // green
  valueNegative: { color: "#D93025", fontWeight: "700" }, // red
  valueNeutral: { color: "#333" },
  grey: { color: "#777" },
});