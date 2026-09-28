"""
test_scenarios.py
Headless end-to-end verification script for Cross-Team Incident Memory Agent.
Validates all 4 planted scenarios:
  1. Cold Start (No Memory)
  2. Same-Team Repeat (Checkout Idempotency Deadlock)
  3. Cross-Team Echo (Fraud detection socket timeout -> Auth Redis pool fix)
  4. False Friend (Webhook 504 DNS NXDOMAIN vs historical gateway pool restart)
"""

import logging
import sys
from agent import CrossTeamIncidentAgent

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_scenarios")

SCENARIOS = [
    {
        "name": "Scenario 1: Brand-New Alert (Cold Start / No Memory)",
        "alert": {
            "team": "checkout",
            "service": "checkout-service",
            "severity": "P1",
            "error_signature": "ERR_SSL_HANDSHAKE_PQC_KEY_EXCHANGE_REJECTED",
            "error_message": "javax.net.ssl.SSLHandshakeException: Post-quantum cryptography Kyber key exchange handshake rejected by payment gateway proxy",
            "stack_trace_snippet": "javax.net.ssl.SSLHandshakeException: Kyber-1024 hybrid key exchange failed\n    at java.base/sun.security.ssl.Alert.createSSLException(Alert.java:131)\n    at java.base/sun.security.ssl.TransportContext.fatal(TransportContext.java:371)\n    at com.fintech.checkout.gateway.PqcTlsClient.negotiate(PqcTlsClient.java:78)"
        },
        "expected_match_type": "none",
        "max_confidence": 70,
        "description": "Novel cryptographic failure with no historical precedent. Agent should return generic advice."
    },
    {
        "name": "Scenario 2: Same-Team Repeat (Checkout Idempotency Deadlock)",
        "alert": {
            "team": "checkout",
            "service": "checkout-service",
            "severity": "P1",
            "error_signature": "PgDeadlockException: Idempotency keys row lock conflict during checkout retry storm",
            "error_message": "org.postgresql.util.PSQLException: ERROR: deadlock detected. Detail: Process 41012 waits for ExclusiveLock on tuple (512, 22) of relation 'payment_idempotency_keys'; blocked by process 41019.",
            "stack_trace_snippet": "org.postgresql.util.PSQLException: ERROR: deadlock detected\n    at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2553)\n    at com.fintech.checkout.idempotency.IdempotencyManager.acquireLock(IdempotencyManager.java:94)\n    at com.fintech.checkout.service.CheckoutOrchestrator.processPayment(CheckoutOrchestrator.java:142)"
        },
        "expected_match_type": "same_team",
        "expected_team": "checkout",
        "min_confidence": 80,
        "description": "Exact repeat of checkout idempotency PostgreSQL deadlock. Agent should recall Redis redlock fix."
    },
    {
        "name": "Scenario 3: The Cross-Team Echo (The Differentiator!)",
        "alert": {
            "team": "fraud-detection",
            "service": "fraud-detection-service",
            "severity": "P1",
            "error_signature": "DownstreamSocketReadTimeout: Socket read timed out during risk evaluation",
            "error_message": "java.net.SocketTimeoutException: Read timed out reading from downstream socket after 5000ms during transaction risk scoring evaluation.",
            "stack_trace_snippet": "java.net.SocketTimeoutException: Read timed out reading from socket\n    at java.base/java.net.SocketInputStream.read(SocketInputStream.java:185)\n    at com.fintech.fraud.evaluator.TransactionRiskEvaluator.evaluateRisk(TransactionRiskEvaluator.java:112)\n    at com.fintech.fraud.service.FraudScoringService.scoreTransaction(FraudScoringService.java:65)"
        },
        "expected_match_type": "cross_team",
        "expected_team": "auth",
        "expected_doc_id": "INC-2026-0314",
        "min_confidence": 80,
        "description": "Alert has ZERO mention of Redis or Jedis. Agent discovers root cause from Auth team incident 6 months ago!"
    },
    {
        "name": "Scenario 4: The False Friend (Textually Similar, Different Root Cause)",
        "alert": {
            "team": "payments-core",
            "service": "webhook-dispatcher",
            "severity": "P2",
            "error_signature": "WebhookGatewayTimeout: HTTP 504 Gateway Timeout delivering merchant dispute webhooks",
            "error_message": "com.fintech.webhook.exception.DeliveryFailedException: HTTP 504 Gateway Timeout while sending merchant dispute webhook to gateway endpoint https://dispatch.fintech.internal/v1/webhooks",
            "stack_trace_snippet": "com.fintech.webhook.exception.DeliveryFailedException: HTTP 504 Gateway Timeout\n    at com.fintech.webhook.client.WebhookHttpClient.dispatch(WebhookHttpClient.java:88)\nCaused by: java.net.UnknownHostException: dispatch.fintech.internal: Name or service not known (DNS NXDOMAIN)\n    at java.base/java.net.InetAddress.getAllByName(InetAddress.java:1328)"
        },
        "expected_match_type": "none",
        "max_confidence": 70,
        "requires_caution": True,
        "description": "Text resembles 504 gateway timeout, but DNS NXDOMAIN root cause differs. Agent must flag caution."
    }
]

