"""
load_memory.py
Idempotent Hindsight Memory Loader for Payment Infrastructure Incidents.
Pushes past incidents from data/incidents.json into Hindsight Cloud.
Uses shared retain_incident() from memory_utils.py to guarantee consistency.
"""

import argparse
import json
import logging
import os
import sys
import time
from dotenv import load_dotenv
from hindsight_client import Hindsight
from memory_utils import retain_incident

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def purge_and_recreate_bank(client: Hindsight, bank_id: str):
    """Purge old bank documents by resetting/recreating the bank cleanly."""
    logger.info(f"Purging existing memory bank '{bank_id}' to clear legacy documents...")
    try:
        client.delete_bank(bank_id=bank_id)
        logger.info(f"Successfully deleted bank '{bank_id}'.")
    except Exception as e:
        logger.warning(f"Could not delete bank '{bank_id}' (may not exist yet): {e}")

    time.sleep(1)
    logger.info(f"Recreating bank '{bank_id}'...")
    try:
        client.create_bank(
            bank_id=bank_id,
            name="Payment Infrastructure Incidents",
            mission="Autonomous cross-team incident memory for payment infrastructure (checkout, payments-core, auth, fraud-detection)."
        )
        logger.info(f"Successfully created bank '{bank_id}'.")
    except Exception as e:
        logger.error(f"Error creating bank '{bank_id}': {e}")
        raise

def load_incidents_to_hindsight(
    file_path: str = "data/incidents.json",
    bank_id: str | None = None,
    clean: bool = False
):
    load_dotenv()

    api_key = os.getenv("HINDSIGHT_API_KEY")
    base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
    bank_id = bank_id or os.getenv("HINDSIGHT_BANK_ID", "payment-infrastructure-incidents")

    if not api_key:
        logger.error("HINDSIGHT_API_KEY is not set in environment or .env file.")
        sys.exit(1)

    logger.info(f"Connecting to Hindsight Cloud at {base_url} (Bank ID: {bank_id})...")
    client = Hindsight(base_url=base_url, api_key=api_key)

    if clean:
        purge_and_recreate_bank(client, bank_id)

    if not os.path.exists(file_path):
        logger.error(f"Incident data file not found at '{file_path}'. Run generate_data.py first.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        incidents = json.load(f)

    total_incidents = len(incidents)
    logger.info(f"Loaded {total_incidents} incidents from {file_path}. Retaining into Hindsight...")

    retained_count = 0
    errors_count = 0

    for i, inc in enumerate(incidents, 1):
        doc_id = inc.get("incident_id", f"INC-{i:04d}")
        team = inc.get("team", "unknown")
        service = inc.get("service", "unknown")

        logger.info(f"[{i}/{total_incidents}] Retaining {doc_id} ({team} -> {service})...")
        success, returned_id, err = retain_incident(client, bank_id, inc, update_mode="replace")

        if success:
            retained_count += 1
        else:
            errors_count += 1
            logger.error(f"Failed to retain {doc_id}: {err}")

        # Minor pause to respect network rate pacing
        time.sleep(0.05)

    logger.info("==================================================")
    logger.info(f"Memory Seeding Completed!")
    logger.info(f"Total Processed: {total_incidents}")
    logger.info(f"Successfully Retained: {retained_count}")
    logger.info(f"Errors: {errors_count}")
    logger.info(f"Bank ID: {bank_id}")
    logger.info("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load incident memories into Hindsight")
    parser.add_argument("--file", default="data/incidents.json", help="Path to incidents.json")
    parser.add_argument("--bank-id", default=None, help="Hindsight Bank ID override")
    parser.add_argument("--clean", action="store_true", help="Clean/recreate memory bank before loading")
    args = parser.parse_args()

    load_incidents_to_hindsight(file_path=args.file, bank_id=args.bank_id, clean=args.clean)
