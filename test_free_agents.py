#!/usr/bin/env python3
"""
Test VaccineGenics agent with FREE Foundry options (no credit card).

This script verifies:
  1. GitHub Models (Azure AI Inference) — completely free
  2. Azure OpenAI fallback (if you have free credits)
  3. Offline mode (local, no cloud)
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

from config import GITHUB_TOKEN, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
from agent.foundry_agent import get_agent


def test_agent_availability():
    """Check which agent modes are available."""
    logger.info("=" * 70)
    logger.info("VaccineGenics Agent Availability Check (Free Tier)")
    logger.info("=" * 70)
    
    credentials = {
        "GITHUB_TOKEN (GitHub Models)": bool(GITHUB_TOKEN),
        "AZURE_OPENAI_ENDPOINT": bool(AZURE_OPENAI_ENDPOINT),
        "AZURE_OPENAI_API_KEY": bool(AZURE_OPENAI_API_KEY),
    }
    
    logger.info("\n✓ Configured Credentials:")
    for name, available in credentials.items():
        status = "✅ READY" if available else "❌ Not configured"
        logger.info(f"  {name:40} {status}")
    
    if not any(credentials.values()):
        logger.error("\n❌ No credentials configured! Check your .env file.")
        return False
    
    logger.info("\n🚀 Attempting to initialize agent...")
    try:
        agent = get_agent()
        logger.info(f"\n✅ SUCCESS! Agent initialized: {type(agent).__name__}")
        logger.info(f"   Ready for VaccineGenics analysis")
        return True
    except Exception as exc:
        logger.error(f"\n❌ Failed to initialize agent: {exc}")
        return False


def test_patient_analysis():
    """Test a real patient analysis with free agent."""
    logger.info("\n" + "=" * 70)
    logger.info("Testing Patient Analysis (Free Agent)")
    logger.info("=" * 70)
    
    # Sample patient data
    test_patient = {
        "patient_id": "TEST-001",
        "age": 35,
        "sex": "M",
        "target_vaccine": "mRNA",
        "special_condition": "NONE",
        "hla_haplotype": {"A": ["A*02:01", "A*01:01"], "B": ["B*44:03", "B*44:02"]},
        "apoe_genotype": "E3/E3",
        "variants": {
            "TLR4-rs4986790": {"rsid": "rs4986790", "alt_allele_count": 1},
            "STAT3-rs744166": {"rsid": "rs744166", "alt_allele_count": 0},
        }
    }
    
    try:
        logger.info(f"\nAnalyzing patient: {test_patient['patient_id']}")
        agent = get_agent()
        result = agent.analyze_patient(test_patient, verbose=True)
        
        logger.info(f"\n✅ Analysis Complete!")
        logger.info(f"   Platform: {result.get('platform', 'N/A')}")
        logger.info(f"   Protection Probability: {result.get('protection_probability', 'N/A'):.1%}")
        logger.info(f"   Risk Level: {result.get('overall_risk_level', 'N/A')}")
        logger.info(f"   Agent Used: {result.get('run_status', 'Unknown')}")
        
        return True
    except Exception as exc:
        logger.error(f"\n❌ Analysis failed: {exc}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("\n")
    logger.info("╔══════════════════════════════════════════════════════════════════╗")
    logger.info("║  VaccineGenics - FREE Agent Test (Agents League Hackathon)      ║")
    logger.info("║  No credit card required - GitHub Models is completely FREE!   ║")
    logger.info("╚══════════════════════════════════════════════════════════════════╝")
    logger.info("\n")
    
    # Step 1: Check credentials
    if not test_agent_availability():
        logger.error("\n❌ Cannot proceed without credentials. Check your .env file.")
        sys.exit(1)
    
    # Step 2: Test analysis
    if test_patient_analysis():
        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL TESTS PASSED - Ready for the competition!")
        logger.info("=" * 70)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 70)
        logger.error("❌ Tests failed - Debug the errors above")
        logger.error("=" * 70)
        sys.exit(1)
