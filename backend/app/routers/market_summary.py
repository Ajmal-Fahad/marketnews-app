# ~/marketnews-app/backend/app/routers/market_summary.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import os
import csv
import re
from datetime import datetime

router = APIRouter(prefix="/market", tags=["market"])

DATA_DIR = os.path.expanduser("~/marketnews-app/backend/data")

def find_latest_csv() -> Optional[str]:
    """Find the most recent EOD CSV file in DATA_DIR.
    Preference order:
      - files containing a YYYY-MM-DD date in filename -> pick max date
      - otherwise fallback to most-recent mtime CSV
    Returns full path or None.
    """
    if not os.path.isdir(DATA_DIR):
        return None

    files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")]
    if not files:
        return None

    date_files: List[tuple] = []
    date_re = re.compile(r"20[0-9]{2}[-_][01][0-9][-_][0-3][0-9]")
    for f in files:
        m = date_re.search(os.path.basename(f))
        if m:
            try:
                s = m.group(0).replace("_", "-")
                dt = datetime.strptime(s, "%Y-%m-%d")
                date_files.append((dt, f))
            except Exception:
                pass

    if date_files:
        # pick file with max date found in filename
        date_files.sort(key=lambda x: x[0], reverse=True)
        return date_files[0][1]

    # fallback: most recent modification time
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files[0]

def safe_keys(row: Dict[str, str]) -> List[str]:
    return [k for k in row.keys()]

def pick(row: Dict[str, str], candidates):
    """Pick first matching column (case-insensitive name) from csv row dict"""
    for c in candidates:
        for k in row.keys():
            if k is None: 
                continue
            if k.strip().lower() == c.lower():
                v = row.get(k)
                return v.strip() if isinstance(v, str) else v
    return None

def to_float(s: Optional[str]) -> Optional[float]:
    if s is None or s == "":
        return None
    try:
        cleaned = str(s).replace(",", "").replace("%", "").replace("₹", "").replace("Cr", "").replace("L", "").strip()
        return float(cleaned)
    except Exception:
        return None

