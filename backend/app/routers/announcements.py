# ~/marketnews-app/backend/app/routers/announcements.py
import os
import re
import csv
from typing import Dict, Any, List
from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/announcements", tags=["announcements"])

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ANNOUNCEMENTS_UPLOADS_DIR = os.path.join(PROJECT_ROOT, "announcements", "uploads")

FNAME_DATE_RE = re.compile(r"20[0-9]{2}[-_][01][0-9][-_][0-3][0-9]")

def _extract_date_from_filename(fname: str) -> str:
    m = FNAME_DATE_RE.search(fname)
    return m.group(0) if m else "no-date"

def _load_symbol_map() -> Dict[str, Dict[str, str]]:
    """
    Load mapping from Symbol → Description from latest CSV
    """
    mapping = {}
    try:
        csv_files = sorted(
            [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")],
            reverse=True,
        )
        if not csv_files:
            return mapping
        latest_csv = os.path.join(DATA_DIR, csv_files[0])
        with open(latest_csv, newline="", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                sym = row.get("Symbol") or row.get("SYMBOL")
                desc = row.get("Description") or row.get("Company") or row.get("Name")
                if sym:
                    mapping[sym.strip().upper()] = {
                        "symbol": sym.strip().upper(),
                        "company": desc.strip() if desc else sym.strip().upper(),
                    }
    except Exception as e:
        print(f"Failed to load CSV symbol map: {e}")
    return mapping

@router.get("/list-enriched")
def announcements_list_enriched(request: Request) -> Dict[str, Any]:
    """
    List uploaded announcement files enriched with company name (from CSV).
    """
    try:
        symbol_map = _load_symbol_map()
        entries: List[Dict[str, Any]] = []

        for fname in sorted(os.listdir(ANNOUNCEMENTS_UPLOADS_DIR)):
            fpath = os.path.join(ANNOUNCEMENTS_UPLOADS_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            sym_guess = os.path.splitext(fname)[0].upper()
            company_info = symbol_map.get(sym_guess, {"symbol": sym_guess, "company": sym_guess})
            base = str(request.base_url).rstrip("/")
            download_url = f"{base}/announcements/file/{fname}"

            entries.append(
                {
                    "filename": fname,
                    "symbol": company_info["symbol"],
                    "company": company_info["company"],
                    "download_url": download_url,
                    "filename_date": _extract_date_from_filename(fname),
                }
            )

        return {"count": len(entries), "files": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))