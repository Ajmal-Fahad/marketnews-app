# ~/marketnews-app/backend/app/routers/announcements_enriched.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import os
import csv
from datetime import datetime, timezone

router = APIRouter(prefix="/announcements", tags=["announcements"])

# folders (adjust if your project uses different paths)
ANNOUNCE_DIR = os.path.expanduser("~/marketnews-app/backend/announcements/uploads")
DATA_DIR = os.path.expanduser("~/marketnews-app/backend/data")

def find_latest_csv_path() -> Optional[str]:
    """Return the most recent eod_YYYY-MM-DD.csv (or latest_eod.csv) if present."""
    candidates = []
    if os.path.isdir(DATA_DIR):
        for fname in os.listdir(DATA_DIR):
            if fname.lower().endswith(".csv") and ("eod" in fname.lower() or "latest" in fname.lower()):
                candidates.append(os.path.join(DATA_DIR, fname))
    if not candidates:
        return None
    # prefer file with YYYY-MM-DD in name and newest mtime as tie-breaker
    def score(path: str):
        base = os.path.basename(path)
        date_part = None
        import re
        m = re.search(r"20[0-9]{2}[-_][01][0-9][-_][0-3][0-9]", base)
        if m:
            try:
                date_part = datetime.fromisoformat(m.group(0).replace("_", "-"))
                # score by date timestamp
                return (int(date_part.timestamp()), os.path.getmtime(path))
            except Exception:
                pass
        # fallback: use mtime only
        return (0, os.path.getmtime(path))
    candidates.sort(key=score, reverse=True)
    return candidates[0]

def build_symbol_to_company_map() -> Dict[str, str]:
    """Read latest CSV and return map: SYMBOL -> Company full name (case-insensitive keys)."""
    csv_path = find_latest_csv_path()
    mapping: Dict[str, str] = {}
    if not csv_path or not os.path.exists(csv_path):
        return mapping
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            # find best guess columns for symbol and company
            headers = [h.strip() for h in reader.fieldnames or []]
            symbol_keys = [h for h in headers if h.lower() in ("symbol","ticker","securitycode","scrip","symbol ")]
            comp_keys = [h for h in headers if h.lower() in ("description","company","companyname","nameofthecompany","name")]
            # fallback to first two headers
            if not symbol_keys and len(headers) >= 1:
                symbol_keys = [headers[0]]
            if not comp_keys and len(headers) >= 2:
                comp_keys = [headers[1]]
            for r in reader:
                sym = None
                comp = None
                for k in symbol_keys:
                    if k in r and r[k] not in (None, ""):
                        sym = r[k].strip()
                        break
                for k in comp_keys:
                    if k in r and r[k] not in (None, ""):
                        comp = r[k].strip()
                        break
                if sym:
                    mapping[sym.upper()] = comp or sym
    except Exception:
        # if anything fails, return empty mapping
        return {}
    return mapping

@router.get("/list-enriched")
def list_announcements_enriched() -> Dict[str, Any]:
    """
    Return announcement files with metadata enriched by CSV lookup:
    - filename
    - ticker_guess (from filename, uppercase)
    - company (lookup from latest CSV; fallback to ticker)
    - download_url (relative)
    - size_bytes
    - mtime_iso
    """
    if not os.path.isdir(ANNOUNCE_DIR):
        raise HTTPException(status_code=500, detail=f"Announcements folder not found at {ANNOUNCE_DIR}")

    mapping = build_symbol_to_company_map()

    files = []
    for fname in sorted(os.listdir(ANNOUNCE_DIR)):
        # consider only images + pdf
        if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".avif", ".pdf")):
            continue
        full = os.path.join(ANNOUNCE_DIR, fname)
        try:
            stat = os.stat(full)
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            # attempt ticker guess from filename (strip extension and non-alphanum from edges)
            base = os.path.splitext(fname)[0]
            ticker_guess = base.strip().upper()
            # try to isolate token by splitting on non-alphanum (common filenames like RELIANCE_...)
            import re
            m = re.match(r"^([A-Z0-9\.\-]{1,20})", ticker_guess)
            if m:
                ticker_guess = m.group(1)
            company = mapping.get(ticker_guess) or mapping.get(ticker_guess.replace(".E1","")) or None
            if not company:
                # fallback: try to match by description column (case-insensitive partial match)
                for k_sym, k_comp in mapping.items():
                    if k_sym.upper() in ticker_guess or (k_comp and k_comp.upper() in ticker_guess):
                        company = mapping[k_sym]
                        break
            if not company:
                company = ticker_guess  # last fallback
            files.append({
                "filename": fname,
                "ticker_guess": ticker_guess,
                "company": company,
                "download_url": f"/announcements/file/{fname}",
                "size_bytes": stat.st_size,
                "mtime_iso": mtime.isoformat(),
            })
        except Exception as e:
            # skip unreadable file
            continue

    # Optionally: sort by mtime desc
    files.sort(key=lambda x: x.get("mtime_iso", ""), reverse=True)

    return {"count": len(files), "files": files}