def format_rupee_cr(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return None
    # 1 Crore = 1e7
    if abs(v) >= 1e7:
        return f"₹{v/1e7:.2f} Cr"
    if abs(v) >= 1e5:
        return f"₹{v/1e5:.2f} L"
    return f"₹{v:,.2f}"

def format_pct(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    try:
        return f"{value:.2f}%"
    except Exception:
        return None

def normalize_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(s)).strip().upper()

@router.get("/summary/{ticker}")
def market_summary(ticker: str) -> Dict[str, Any]:
    """
    Return a compact market summary for the given ticker using latest CSV in data/.
    Matching is flexible: exact symbol, symbol contains token, or description contains company text.
    """
    csv_path = find_latest_csv()
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=500, detail=f"EOD CSV not found in {DATA_DIR}")

    rows = []
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                rows.append(r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed reading CSV: {e}")

    t_raw = (ticker or "").strip()
    if not t_raw:
        raise HTTPException(status_code=400, detail="Empty ticker")

    t = t_raw.upper()
    t_norm = normalize_text(t_raw)

    match = None

    # first pass: exact symbol match against likely symbol-like headers
    symbol_headers = ("symbol", "ticker", "securitycode", "security code", "scrip")
    desc_headers = ("description", "company", "companyname", "nameofthecompany", "name", "description of announcement")

    # helper to get header-insensitive value
    def header_get(row, header_candidates):
        for k in row.keys():
            if k is None:
                continue
            if k.strip().lower() in [h.lower() for h in header_candidates]:
                return row.get(k)
        return None

    # 1) exact symbol match (case-insensitive)
    for r in rows:
        sym = header_get(r, symbol_headers)
        if sym and isinstance(sym, str) and sym.strip().upper() == t:
            match = r
            break

    # 2) normalized symbol comparison (remove punctuation) exact
    if not match:
        for r in rows:
            sym = header_get(r, symbol_headers)
            if sym:
                if normalize_text(sym) == t_norm:
                    match = r
                    break

    # 3) symbol contains requested token (e.g. t=INFOSYS might match sym INFY if token present) 
    if not match:
        for r in rows:
            sym = header_get(r, symbol_headers)
            if sym:
                if t in str(sym).upper() or t_norm in normalize_text(sym):
                    match = r
                    break

    # 4) fallback: match by description/company containing the requested text (partial, case-insensitive)
    if not match:
        lowered_t = t_raw.lower()
        for r in rows:
            comp = header_get(r, desc_headers)
            if comp and isinstance(comp, str) and lowered_t in comp.lower():
                match = r
                break

    # 5) last resort: partial token match across description words (split company name and check tokens)
    if not match:
        t_tokens = re.split(r"\s+|[^A-Za-z0-9]+", t_raw)
        t_tokens = [tok for tok in t_tokens if tok]
        if t_tokens:
            for r in rows:
                comp = header_get(r, desc_headers)
                if comp and isinstance(comp, str):
                    comp_low = comp.lower()
                    for tok in t_tokens:
                        if tok.lower() and tok.lower() in comp_low:
                            match = r
                            break
                if match:
                    break

    if not match:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found in CSV at {os.path.basename(csv_path)}")

    # Now extract fields using header names present in that CSV row
    # Use the visible header text from CSV and common variants
    price_raw = pick(match, ["Price", "price", "Close", "ClosePrice", "LastPrice"])
    price = to_float(price_raw)

    change_1d_raw = pick(match, ["Price Change % 1 day", "Price Change % 1 day ", "Price Change % 1 day", "Price Change % 1 day", "Price Change % 1 day"])
    change_1d = to_float(change_1d_raw)

    change_1w_raw = pick(match, ["Price Change % 1 week", "Price Change % 1 week "])
    change_1w = to_float(change_1w_raw)

    volume_raw = pick(match, ["Price * Volume (Turnover) 1 day", "Price * Volume (Turnover) 1 day ", "Volume", "Volume(24H)", "TradedQty", "TOTTRDQTY"])
    try:
        volume_num = None
        if volume_raw not in (None, ""):
            volume_num = float(str(volume_raw).replace(",", "").strip())
    except Exception:
        volume_num = None

    mcap_raw = pick(match, ["Market capitalization", "Mcap", "MarketCap", "marketcap"])
    mcap_num = to_float(mcap_raw)

    rank_raw = pick(match, ["Rank", "rank"])
    try:
        rank_num = int(str(rank_raw).strip()) if rank_raw and str(rank_raw).strip().isdigit() else None
    except Exception:
        rank_num = None

    vwap_raw = pick(match, ["Volume Weighted Average Price 1 day", "VWAP", "vwap", "Volume Weighted Average Price"])
    vwap = to_float(vwap_raw)

    atr14_raw = pick(match, ["Average True Range % (14) 1 day", "Average True Range % (14) 1 day ", "ATR14", "ATR_14", "ATR(14)"])
    atr14 = to_float(atr14_raw)

    relvol_raw = pick(match, ["Relative Volume 1 day", "RelVol", "relative_volume", "relative vol", "RelativeVolume", "Relative Vol"])
    relvol = to_float(relvol_raw)

    vol_change_raw = pick(match, ["Volume Change % 1 day", "Volume Change % 1 day ", "Volume Change % 1 day", "Volume Change % 1 day"])
    vol_change = to_float(vol_change_raw)

    volatility_raw = pick(match, ["Volatility 1 day", "Volatility 1 day ", "Volatility", "volatility"])
    volatility = to_float(volatility_raw)

    beta_raw = pick(match, ["Beta", "beta"])
    beta = to_float(beta_raw) if beta_raw else None

    # company/description
    company = pick(match, ["Description", "description", "Company", "company", "CompanyName", "NameOfTheCompany"]) or None

    # Try to parse an EOD date from filename (if present) otherwise None
    filename = os.path.basename(csv_path)
    date_match = re.search(r"(20[0-9]{2})[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12][0-9]|3[01])", filename)
    eod_date = None
    if date_match:
        try:
            eod_date = datetime.strptime(date_match.group(0), "%Y-%m-%d").date().isoformat()
        except Exception:
            try:
                eod_date = datetime.strptime(date_match.group(0).replace("_", "-"), "%Y-%m-%d").date().isoformat()
            except Exception:
                eod_date = None

    resp = {
        "ticker": (pick(match, ["Symbol", "symbol", "Ticker", "ticker"]) or ticker).strip().upper(),
        "company": company,
        "csv_filename": os.path.basename(csv_path),
        "eod_date": eod_date,
        "price": price,
        "price_display": format_rupee_cr(price) if price is not None else None,
        "change_1d_pct": change_1d,
        "change_1d_display": format_pct(change_1d),
        "change_1w_pct": change_1w,
        "change_1w_display": format_pct(change_1w),
        "volume_24h_raw": volume_raw,
        "volume_24h": volume_num,
        "volume_24h_display": format_rupee_cr(volume_num) if volume_num is not None else None,
        "mcap_raw": mcap_raw,
        "mcap": mcap_num,
        "mcap_display": format_rupee_cr(mcap_num),
        "rank": rank_num,
        "vwap": vwap,
        "vwap_display": f"{vwap:.2f}" if vwap is not None else None,
        "atr14": atr14,
        "atr14_display": f"{atr14:.2f}%" if atr14 is not None else None,
        "relative_vol": relvol,
        "vol_change": vol_change,
        "volatility": volatility,
        "beta": beta,
    }

    return resp