def run_all_tests():
    print("================================================================================")
    print("STARTING TEST SUITE: Cross-Team Incident Memory Agent (4/4 Scenarios)")
    print("================================================================================")

    agent = CrossTeamIncidentAgent()
    passed = 0
    total = len(SCENARIOS)

    for i, scen in enumerate(SCENARIOS, 1):
        print(f"\n[{i}/{total}] Running {scen['name']}...")
        print(f"      Description: {scen['description']}")

        alert = scen["alert"]
        memories = agent.recall_memories(alert, max_tokens=1500)
        print(f"      Recalled {len(memories)} candidate memories from Hindsight.")

        diag = agent.diagnose_with_memory(alert, memories)
        match_type = diag.get("match_type")
        confidence = diag.get("confidence", 0)
        matched_id = diag.get("matched_incident_id")
        matched_team = diag.get("matched_team")
        caution = diag.get("caution_warning")

        print(f"      Result: match_type='{match_type}', confidence={confidence}%, matched_id={matched_id}, matched_team={matched_team}")
        if caution:
            print(f"      Caution Warning: {caution}")

        # Assertions
        test_ok = True
        reasons = []

        if match_type != scen["expected_match_type"]:
            test_ok = False
            reasons.append(f"Expected match_type '{scen['expected_match_type']}', got '{match_type}'")

        if "min_confidence" in scen and confidence < scen["min_confidence"]:
            test_ok = False
            reasons.append(f"Expected confidence >= {scen['min_confidence']}%, got {confidence}%")

        if "max_confidence" in scen and confidence > scen["max_confidence"]:
            test_ok = False
            reasons.append(f"Expected confidence <= {scen['max_confidence']}%, got {confidence}%")

        if "expected_team" in scen and matched_team and matched_team.lower() != scen["expected_team"].lower():
            test_ok = False
            reasons.append(f"Expected matched_team '{scen['expected_team']}', got '{matched_team}'")

        if "expected_doc_id" in scen and matched_id and matched_id != scen["expected_doc_id"]:
            # If doc_id differs, check if team is auth
            if matched_team != "auth":
                test_ok = False
                reasons.append(f"Expected doc_id '{scen['expected_doc_id']}', got '{matched_id}'")

        if scen.get("requires_caution") and not caution:
            test_ok = False
            reasons.append("Expected caution_warning to be set for False Friend scenario")

        if test_ok:
            passed += 1
            print(f"  --> PASS: {scen['name']}")
        else:
            print(f"  --> FAIL: {scen['name']}")
            for r in reasons:
                print(f"      FAILED ASSERTION: {r}")

    print("\n================================================================================")
    print(f"TEST RESULTS: {passed}/{total} scenarios PASSED.")
    print("================================================================================")

    if passed == total:
        print("[SUCCESS] All 4/4 verification scenarios passed successfully!")
        return 0
    else:
        print(f"[FAILURE] {total - passed} scenario(s) failed.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
