"""Append-Only Dual Knowledge Ledger Service."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, List, Optional
from server.config import settings
from server.models.canonical import ConfidenceLevel, SourceType
from server.models.ledger import CollegeKnowledgeEntry, EnrichmentRun, LedgerEvent


class KnowledgeLedgerService:
    """Manages concurrent, atomic writes to human-readable Markdown and machine JSONL ledgers."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self.md_path: Path = settings.LEDGER_MD_PATH
        self.jsonl_path: Path = settings.LEDGER_JSONL_PATH
        self._init_ledgers()

    def _init_ledgers(self) -> None:
        """Ensure ledger files and headers exist."""
        self.md_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.md_path.exists():
            header = (
                "# College Knowledge Ledger (Audit Trail)\n\n"
                "This document is an append-only, human-readable audit log tracking all data provenance mutations, "
                "Scorecard ingests, and Gemini AI enrichments committed to the College Portfolio system.\n\n"
                "| Timestamp (UTC) | College | Field Path | Action / Change | Source Authority | Confidence |\n"
                "|---|---|---|---|---|---|\n"
            )
            self.md_path.write_text(header, encoding="utf-8")

        if not self.jsonl_path.exists():
            self.jsonl_path.touch()

    async def record_events(
        self,
        events: List[LedgerEvent],
        run_metadata: Optional[EnrichmentRun] = None,
    ) -> None:
        """Atomically append events to both JSONL and Markdown ledgers."""
        if not events and not run_metadata:
            return

        async with self._lock:
            # 1. Append to JSONL
            with open(self.jsonl_path, "a", encoding="utf-8") as jf:
                for evt in events:
                    jf.write(json.dumps(evt.model_dump()) + "\n")

            # 2. Append to Markdown
            with open(self.md_path, "a", encoding="utf-8") as mf:
                if run_metadata:
                    mf.write(
                        f"\n## College: {run_metadata.college_name} ({run_metadata.college_id})\n"
                        f"- **Timestamp**: {run_metadata.created_at}\n"
                        f"- **Enrichment**: {run_metadata.model} (run {run_metadata.run_id})\n"
                        f"- **Status**: {run_metadata.status}\n"
                        f"- **Fields Updated**: {', '.join(run_metadata.fields_updated) if run_metadata.fields_updated else 'None'}\n\n"
                    )

                for evt in events:
                    old_str = f"`{evt.old_value}`" if evt.old_value is not None else "*None*"
                    new_str = f"`{evt.new_value}`" if not isinstance(evt.new_value, (list, dict)) else f"`{type(evt.new_value).__name__} ({len(evt.new_value)} items)`"
                    change_desc = f"{old_str} &rarr; {new_str}"
                    source_desc = f"{evt.source_type.value} ({', '.join(evt.source_ids) if evt.source_ids else 'system'})"
                    mf.write(
                        f"| {evt.committed_at} | {evt.college_name} (`{evt.college_id}`) | `{evt.field_path}` | {change_desc} | {source_desc} | {evt.confidence.value} |\n"
                    )

    async def get_events_for_college(self, college_id: str) -> List[LedgerEvent]:
        """Read all ledger events associated with a specific college ID."""
        events: List[LedgerEvent] = []
        if not self.jsonl_path.exists():
            return events

        async with self._lock:
            with open(self.jsonl_path, "r", encoding="utf-8") as jf:
                for line in jf:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if str(data.get("college_id")) == str(college_id):
                            events.append(LedgerEvent(**data))
                    except Exception:
                        continue
        return events

    async def get_all_events(self, limit: int = 100) -> List[LedgerEvent]:
        """Read the most recent ledger events across all colleges."""
        events: List[LedgerEvent] = []
        if not self.jsonl_path.exists():
            return events

        async with self._lock:
            with open(self.jsonl_path, "r", encoding="utf-8") as jf:
                for line in jf:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        events.append(LedgerEvent(**data))
                    except Exception:
                        continue
        return events[-limit:]

    async def export_knowledge_summary(self) -> List[CollegeKnowledgeEntry]:
        """Generate a summary index of all enriched colleges and event counts."""
        college_map = {}
        if not self.jsonl_path.exists():
            return []

        async with self._lock:
            with open(self.jsonl_path, "r", encoding="utf-8") as jf:
                for line in jf:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        cid = str(data.get("college_id"))
                        cname = data.get("college_name", "Unknown")
                        evt = LedgerEvent(**data)
                        if cid not in college_map:
                            college_map[cid] = {
                                "college_id": cid,
                                "college_name": cname,
                                "last_updated": evt.committed_at,
                                "events": [],
                            }
                        college_map[cid]["last_updated"] = evt.committed_at
                        college_map[cid]["events"].append(evt)
                    except Exception:
                        continue

        results = []
        for cid, info in college_map.items():
            results.append(
                CollegeKnowledgeEntry(
                    college_id=info["college_id"],
                    college_name=info["college_name"],
                    last_updated=info["last_updated"],
                    event_count=len(info["events"]),
                    recent_events=info["events"][-10:],
                )
            )
        return results


ledger_service = KnowledgeLedgerService()
