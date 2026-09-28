"""
agent.py
Autonomous Cross-Team Incident Memory Agent for Payment Infrastructure.
Combines Hindsight Cloud memory with Groq LLM (openai/gpt-oss-120b with fallback).
"""

import json
import logging
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight
from memory_utils import clean_warning_text, retain_incident

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODELS = ["qwen/qwen3-32b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]

DIAGNOSIS_PROMPT_TEMPLATE = """You are an elite Staff SRE & Principal Incident Responder for a tier-1 payment infrastructure system.
Your mission is to analyze incoming production incidents by leveraging Cross-Team Incident Memory from Hindsight.

INCOMING INCIDENT ALERT:
- Team: {team}
- Service: {service}
- Severity: {severity}
- Error Signature: {error_signature}
- Error Message: {error_message}
- Stack Trace:
{stack_trace_snippet}

RECALLED PAST INCIDENTS FROM ORG MEMORY (Hindsight Cloud):
{memory_context}

ANALYSIS INSTRUCTIONS:
1. Examine the error symptoms and compare them carefully with the recalled incidents.
2. Determine if any recalled incident is a TRUE root-cause match:
   - "same_team": Matched incident belongs to the SAME team ({team}) and shares the same root failure mechanism.
   - "cross_team": Matched incident belongs to a DIFFERENT team, transferring vital cross-team institutional knowledge! For example, when downstream socket read timeouts or connection starvation on fraud-detection-service exhibit the same connection pool starvation pattern solved by auth-service (e.g. INC-2026-0314 with Jedis/Redis pool limits), classify as "cross_team" with high confidence (>= 80%).
   - "none": No matching historical incident, OR a true "False Friend" where surface text/HTTP status codes match (e.g. HTTP 504 Gateway Timeout), but the stack trace explicitly shows an unrelated root cause (e.g. DNS NXDOMAIN UnknownHostException vs gateway pool exhaustion).
3. If this is a FALSE FRIEND or low-confidence match:
   - Set "match_type" to "none".
   - Set "caution_warning" to: "⚠️ Proceed with caution: Surface symptoms resemble a past incident, but root causes diverge. Do NOT apply past fixes blindly."
   - Keep "confidence" strictly below 70.
   - Do NOT prepend "⚠️ Proceed with caution:" to "root_cause" or "fix_applied". Keep caution warnings strictly in "caution_warning".
4. If this is a VALID MATCH ("same_team" or "cross_team"):
   - Set "confidence" between 80 and 96 based on match strength.
   - Set "caution_warning" to null.
   - "matched_incident_id": The exact Incident ID matched (e.g. INC-2026-0314).
   - "matched_team": The team that solved it originally.
   - "root_cause": Clear, technical explanation of the actual root cause.
   - "fix_applied": Concrete technical fix with PR numbers, code/configuration changes, and exact parameter names.
   - "time_to_fix_past": How long it took last time (e.g. "85 mins").
   - "time_to_fix_estimated": Expected resolution time with memory (e.g. "10 mins").
   - "revenue_protected": Estimated revenue preserved by rapid cross-team resolution.
   - "specifics": List of 3-5 factual specifics ONLY memory could know (e.g., exact PR #, configuration parameters, engineer names, table names).

5. Return ONLY a valid JSON object matching this schema:
{{
  "match_type": "same_team" | "cross_team" | "none",
  "matched_incident_id": string or null,
  "matched_team": string or null,
  "confidence": number (0-100),
  "caution_warning": string or null,
  "root_cause": string,
  "fix_applied": string,
  "time_to_fix_past": string,
  "time_to_fix_estimated": string,
  "revenue_protected": string,
  "specifics": [string]
}}
"""

GENERIC_BASELINE_PROMPT = """You are a standard LLM without access to internal organization memory.
Analyze this production alert and provide standard, generic troubleshooting recommendations:

- Team: {team}
- Service: {service}
- Severity: {severity}
- Error Signature: {error_signature}
- Error Message: {error_message}
- Stack Trace:
{stack_trace_snippet}

Return ONLY a valid JSON object:
{{
  "root_cause": "Hypothetical generic textbook root cause",
  "fix_applied": "Generic standard best-practice suggestions (check logs, review recent commits, restart pod)",
  "confidence": 40,
  "time_to_fix_estimated": "60-90 mins",
  "specifics": []
}}
"""

class CrossTeamIncidentAgent:
    def __init__(self, bank_id: Optional[str] = None):
        load_dotenv()
        self.hindsight_api_key = os.getenv("HINDSIGHT_API_KEY")
        self.hindsight_base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.bank_id = bank_id or os.getenv("HINDSIGHT_BANK_ID", "payment-infrastructure-incidents")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        if not self.hindsight_api_key:
            raise ValueError("HINDSIGHT_API_KEY is missing from environment.")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is missing from environment.")

        self.hindsight = Hindsight(base_url=self.hindsight_base_url, api_key=self.hindsight_api_key)
        self.groq = Groq(api_key=self.groq_api_key)

    def _call_groq_json(self, prompt: str) -> Dict[str, Any]:
        """Execute Groq chat completion with model fallback and strict JSON parsing."""
        models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS
        last_error = None

        for model in models_to_try:
            try:
                logger.info(f"Calling Groq LLM model: {model}")
                response = self.groq.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a specialized site reliability engineering AI. Return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                raw_content = response.choices[0].message.content or "{}"
                parsed = json.loads(raw_content)
                return parsed
            except Exception as e:
                logger.warning(f"Groq invocation failed on {model}: {e}")
                last_error = e
                time.sleep(0.5)

        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")

    def recall_memories(self, alert_data: Dict[str, Any], max_tokens: int = 1500) -> List[Dict[str, Any]]:
        """
        Recall relevant incident memories from Hindsight Cloud bank.
        Returns a structured list of memory items with metadata and similarity scores.
        """
        team = alert_data.get("team", "")
        service = alert_data.get("service", "")
        error_msg = alert_data.get("error_message", "")
        error_sig = alert_data.get("error_signature", "")
        stack = alert_data.get("stack_trace_snippet", "")

        # Pure symptom-driven semantic query matching error signature, message, and stack trace
        # Do not bias the search by the reporting team/service so true cross-team memories are surfaced!
        query = f"{error_sig} {error_msg} {stack[:300]}".strip()

        try:
            logger.info(f"Recalling memories from Hindsight bank '{self.bank_id}'...")
            recall_resp = self.hindsight.recall(
                bank_id=self.bank_id,
                query=query,
                max_tokens=max_tokens,
                budget="mid",
                include_chunks=True
            )

            results = getattr(recall_resp, "results", []) or []
            parsed_memories = []

            for r in results:
                # Handle model fields safely
                r_meta = getattr(r, "metadata", {}) or {}
                if hasattr(r_meta, "model_dump"):
                    r_meta = r_meta.model_dump()
                elif not isinstance(r_meta, dict):
                    r_meta = dict(r_meta)

                # Extract score safely
                scores = getattr(r, "scores", {}) or {}
                if hasattr(scores, "model_dump"):
                    scores = scores.model_dump()
                elif not isinstance(scores, dict):
                    try:
                        scores = dict(scores)
                    except Exception:
                        scores = {}

                # Calculate primary similarity metric
                score_val = 0.0
                if isinstance(scores, dict):
                    for k in ["relevance", "similarity", "cosine", "semantic"]:
                        if k in scores and isinstance(scores[k], (int, float)):
                            score_val = float(scores[k])
                            break
                    if score_val == 0.0 and scores:
                        first_val = list(scores.values())[0]
                        if isinstance(first_val, (int, float)):
                            score_val = float(first_val)

                memory_item = {
                    "document_id": getattr(r, "document_id", "") or r_meta.get("incident_id", ""),
                    "incident_id": r_meta.get("incident_id", getattr(r, "document_id", "")),
                    "team": r_meta.get("team", "unknown"),
                    "service": r_meta.get("service", "unknown"),
                    "severity": r_meta.get("severity", "P2"),
                    "date": r_meta.get("timestamp", getattr(r, "occurred_start", "N/A")),
                    "resolved_by": r_meta.get("resolved_by", "oncall"),
                    "time_to_resolve_minutes": r_meta.get("time_to_resolve_minutes", "30"),
                    "revenue_impact": r_meta.get("revenue_impact", "$0"),
                    "text": getattr(r, "text", ""),
                    "score": round(score_val * 100, 1) if score_val <= 1.0 and score_val > 0 else round(score_val, 1),
                    "metadata": r_meta
                }
                parsed_memories.append(memory_item)

            logger.info(f"Recalled {len(parsed_memories)} memories from Hindsight.")
            return parsed_memories

        except Exception as e:
            logger.error(f"Error querying Hindsight memory: {e}")
            traceback.print_exc()
            return []

    def diagnose_with_memory(
        self,
        alert_data: Dict[str, Any],
        recalled_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize incident diagnosis and remediation using recalled Hindsight memories.
        """
        if recalled_memories:
            context_blocks = []
            for i, m in enumerate(recalled_memories[:6], 1):
                context_blocks.append(
                    f"--- RECALLED MEMORY #{i} [Doc ID: {m.get('incident_id')}] ---\n"
                    f"Team: {m.get('team')} | Service: {m.get('service')} | Severity: {m.get('severity')}\n"
                    f"Occurred: {m.get('date')} | Resolved By: {m.get('resolved_by')}\n"
                    f"Memory Text:\n{m.get('text')}\n"
                )
            memory_context = "\n".join(context_blocks)
        else:
            memory_context = "No previous incidents recalled from memory bank."

        prompt = DIAGNOSIS_PROMPT_TEMPLATE.format(
            team=alert_data.get("team", "unknown"),
            service=alert_data.get("service", "unknown"),
            severity=alert_data.get("severity", "P2"),
            error_signature=alert_data.get("error_signature", ""),
            error_message=alert_data.get("error_message", ""),
            stack_trace_snippet=alert_data.get("stack_trace_snippet", "N/A"),
            memory_context=memory_context
        )

        res = self._call_groq_json(prompt)

        # Enforce clean data: strip any caution prefixes if LLM accidentally included them
        res["root_cause"] = clean_warning_text(res.get("root_cause", ""))
        res["fix_applied"] = clean_warning_text(res.get("fix_applied", ""))

        # Ensure confidence is integer
        try:
            res["confidence"] = int(res.get("confidence", 50))
        except Exception:
            res["confidence"] = 50

        # Validate match_type
        if res.get("match_type") not in ["same_team", "cross_team", "none"]:
            res["match_type"] = "none"

        return res

    def diagnose_without_memory(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Baseline analysis without Hindsight memory (Generic LLM behavior).
        """
        prompt = GENERIC_BASELINE_PROMPT.format(
            team=alert_data.get("team", "unknown"),
            service=alert_data.get("service", "unknown"),
            severity=alert_data.get("severity", "P2"),
            error_signature=alert_data.get("error_signature", ""),
            error_message=alert_data.get("error_message", ""),
            stack_trace_snippet=alert_data.get("stack_trace_snippet", "N/A")
        )
        res = self._call_groq_json(prompt)
        res["root_cause"] = clean_warning_text(res.get("root_cause", "Generic diagnostic hypothesis."))
        res["fix_applied"] = clean_warning_text(res.get("fix_applied", "Inspect logs, check connection settings, restart instance."))
        res["confidence"] = int(res.get("confidence", 40))
        res["specifics"] = []
        return res

    def resolve_and_learn(
        self,
        alert_data: Dict[str, Any],
        resolution_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Exception]]:
        """
        Save resolution into Hindsight Cloud and retain as permanent institutional memory.
        Uses shared retain_incident() utility with full error logging and traceback.
        """
        # Combine alert and resolution info
        merged_incident = {
            "incident_id": resolution_data.get("incident_id"),
            "team": alert_data.get("team", "unknown"),
            "service": alert_data.get("service", "unknown"),
            "severity": alert_data.get("severity", "P2"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_signature": alert_data.get("error_signature", ""),
            "error_message": alert_data.get("error_message", ""),
            "stack_trace_snippet": alert_data.get("stack_trace_snippet", "N/A"),
            "root_cause": clean_warning_text(resolution_data.get("root_cause", "")),
            "fix_applied": clean_warning_text(resolution_data.get("fix_applied", "")),
            "resolved_by": resolution_data.get("resolved_by", "oncall-engineer"),
            "time_to_resolve_minutes": str(resolution_data.get("time_to_resolve_minutes", 20)),
            "estimated_revenue_impact": str(resolution_data.get("estimated_revenue_impact", "$15,000"))
        }

        try:
            success, doc_id, err = retain_incident(
                client=self.hindsight,
                bank_id=self.bank_id,
                incident_data=merged_incident,
                update_mode="replace"
            )
            return success, doc_id, err
        except Exception as e:
            logger.error(f"Failed in resolve_and_learn: {e}")
            traceback.print_exc()
            return False, merged_incident.get("incident_id", ""), e

    def is_recallable(self, query: str, expected_doc_id: str) -> bool:
        """Helper to verify if a recently retained incident is immediately recallable."""
        try:
            resp = self.hindsight.recall(bank_id=self.bank_id, query=query, max_tokens=1000)
            results = getattr(resp, "results", []) or []
            for r in results:
                doc_id = getattr(r, "document_id", "")
                r_meta = getattr(r, "metadata", {}) or {}
                if doc_id == expected_doc_id or r_meta.get("incident_id") == expected_doc_id:
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking recallability: {e}")
            return False
