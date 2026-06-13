#!/usr/bin/env python3
"""
Quick connectivity test for the FoundryProjectAgent.
Run from the project root: python test_foundry.py
"""
import sys, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from config import AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_PROJECT_KEY

logger.info("Endpoint : %s", AZURE_AI_PROJECT_ENDPOINT or "(not set)")
logger.info("Key      : %s", ("****" + AZURE_AI_PROJECT_KEY[-4:]) if AZURE_AI_PROJECT_KEY else "(not set)")

if not AZURE_AI_PROJECT_ENDPOINT or not AZURE_AI_PROJECT_KEY:
    logger.error("Set AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_PROJECT_KEY in .env")
    sys.exit(1)

from agent.foundry_agent import FoundryProjectAgent

agent = FoundryProjectAgent()
logger.info("URL      : %s", agent._url)
logger.info("Sending ping...")

import requests
payload = {
    "input": [{"role": "user", "content": "Responde solo: OK"}],
    "agent_reference": {"name": "vaccinegenics", "version": "1", "type": "agent_reference"},
}
r = requests.post(
    agent._url,
    headers=agent._headers(),
    json=payload,
    timeout=20,
)
logger.info("HTTP %s", r.status_code)
logger.info("Body: %s", r.text[:600])
