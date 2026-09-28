"""
memory_utils.py
Unified memory utility functions for Hindsight Cloud retention and recall.
Shared across load_memory.py, agent.py, and app.py to guarantee consistency.
"""

import logging
import os
import re
import sys
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from hindsight_client import Hindsight

logger = logging.getLogger(__name__)

CAUTION_PREFIX_REGEX = re.compile(
    r'^(?:[\U0001F000-\U0001FAFF\u2600-\u26FF\u2700-\u27BF⚠️]*\s*)?(?:proceed with caution[:\s-]*)+',
    re.IGNORECASE
)

def clean_warning_text(text: Optional[str]) -> str:
    """
    Strips '⚠️ Proceed with caution:' prefixes (with or without emoji, case-insensitive)
    so warning text never enters memory or pre-fills form fields as factual data.
    """
    if not text:
        return ""
    cleaned = CAUTION_PREFIX_REGEX.sub("", str(text)).strip()
    return cleaned

def format_incident_content(inc: Dict[str, Any]) -> str:
    """Format rich, semantically dense content for Hindsight memory extraction."""
    root_cause = clean_warning_text(inc.get("root_cause", ""))
    fix_applied = clean_warning_text(inc.get("fix_applied", ""))
    
    return (
        f"INCIDENT REPORT: {inc.get('incident_id')}\n"
        f"Team: {inc.get('team')}\n"
        f"Service: {inc.get('service')}\n"
        f"Severity: {inc.get('severity')}\n"
        f"Occurred At: {inc.get('timestamp')}\n"
        f"Error Signature: {inc.get('error_signature')}\n"
        f"Error Message: {inc.get('error_message')}\n"
        f"Stack Trace Snippet:\n{inc.get('stack_trace_snippet', 'N/A')}\n"
        f"Root Cause:\n{root_cause}\n"
        f"Fix Applied:\n{fix_applied}\n"
        f"Resolved By: {inc.get('resolved_by')}\n"
        f"Time to Resolve: {inc.get('time_to_resolve_minutes')} minutes\n"
        f"Estimated Revenue Impact: {inc.get('estimated_revenue_impact')}\n"
    )

def retain_incident(
    client: Hindsight,
    bank_id: str,
    incident_data: Dict[str, Any],
    update_mode: str = "replace"
) -> Tuple[bool, str, Optional[Exception]]:
    """
    Unified retention function used by both bulk loader and live resolution form.
    Guarantees:
      - Cleaned warning prefixes
      - String-only metadata values
      - Valid unique document_id
      - Valid timezone-aware timestamp
      - Full traceback on exception
    Returns:
      (success: bool, document_id: str, error: Optional[Exception])
    """
    # Generate unique document ID if not present
    doc_id = incident_data.get("incident_id")
    if not doc_id:
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_id = uuid.uuid4().hex[:6]
        doc_id = f"INC-{today_str}-{short_id}"

    # Clean root cause and fix
    cleaned_root_cause = clean_warning_text(incident_data.get("root_cause", ""))
    cleaned_fix = clean_warning_text(incident_data.get("fix_applied", ""))

    content = (
        f"INCIDENT REPORT: {doc_id}\n"
        f"Team: {incident_data.get('team', 'unknown')}\n"
        f"Service: {incident_data.get('service', 'unknown')}\n"
        f"Severity: {incident_data.get('severity', 'P2')}\n"
        f"Resolved At: {datetime.now(timezone.utc).isoformat()}\n"
        f"Error Signature: {incident_data.get('error_signature', str(incident_data.get('error_message', ''))[:80])}\n"
        f"Error Message: {incident_data.get('error_message', '')}\n"
        f"Stack Trace Snippet:\n{incident_data.get('stack_trace_snippet', 'N/A')}\n"
        f"Root Cause:\n{cleaned_root_cause}\n"
        f"Fix Applied:\n{cleaned_fix}\n"
        f"Resolved By: {incident_data.get('resolved_by', 'oncall-engineer')}\n"
        f"Time to Resolve: {incident_data.get('time_to_resolve_minutes', 30)} minutes\n"
        f"Estimated Revenue Impact: {incident_data.get('estimated_revenue_impact', '$0')}\n"
    )

    # Strictly string metadata values for Hindsight API compliance
    metadata = {
        "incident_id": str(doc_id),
        "team": str(incident_data.get("team", "unknown")),
        "service": str(incident_data.get("service", "unknown")),
        "severity": str(incident_data.get("severity", "P2")),
        "timestamp": str(incident_data.get("timestamp") or datetime.now(timezone.utc).isoformat()),
        "resolved_by": str(incident_data.get("resolved_by", "oncall-engineer")),
        "time_to_resolve_minutes": str(incident_data.get("time_to_resolve_minutes", 30)),
        "revenue_impact": str(incident_data.get("estimated_revenue_impact", "$0")),
        "error_signature": str(incident_data.get("error_signature", str(incident_data.get("error_message", ""))[:80]))
    }

    tags = [
        str(incident_data.get("team", "unknown")),
        str(incident_data.get("service", "unknown")),
        str(incident_data.get("severity", "p2")).lower(),
        "incident-memory",
        "resolved"
    ]

    # Timestamp as datetime object
    ts = None
    raw_ts = incident_data.get("timestamp")
    if raw_ts:
        try:
            ts = datetime.fromisoformat(str(raw_ts))
        except Exception:
            ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)

    try:
        logger.info(f"Retaining incident '{doc_id}' into Hindsight bank '{bank_id}'...")
        res = client.retain(
            bank_id=bank_id,
            content=content,
            document_id=doc_id,
            metadata=metadata,
            tags=tags,
            update_mode=update_mode,
            timestamp=ts,
            context=f"Payment Infrastructure Incident in {incident_data.get('team')} on {incident_data.get('service')}"
        )
        success = bool(getattr(res, "success", False))
        logger.info(f"Hindsight retention response for '{doc_id}': success={success}")
        return success, doc_id, None
    except Exception as e:
        logger.error(f"Hindsight retain exception for '{doc_id}': {e}")
        traceback.print_exc()
        return False, doc_id, e
