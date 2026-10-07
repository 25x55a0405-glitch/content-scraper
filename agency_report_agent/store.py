"""The workspace: everything Report Desk knows, as plain files on disk.

    <home>/agency.json
    <home>/clients/<client_id>/client.json
    <home>/clients/<client_id>/periods/<YYYY-MM>/sources/<source_id>.json
    <home>/clients/<client_id>/periods/<YYYY-MM>/uploads/<source_id>__<original name>
    <home>/reports/<client_id>/<YYYY-MM>/v<N>.html   (+ .pdf, .json)
    <home>/audit.jsonl
    <home>/runs.sqlite   (paused agent runs)

Plain files keep the data inspectable and easy to back up. Every write is
atomic (temp file + rename) and serialised by one lock, so concurrent web
requests can't interleave a half-written file.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .importers import PRECEDENCE, ImportResult
from .model import (METRICS, TOTAL, PeriodData, channel_label, compute_derived,
                    fill_totals, is_period, shift_period)

_LOCK = threading.RLock()
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")

DEFAULT_AGENCY = {
    "name": "Your Agency",
    "brand_color": "#1B4D3E",
    "logo": None,
    "voice": "Clear, warm and direct. Plain English for a busy business owner. Lead with what the "
             "numbers mean for their business, then what happens next. Never over-claim.",
    "reviewers": [],
    "currency": "GBP",
    "drafting": "template",          # "template" (free) or "claude"
    "model": "claude-opus-5-5",
    "sign_off": "",
}

CURRENCY_SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€", "AUD": "A$", "CAD": "C$", "NZD": "NZ$"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s[:60] or "client"


class StoreError(Exception):
    pass


class Store:
    def __init__(self, home: str | os.PathLike):
        self.home = Path(home).resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "clients").mkdir(exist_ok=True)
        (self.home / "reports").mkdir(exist_ok=True)

    # ------------------------------------------------------------------ io
    def _write_json(self, path: Path, obj: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _LOCK:
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, path)

    def _write_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _LOCK:
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.replace(tmp, path)

    @staticmethod
    def _read_json(path: Path, default=None):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return default

    def _safe(self, *parts: str) -> Path:
        p = self.home.joinpath(*parts).resolve()
        if self.home not in p.parents and p != self.home:
            raise StoreError("Path escapes the workspace.")
        return p

    @staticmethod
    def check_id(client_id: str) -> str:
        if not client_id or not _ID_RE.match(client_id):
            raise StoreError("Invalid client id.")
        return client_id

    @staticmethod
    def check_period(period: str) -> str:
        if not is_period(period):
            raise StoreError("Invalid period — use YYYY-MM.")
        return period

    # -------------------------------------------------------------- agency
    def agency(self) -> dict:
        a = dict(DEFAULT_AGENCY)
        a.update(self._read_json(self.home / "agency.json", {}) or {})
        return a

    def save_agency(self, updates: dict) -> dict:
        a = self.agency()
        a.update({k: v for k, v in updates.items() if k in DEFAULT_AGENCY})
        self._write_json(self.home / "agency.json", a)
        return a

    def currency_symbol(self) -> str:
        return CURRENCY_SYMBOLS.get(self.agency().get("currency", "GBP"), "£")

    def save_logo(self, data: bytes, mime: str = "") -> None:
        """Save the agency logo. The type is decided from the file's own bytes, never from the upload's label."""
        if len(data) > 1024 * 1024:
            raise StoreError("Logo must be under 1 MB.")
        head = data[:16]
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = "png"
        elif head.startswith(b"\xff\xd8\xff"):
            ext = "jpg"
        elif head[:4] == b"RIFF" and data[8:12] == b"WEBP":
            ext = "webp"
        elif re.search(rb"<svg[\s>]", data[:4096], re.I):
            ext = "svg"
            if re.search(rb"<\s*(script|foreignObject|iframe|embed|object|style\b[^>]*@import)|\bon\w+\s*=|"
                         rb"javascript:|data:text/html|<!ENTITY|<!DOCTYPE[^>]*\[|(?:xlink:)?href\s*=\s*[\"']\s*(?!#)",
                         data, re.I):
                raise StoreError("That SVG contains scripts or external links, which aren't allowed in a logo. "
                                 "Export a plain SVG, or use a PNG.")
        else:
            raise StoreError("That doesn't look like a PNG, JPEG, SVG or WebP image.")
        for old in self.home.glob("logo.*"):
            old.unlink()
        self._write_bytes(self.home / f"logo.{ext}", data)
        self.save_agency({"logo": f"logo.{ext}"})

    def logo_bytes(self) -> tuple[Optional[bytes], Optional[str]]:
        name = self.agency().get("logo")
        if not name:
            return None, None
        p = self._safe(name)
        if not p.exists():
            return None, None
        mime = {"png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml",
                "webp": "image/webp"}[p.suffix.lstrip(".")]
        return p.read_bytes(), mime

    # ------------------------------------------------------------- clients
    def list_clients(self, include_archived: bool = False) -> list[dict]:
        out = []
        for d in sorted((self.home / "clients").iterdir()) if (self.home / "clients").exists() else []:
            c = self._read_json(d / "client.json")
            if c and (include_archived or not c.get("archived")):
                out.append(c)
        return sorted(out, key=lambda c: c["name"].lower())

    def client(self, client_id: str) -> Optional[dict]:
        self.check_id(client_id)
        return self._read_json(self._safe("clients", client_id, "client.json"))

    def create_client(self, name: str, **fields) -> dict:
        name = (name or "").strip()
        if not name:
            raise StoreError("Client name is required.")
        if len(name) > 120:
            raise StoreError("Client name is too long.")
        base = slugify(name)
        cid, n = base, 2
        with _LOCK:
            while (self.home / "clients" / cid).exists():
                cid = f"{base}-{n}"
                n += 1
            c = {
                "id": cid,
                "name": name,
                "sector": "",
                "contact_name": "",
                "conversion_label": "enquiries",
                "monthly_target": None,
                "context": "",
                "archived": False,
                "created_at": now_iso(),
            }
            c.update(self._clean_client_fields(fields))
            self._write_json(self._safe("clients", cid, "client.json"), c)
        return c

    def update_client(self, client_id: str, **fields) -> dict:
        c = self.client(client_id)
        if not c:
            raise StoreError("No such client.")
        c.update(self._clean_client_fields(fields))
        if "name" in fields and fields["name"].strip():
            c["name"] = fields["name"].strip()[:120]
        self._write_json(self._safe("clients", client_id, "client.json"), c)
        return c

    @staticmethod
    def _clean_client_fields(fields: dict) -> dict:
        out = {}
        for k in ("sector", "contact_name", "context", "conversion_label"):
            if k in fields and fields[k] is not None:
                out[k] = str(fields[k]).strip()[:2000]
        if "conversion_label" in out and not out["conversion_label"]:
            out["conversion_label"] = "enquiries"
        if "monthly_target" in fields:
            t = fields["monthly_target"]
            if t in (None, ""):
                out["monthly_target"] = None
            else:
                try:
                    t = float(t)
                except (TypeError, ValueError):
                    raise StoreError("Monthly target must be a number.")
                if not math.isfinite(t) or t < 0 or t > 1e9:
                    raise StoreError("Monthly target must be a normal, non-negative number.")
                out["monthly_target"] = t
        if "archived" in fields:
            out["archived"] = bool(fields["archived"])
        return out

    # ------------------------------------------------------------- sources
    def _period_dir(self, client_id: str, period: str) -> Path:
        self.check_id(client_id)
        self.check_period(period)
        return self._safe("clients", client_id, "periods", period)

    def add_source(self, client_id: str, result: ImportResult, period: str,
                   filename: str = "", raw: bytes = b"", replace_same_type: bool = True) -> dict:
        """Store one import's figures for one period. Re-uploading the same source type replaces it."""
        if not self.client(client_id):
            raise StoreError("No such client.")
        values = result.periods.get(period)
        if not values:
            raise StoreError(f"That file has no figures for {period}.")
        pdir = self._period_dir(client_id, period)
        if replace_same_type and result.source_type != "generic":
            for old in self.sources(client_id, period):
                if old["type"] == result.source_type:
                    self.delete_source(client_id, period, old["id"])
        sid = f"{result.source_type}-{uuid.uuid4().hex[:8]}"
        rec = {
            "id": sid,
            "type": result.source_type,
            "filename": os.path.basename(filename or "")[:200],
            "imported_at": now_iso(),
            "values": values,
            "warnings": result.warnings,
            "rows_read": result.rows_read,
            "extras": result.extras,
        }
        self._write_json(pdir / "sources" / f"{sid}.json", rec)
        if raw:
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", rec["filename"] or "upload")[:120]
            self._write_bytes(pdir / "uploads" / f"{sid}__{safe_name}", raw)
        return rec

    def set_manual(self, client_id: str, period: str, values: dict[str, dict[str, float]]) -> dict:
        res = ImportResult(source_type="manual")
        for scope, row in values.items():
            for m, v in row.items():
                if m in METRICS and v is not None and math.isfinite(float(v)) and 0 <= float(v) <= 1e12:
                    res.put(period, scope, m, float(v))
        for old in self.sources(client_id, period):
            if old["type"] == "manual":
                self.delete_source(client_id, period, old["id"])
        if not res.periods:
            return {}
        return self.add_source(client_id, res, period, filename="Entered by hand", replace_same_type=False)

    def sources(self, client_id: str, period: str) -> list[dict]:
        d = self._period_dir(client_id, period) / "sources"
        if not d.exists():
            return []
        out = [self._read_json(p) for p in sorted(d.glob("*.json"))]
        return sorted([s for s in out if s], key=lambda s: s["imported_at"])

    def delete_source(self, client_id: str, period: str, source_id: str) -> None:
        if not re.match(r"^[a-z_]+-[0-9a-f]{8}$", source_id or ""):
            raise StoreError("Invalid source id.")
        pdir = self._period_dir(client_id, period)
        with _LOCK:
            (pdir / "sources" / f"{source_id}.json").unlink(missing_ok=True)
            for f in (pdir / "uploads").glob(f"{source_id}__*") if (pdir / "uploads").exists() else []:
                f.unlink()

    def periods_with_data(self, client_id: str) -> list[str]:
        d = self._safe("clients", self.check_id(client_id), "periods")
        if not d.exists():
            return []
        return sorted(p.name for p in d.iterdir() if is_period(p.name) and any((p / "sources").glob("*.json")))

    def period_data(self, client_id: str, period: str) -> tuple[PeriodData, list[str]]:
        """Merge every source for a month by precedence. Returns (data, conflict notes)."""
        sources = self.sources(client_id, period)
        pd = PeriodData(period=period)
        notes: list[str] = []
        candidates: dict[tuple[str, str], list[tuple[str, float]]] = {}
        for s in sources:
            for scope, row in s["values"].items():
                for m, v in row.items():
                    candidates.setdefault((scope, m), []).append((s["type"], v))
        for (scope, m), vals in candidates.items():
            order = PRECEDENCE.get(m, ["manual", "ga4", "generic"])
            vals.sort(key=lambda tv: order.index(tv[0]) if tv[0] in order else 99)
            winner_type, winner = vals[0]
            pd.set(scope, m, winner, origin=winner_type)
            for other_type, other in vals[1:]:
                if other_type == winner_type:
                    continue
                base = max(abs(winner), abs(other), 1e-9)
                if abs(winner - other) / base > 0.05 and abs(winner - other) >= 2:
                    notes.append(
                        f"{channel_label(scope)} {METRICS[m].label.lower()}: {SOURCE_NAMES.get(winner_type, winner_type)} "
                        f"says {winner:,.0f}, {SOURCE_NAMES.get(other_type, other_type)} says {other:,.0f}. "
                        f"Using {SOURCE_NAMES.get(winner_type, winner_type)}.")
        fill_totals(pd)
        compute_derived(pd)
        return pd, notes

    def extras(self, client_id: str, period: str) -> dict:
        out: dict = {}
        for s in self.sources(client_id, period):
            out.update(s.get("extras") or {})
        return out

    # ------------------------------------------------------------- reports
    def report_dir(self, client_id: str, period: str) -> Path:
        return self._safe("reports", self.check_id(client_id), self.check_period(period))

    def save_report(self, client_id: str, period: str, html: str, meta: dict,
                    pdf: Optional[bytes] = None) -> dict:
        d = self.report_dir(client_id, period)
        with _LOCK:
            existing = sorted(int(p.stem[1:]) for p in d.glob("v*.json")) if d.exists() else []
            n = (existing[-1] + 1) if existing else 1
            self._write_bytes(d / f"v{n}.html", html.encode("utf-8"))
            if pdf:
                self._write_bytes(d / f"v{n}.pdf", pdf)
            meta = dict(meta, version=n, saved_at=now_iso(), has_pdf=bool(pdf))
            self._write_json(d / f"v{n}.json", meta)
        return meta

    def reports(self, client_id: str, period: str) -> list[dict]:
        d = self.report_dir(client_id, period)
        if not d.exists():
            return []
        return [self._read_json(p) for p in sorted(d.glob("v*.json"), key=lambda p: int(p.stem[1:]))]

    def report_file(self, client_id: str, period: str, version: int, ext: str) -> Optional[Path]:
        if ext not in ("html", "pdf"):
            raise StoreError("Bad file type.")
        p = self.report_dir(client_id, period) / f"v{int(version)}.{ext}"
        return p if p.exists() else None

    # --------------------------------------------------------------- audit
    def audit(self, actor: str, action: str, client_id: str = "", period: str = "", detail: str = "") -> None:
        line = json.dumps({"at": now_iso(), "actor": actor or "system", "action": action,
                           "client": client_id, "period": period, "detail": detail[:2000]},
                          ensure_ascii=False)
        with _LOCK:
            with open(self.home / "audit.jsonl", "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def audit_log(self, limit: int = 300, client_id: str = "") -> list[dict]:
        p = self.home / "audit.jsonl"
        if not p.exists():
            return []
        lines = p.read_text(encoding="utf-8").splitlines()
        out = []
        for ln in reversed(lines):
            try:
                e = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if client_id and e.get("client") != client_id:
                continue
            out.append(e)
            if len(out) >= limit:
                break
        return out


SOURCE_NAMES = {
    "ga4": "GA4",
    "google_ads": "Google Ads",
    "search_console": "Search Console",
    "meta_ads": "Meta Ads",
    "generic": "Imported CSV",
    "manual": "Manual entry",
}


def previous_periods(period: str) -> tuple[str, str]:
    return shift_period(period, -1), shift_period(period, -12)
