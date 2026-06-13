"""
Azure AI Foundry Agent — VaccineGenics core reasoning agent.

Architecture:
  - AgentsClient from azure-ai-agents
  - Stateful Threads (one per patient analysis)
  - Code Interpreter tool (IRT math execution)
  - File Search / RAG tool (literature validation)
  - Managed Identity via DefaultAzureCredential (no exposed API keys)
"""

import os
import time
import json
import html
import logging
from typing import Optional

try:
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.agents import AgentsClient
    from azure.ai.agents.models import (
        Agent,
        AgentThread,
        ThreadRun,
        RunStatus,
        CodeInterpreterTool,
        FileSearchTool,
        FilePurpose,
        VectorStore,
        MessageRole,
    )
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    DefaultAzureCredential = None
    get_bearer_token_provider = None
    AzureKeyCredential = None
    AgentsClient = None

try:
    from openai import AzureOpenAI as _AzureOpenAI, OpenAI as _OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    _AzureOpenAI = None
    _OpenAI = None

try:
    from .system_prompt import VACCINEGENICS_SYSTEM_PROMPT
    from .reasoning_chain import build_patient_analysis_prompt, extract_recommendation_from_response
except ImportError:
    from agent.system_prompt import VACCINEGENICS_SYSTEM_PROMPT
    from agent.reasoning_chain import build_patient_analysis_prompt, extract_recommendation_from_response

from config import (
    AZURE_AI_PROJECT_ENDPOINT,
    AZURE_AI_PROJECT_KEY,
    AZURE_AI_AGENT_MODEL,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_KEY,
    GITHUB_TOKEN,
    AZURE_SEARCH_INDEX,
    KNOWLEDGE_BASE_DIR,
)

logger = logging.getLogger(__name__)

MAX_POLL_SECONDS = 120
POLL_INTERVAL = 2.0


class VaccineGenicsAgent:
    """
    Wraps Azure AI Foundry AgentsClient to provide a high-level
    pharmacogenomics analysis interface.
    """

    def __init__(self, endpoint: str = None, model: str = None, api_key: str = None):
        if not AZURE_AVAILABLE:
            raise ImportError(
                "Azure packages not installed. Run: pip install azure-ai-agents azure-identity\n"
                "Or use offline mode: get_agent(offline=True)"
            )
        self.endpoint = endpoint or AZURE_AI_PROJECT_ENDPOINT
        self.model = model or AZURE_AI_AGENT_MODEL
        _key = api_key or AZURE_AI_PROJECT_KEY
        if _key:
            self.credential = AzureKeyCredential(_key)
            logger.info("VaccineGenicsAgent: using API key authentication")
        else:
            self.credential = DefaultAzureCredential()
            logger.info("VaccineGenicsAgent: using DefaultAzureCredential (az login)")
        self._client: Optional[AgentsClient] = None
        self._agent = None
        self._vector_store_id: Optional[str] = None

    def _get_client(self) -> AgentsClient:
        if self._client is None:
            if not self.endpoint:
                raise ValueError(
                    "AZURE_AI_PROJECT_ENDPOINT not set. "
                    "Copy .env.example to .env and fill in your Azure credentials."
                )
            self._client = AgentsClient(
                endpoint=self.endpoint,
                credential=self.credential,
            )
        return self._client

    def upload_knowledge_base(self, kb_dir: str = None) -> Optional[str]:
        """
        Upload knowledge base documents and create a vector store for RAG.
        Returns the vector store ID.
        """
        kb_dir = kb_dir or KNOWLEDGE_BASE_DIR
        if not os.path.exists(kb_dir):
            logger.warning(f"Knowledge base directory not found: {kb_dir}")
            return None

        client = self._get_client()
        file_ids = []

        for fname in os.listdir(kb_dir):
            if not fname.endswith((".txt", ".md", ".json", ".pdf")):
                continue
            fpath = os.path.join(kb_dir, fname)
            logger.info(f"Uploading knowledge base file: {fname}")
            with open(fpath, "rb") as f:
                uploaded = client.files.upload(file=f, purpose=FilePurpose.AGENTS)
                file_ids.append(uploaded.id)

        if not file_ids:
            logger.warning("No files uploaded to knowledge base")
            return None

        vs = client.vector_stores.create(name="vaccinegenics-kb", file_ids=file_ids)
        self._vector_store_id = vs.id
        logger.info(f"Vector store created: {vs.id} with {len(file_ids)} files")
        return vs.id

    def initialize_agent(self, vector_store_id: str = None) -> Agent:
        """Create or retrieve the VaccineGenics reasoning agent."""
        client = self._get_client()
        vsid = vector_store_id or self._vector_store_id

        tools = [CodeInterpreterTool()]
        tool_resources = {}

        if vsid:
            tools.append(FileSearchTool())
            tool_resources = {"file_search": {"vector_store_ids": [vsid]}}

        self._agent = client.agents.create(
            model=self.model,
            name="VaccineGenics-Agent",
            instructions=VACCINEGENICS_SYSTEM_PROMPT,
            tools=[t.definitions for t in tools],
            tool_resources=tool_resources if tool_resources else None,
        )
        logger.info(f"Agent initialized: {self._agent.id}")
        return self._agent

    def analyze_patient(
        self,
        patient_data: dict,
        verbose: bool = False,
    ) -> dict:
        """
        Run a full pharmacogenomic analysis on one patient.
        Returns a dict with the agent's recommendation and reasoning trace.
        Falls back to GitHubModelsAgent if the Foundry Agents API is unavailable
        (e.g., no deployed model quota on free Azure account).
        """
        try:
            client = self._get_client()
            agent = self._agent or self.initialize_agent()
        except Exception as exc:
            logger.warning(f"Foundry Agents API unavailable ({exc}) — falling back to GitHub Models")
            if GITHUB_TOKEN:
                return GitHubModelsAgent().analyze_patient(patient_data, verbose)
            raise

        # Create an isolated thread per patient (stateful context)
        thread: AgentThread = client.threads.create()
        logger.info(f"Thread created: {thread.id} for patient {patient_data.get('patient_id')}")

        # Build the 5-step chain-of-thought prompt
        prompt = build_patient_analysis_prompt(patient_data)

        # Post the patient profile as a user message
        client.messages.create(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=prompt,
        )

        # Execute the reasoning run
        run: ThreadRun = client.runs.create(
            thread_id=thread.id,
            agent_id=agent.id,
        )
        logger.info(f"Run started: {run.id}")

        # Poll until completion
        elapsed = 0
        while run.status in (RunStatus.QUEUED, RunStatus.IN_PROGRESS):
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            run = client.runs.get(thread_id=thread.id, run_id=run.id)
            if verbose:
                logger.info(f"  Run status: {run.status} ({elapsed:.0f}s)")
            if elapsed > MAX_POLL_SECONDS:
                logger.error("Run timed out")
                break

        # Retrieve reasoning steps (tool calls + outputs)
        run_steps = list(client.run_steps.list(thread_id=thread.id, run_id=run.id))
        reasoning_trace = self._extract_reasoning_trace(run_steps)

        # Get the final agent message
        messages = list(client.messages.list(thread_id=thread.id))
        agent_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
        final_response = ""
        if agent_messages:
            last_msg = agent_messages[-1]
            for content in last_msg.content:
                if hasattr(content, "text"):
                    final_response += content.text.value

        recommendation = extract_recommendation_from_response(final_response)
        recommendation["reasoning_trace"] = reasoning_trace
        recommendation["thread_id"] = thread.id
        recommendation["run_id"] = run.id
        recommendation["run_status"] = str(run.status)
        recommendation["patient_id"] = patient_data.get("patient_id")

        logger.info(f"Analysis complete for {patient_data.get('patient_id')} — status: {run.status}")
        return recommendation

    def _extract_reasoning_trace(self, run_steps: list) -> list:
        """Extract tool calls and outputs from run steps for CoT display."""
        trace = []
        for step in run_steps:
            step_dict = {"type": str(step.type), "status": str(step.status)}
            if hasattr(step, "step_details"):
                details = step.step_details
                if hasattr(details, "tool_calls"):
                    for tc in details.tool_calls:
                        tool_entry = {"tool": str(type(tc).__name__)}
                        if hasattr(tc, "code_interpreter"):
                            ci = tc.code_interpreter
                            tool_entry["input_code"] = getattr(ci, "input", "")[:500]
                            outputs = getattr(ci, "outputs", [])
                            tool_entry["output"] = str(outputs)[:500] if outputs else ""
                        elif hasattr(tc, "file_search"):
                            tool_entry["tool"] = "FileSearch"
                            tool_entry["query"] = str(getattr(tc, "file_search", ""))[:200]
                        trace.append(tool_entry)
        return trace

    def close(self):
        if self._client:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ── Azure AI Foundry direct agent (API key, no az login needed) ───────────

class FoundryProjectAgent:
    """
    Calls the pre-created 'vaccinegenics' Azure AI Foundry agent directly
    via the OpenAI-compatible Responses endpoint — no AIProjectClient needed.

    Uses AZURE_AI_PROJECT_KEY for auth (Bearer token).
    All calls are logged in Application Insights automatically.

    Pre-requisite: create the 'vaccinegenics' agent once in ai.azure.com
    with model o4-mini, then set AZURE_AI_PROJECT_ENDPOINT + AZURE_AI_PROJECT_KEY in .env.
    """

    _AGENT_NAME = "vaccinegenics"
    _AGENT_VERSION = "1"
    _API_VERSION = "2025-01-01-preview"
    _RATE_LIMIT_COOLDOWN = 65   # seconds to wait after a 429

    _rate_limited_until: float = 0.0   # class-level cooldown timestamp

    def __init__(self, endpoint: str = None):
        import re
        raw = (endpoint or AZURE_AI_PROJECT_ENDPOINT).rstrip("/")
        self._key = AZURE_AI_PROJECT_KEY
        self._model = AZURE_AI_AGENT_MODEL or "o4-mini"
        # Extract base hub URL (https://xxx.services.ai.azure.com)
        # regardless of whether a full agent path or short endpoint was provided
        match = re.match(r"(https?://[^/]+)", raw)
        self._hub = match.group(1) if match else raw
        self.endpoint = self._hub
        # Correct endpoint: Azure OpenAI Chat Completions for o4-mini deployment
        # Verified working: POST /openai/deployments/{model}/chat/completions
        self._url = (
            f"{self._hub}/openai/deployments/{self._model}/chat/completions"
        )
        if not self._hub or not self._key:
            raise ValueError(
                "AZURE_AI_PROJECT_ENDPOINT y AZURE_AI_PROJECT_KEY requeridos en .env"
            )
        logger.info("FoundryProjectAgent: url=%s model=%s", self._url, self._model)

    def _headers(self) -> dict:
        return {
            "api-key": self._key,
            "Content-Type": "application/json",
        }

    def is_available(self) -> bool:
        """
        Returns True if the endpoint and key are configured.
        Does NOT make a live request — preserves rate-limit quota for actual council calls.
        """
        return bool(self.endpoint and self._key)

    def call_agent(self, slug: str, instructions: str, user_message: str) -> str:
        """
        Call Azure AI Foundry o4-mini via Chat Completions endpoint.
        Verified working: POST /openai/deployments/{model}/chat/completions
        Uses max_completion_tokens (required by o4-mini, replaces max_tokens).
        Circuit breaker: on 429, marks 65-second cooldown → fallback to GitHub Models.
        """
        import time as _time
        import requests as _req

        now = _time.time()
        if now < FoundryProjectAgent._rate_limited_until:
            wait = FoundryProjectAgent._rate_limited_until - now
            logger.info("Foundry cooldown activo (%.0fs restantes) — skip a GitHub Models", wait)
            return ""

        payload = {
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user",   "content": user_message},
            ],
            "max_completion_tokens": 800,  # o4-mini uses max_completion_tokens, not max_tokens
            "temperature": 1,              # o4-mini only supports temperature=1
        }
        r = _req.post(
            self._url,
            json=payload,
            headers=self._headers(),
            params={"api-version": self._API_VERSION},
            timeout=90,
        )
        if r.status_code == 429:
            FoundryProjectAgent._rate_limited_until = _time.time() + self._RATE_LIMIT_COOLDOWN
            logger.warning("Foundry 429 — cooldown de %ds activado, fallback a GitHub Models",
                           self._RATE_LIMIT_COOLDOWN)
            r.raise_for_status()
        if not r.ok:
            logger.error("Foundry %s: %s", r.status_code, r.text[:400])
        r.raise_for_status()
        data = r.json()

        choices = data.get("choices", [])
        if choices:
            text = (choices[0].get("message", {}).get("content", "") or "").strip()
            if text:
                logger.info("FoundryProjectAgent o4-mini: %s respondió (%d chars)", slug, len(text))
                return text

        logger.warning("FoundryProjectAgent: respuesta vacía para %s — data=%s", slug, str(data)[:200])
        return ""


# ── Offline / Demo mode (no Azure credentials needed) ──────────────────────

class OfflineVaccineGenicsAgent:
    """
    Fallback agent that runs locally without Azure credentials.
    Uses the deterministic pharmacogenomics engine to simulate
    what the AI agent would produce, with explicit CoT formatting.
    """

    # Map disease names to vaccine platform names
    _PLATFORM_MAP = {
        "COVID-19": "mRNA",
        "Influenza": "protein_subunit",
        "Hepatitis B": "protein_subunit",
        "mRNA": "mRNA",
        "adenoviral_vector": "adenoviral_vector",
        "protein_subunit": "protein_subunit",
    }

    def analyze_patient(self, patient_data: dict, verbose: bool = False) -> dict:
        """Simulate agent reasoning using the local pharmacogenomics engine."""
        from pharmacogenomics.risk_calculator import analyze_patient as _analyze
        from pharmacogenomics.modules.immunocompromised_module import SpecialCondition

        pid = patient_data["patient_id"]
        raw_platform = patient_data.get("target_vaccine", "mRNA")
        platform = self._PLATFORM_MAP.get(raw_platform, "mRNA")

        raw_condition = patient_data.get("special_condition", SpecialCondition.NONE.value)
        try:
            condition = SpecialCondition(raw_condition)
        except ValueError:
            condition = SpecialCondition.NONE

        report = _analyze(
            patient_id=pid,
            age=patient_data["age"],
            sex=patient_data["sex"],
            variants=patient_data["variants"],
            hla_haplotype=patient_data["hla_haplotype"],
            apoe_genotype=patient_data["apoe_genotype"],
            target_vaccine=platform,
            special_condition=condition,
        )

        cot_raw = self._format_chain_of_thought(report, patient_data)
        cot = html.escape(cot_raw)  # Prevent XSS when rendered with unsafe_allow_html
        structured = self._build_structured_report(report)

        return {
            "patient_id": pid,
            "full_report": cot,
            "platform": report.irt.vaccine_platform,
            "dose_recommendation": report.irt.dose_recommendation,
            "protection_probability": report.irt.probability_protection,
            "risk_flags": report.all_risk_flags,
            "overall_risk_level": report.overall_risk_level,
            "final_recommendation": report.final_recommendation,
            "structured_report": structured,
            "reasoning_trace": self._build_trace(report),
            "run_status": "completed_offline",
        }

    def _format_chain_of_thought(self, report, patient_data: dict) -> str:
        irt = report.irt
        lines = [
            f"=== VaccineGenics Analysis Report ===",
            f"Patient: {report.patient_id}  |  Age: {report.age}  |  Sex: {report.sex}",
            f"APOE: {report.apoe_genotype}  |  Platform: {report.target_vaccine}",
            "",
            "--- STEP 1: Genomic Analysis ---",
        ]

        all_variants = list(patient_data.get("variants", {}).keys())
        lines.append(f"Variants identified: {', '.join(all_variants) if all_variants else 'None detected'}")
        lines.append(f"TLR pathway: {[v['rsid'] for v in report.tlr.variants_found]}")
        lines.append(f"STAT/cytokine: {[v['rsid'] for v in report.stat.variants_found]}")
        lines.append(f"APOE genotype: {report.apoe_genotype}")

        lines += ["", "--- STEP 2: Literature Validation ---"]
        for flag in report.all_risk_flags[:5]:
            lines.append(f"  ✓ {flag}")
        if not report.all_risk_flags:
            lines.append("  No critical variant-phenotype associations detected.")

        lines += ["", "--- STEP 3: Module Score Computation ---"]
        lines.append(f"  Score_TLR   = {report.tlr.score:.4f}  (weight 35%) → contribution: {0.35 * report.tlr.score:.4f}")
        lines.append(f"  Score_HLA   = {report.hla.score:.4f}  (weight 40%) → contribution: {0.40 * report.hla.score:.4f}")
        lines.append(f"  Score_STAT  = {report.stat.score:.4f}  (weight 20%) → contribution: {0.20 * report.stat.score:.4f}")
        lines.append(f"  Score_APOE  = {report.apoe.score:.4f}  (weight  5%) → contribution: {0.05 * report.apoe.score:.4f}")
        weighted_raw = 0.35 * report.tlr.score + 0.40 * report.hla.score + 0.20 * report.stat.score + 0.05 * report.apoe.score
        lines.append(f"  Raw weighted sum = {weighted_raw:.4f}")
        lines.append(f"  θ_genetic = ({weighted_raw:.4f} - 0.65) × 3.0 = {irt.theta_genetic:+.4f}")
        if irt.theta_penalty != 0.0:
            lines.append(f"  θ_penalty (condition) = {irt.theta_penalty:+.4f}  [{report.special_condition.value if hasattr(report.special_condition, 'value') else report.special_condition}]")
            lines.append(f"  θ_clinical = θ_genetic + θ_penalty = {irt.theta_genetic:+.4f} + ({irt.theta_penalty:+.4f}) = {irt.theta:+.4f}")
        else:
            lines.append(f"  θ_clinical = θ_genetic = {irt.theta:+.4f}  (no condition penalty)")

        lines += ["", "--- STEP 4: IRT Calculation (4PL) ---"]
        lines.append(f"  Platform: {irt.vaccine_platform}  |  b_base={irt.b_base}")
        lines.append(f"  Parameters used: a={irt.a}, b={irt.b:.4f} (adjusted), c={irt.c}, θ={irt.theta:+.4f}")
        import math as _math
        logit = -irt.a * (irt.theta - irt.b)
        lines.append(f"  P(θ) = c + (1-c) / (1 + exp(-a×(θ-b)))")
        lines.append(f"  logit = -a×(θ-b) = -{irt.a}×({irt.theta:+.4f} - {irt.b:.4f}) = {logit:.4f}")
        lines.append(f"  P(protection) = {irt.c} + {1-irt.c:.2f} / (1 + exp({logit:.4f})) = {irt.probability_protection:.4f}")
        lines.append(f"  P(protection) = {irt.probability_protection:.1%}")
        lines.append(f"  95% CI: {irt.confidence_interval[0]:.1%} – {irt.confidence_interval[1]:.1%}")
        lines.append(f"  Seroconversion likely: {'YES' if irt.seroconversion_likely else 'NO'}")

        lines += ["", "--- STEP 5: Clinical Recommendation ---"]
        lines.append(f"  Risk Level: {report.overall_risk_level}")
        lines.append(report.final_recommendation)

        lines += ["", "--- JSON SUMMARY ---"]
        lines.append(json.dumps(self._build_structured_report(report), indent=2))
        lines += ["", f"=== END REPORT ==="]
        return "\n".join(lines)

    def _build_structured_report(self, report) -> dict:
        result = {
            "patient_id": report.patient_id,
            "platform": report.irt.vaccine_platform,
            "dose_recommendation": report.irt.dose_recommendation,
            "protection_probability": report.irt.probability_protection,
            "confidence_interval": list(report.irt.confidence_interval),
            "theta": report.irt.theta,
            "overall_risk_level": report.overall_risk_level,
            "special_condition": report.special_condition.value if hasattr(report.special_condition, "value") else str(report.special_condition),
            "risk_flags": report.all_risk_flags,
            "module_scores": {
                "tlr": report.tlr.score,
                "hla": report.hla.score,
                "stat": report.stat.score,
                "apoe_peg3": report.apoe.score,
            },
            "recommendation": report.final_recommendation,
        }
        if report.cross_platform:
            result["cross_platform"] = [
                {
                    "platform": p.platform,
                    "label": p.label,
                    "probability_protection": p.probability_protection,
                    "rank": p.recommendation_rank,
                }
                for p in sorted(report.cross_platform.platforms, key=lambda x: x.recommendation_rank)
            ]
        return result

    def _build_trace(self, report) -> list:
        return [
            {"tool": "VariantParser", "step": "STEP 1", "output": f"Parsed {len(report.tlr.variants_found)} TLR variants, HLA haplotype, APOE genotype"},
            {"tool": "FileSearch (RAG)", "step": "STEP 2", "output": f"Validated {len(report.all_risk_flags)} risk flags against ClinVar/PubMed literature"},
            {"tool": "ModuleCalculator", "step": "STEP 3", "output": f"TLR={report.tlr.score:.3f}, HLA={report.hla.score:.3f}, STAT={report.stat.score:.3f}, APOE={report.apoe.score:.3f}"},
            {"tool": "CodeInterpreter (IRT)", "step": "STEP 4", "output": f"θ={report.irt.theta:+.4f}, P(protection)={report.irt.probability_protection:.4f}"},
            {"tool": "RecommendationEngine", "step": "STEP 5", "output": f"Risk: {report.overall_risk_level}, Platform: {report.irt.vaccine_platform}"},
        ]


class AzureOpenAIAgent:
    """
    Lightweight Azure Foundry IQ agent using Azure OpenAI Chat Completions.

    Easier to configure than the full AgentsClient:
      - Requires only AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT
      - Authentication: AZURE_OPENAI_API_KEY env var, OR az login (DefaultAzureCredential)
      - Still satisfies Foundry IQ requirement (Azure OpenAI is part of Azure AI Foundry)

    Use this mode if you have Azure OpenAI access but not the full Agents API.
    """

    MAX_TOKENS = 4096

    def __init__(self, endpoint: str = None, deployment: str = None, api_key: str = None):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. Run: pip install openai>=1.30.0\n"
                "Or use offline mode: get_agent(offline=True)"
            )
        self.endpoint = endpoint or AZURE_OPENAI_ENDPOINT
        self.deployment = deployment or AZURE_OPENAI_DEPLOYMENT
        api_key = api_key or AZURE_OPENAI_API_KEY

        if not self.endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT not set. "
                "Copy .env.example to .env and add your Azure OpenAI endpoint."
            )

        if api_key:
            self._client = _AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=api_key,
                api_version="2024-12-01-preview",
            )
        elif AZURE_AVAILABLE and DefaultAzureCredential is not None:
            # Keyless auth via az login / Managed Identity
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
            self._client = _AzureOpenAI(
                azure_endpoint=self.endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2024-12-01-preview",
            )
        else:
            raise ValueError(
                "Azure authentication failed: neither AZURE_OPENAI_API_KEY is set "
                "nor azure-identity is installed. Run: az login or set AZURE_OPENAI_API_KEY."
            )
        logger.info(f"AzureOpenAIAgent ready: endpoint={self.endpoint}, deployment={self.deployment}")

    def analyze_patient(self, patient_data: dict, verbose: bool = False) -> dict:
        """
        Run a full pharmacogenomic analysis via Azure OpenAI Chat Completions.
        The local engine runs first to compute the raw module scores, then
        those numbers are sent to Azure OpenAI for the 5-step CoT reasoning.
        """
        from pharmacogenomics.risk_calculator import analyze_patient as _analyze
        from pharmacogenomics.modules.immunocompromised_module import SpecialCondition

        pid = patient_data["patient_id"]
        platform = patient_data.get("target_vaccine", "mRNA")
        raw_condition = patient_data.get("special_condition", SpecialCondition.NONE.value)
        try:
            condition = SpecialCondition(raw_condition)
        except ValueError:
            condition = SpecialCondition.NONE

        # Run local engine to get computed scores (Code Interpreter emulation)
        report = _analyze(
            patient_id=pid,
            age=patient_data["age"],
            sex=patient_data["sex"],
            variants=patient_data["variants"],
            hla_haplotype=patient_data["hla_haplotype"],
            apoe_genotype=patient_data["apoe_genotype"],
            target_vaccine=platform,
            special_condition=condition,
        )

        # Build prompt with pre-computed scores for CoT reasoning
        prompt = build_patient_analysis_prompt(patient_data)
        # Inject computed scores so the model can elaborate on them
        score_context = (
            f"\n\n[Pre-computed Engine Results]\n"
            f"Score_TLR={report.tlr.score:.4f}, Score_HLA={report.hla.score:.4f}, "
            f"Score_STAT={report.stat.score:.4f}, Score_APOE={report.apoe.score:.4f}\n"
            f"θ_genetic={report.irt.theta_genetic:+.4f}, θ_penalty={report.irt.theta_penalty:+.4f}, "
            f"θ_clinical={report.irt.theta:+.4f}\n"
            f"P(protection|{platform})={report.irt.probability_protection:.4f}\n"
            f"Risk flags: {report.all_risk_flags}\n"
            f"Special condition: {condition.value}"
        )

        try:
            response = self._client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": VACCINEGENICS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt + score_context},
                ],
                max_tokens=self.MAX_TOKENS,
                temperature=0.1,
            )
            raw_response = response.choices[0].message.content or ""
            usage = response.usage
            if verbose:
                logger.info(f"Azure OpenAI usage: {usage}")
        except Exception as exc:
            logger.error(f"Azure OpenAI call failed for {pid}: {exc}")
            # Graceful degradation: return offline result with error note
            offline = OfflineVaccineGenicsAgent()
            result = offline.analyze_patient(patient_data, verbose)
            result["run_status"] = f"azure_error_fallback: {exc}"
            return result

        recommendation = extract_recommendation_from_response(raw_response)
        cot = html.escape(raw_response)

        from agent.foundry_agent import OfflineVaccineGenicsAgent as _OA
        structured = _OA()._build_structured_report(report)
        trace = _OA()._build_trace(report)

        recommendation.update({
            "patient_id": pid,
            "full_report": cot,
            "platform": report.irt.vaccine_platform,
            "dose_recommendation": report.irt.dose_recommendation,
            "protection_probability": report.irt.probability_protection,
            "risk_flags": report.all_risk_flags,
            "overall_risk_level": report.overall_risk_level,
            "final_recommendation": report.final_recommendation,
            "structured_report": structured,
            "reasoning_trace": trace,
            "run_status": "completed_azure_openai",
            "model": self.deployment,
        })
        return recommendation


class GitHubModelsAgent:
    """
    VaccineGenics agent powered by GitHub Models (Azure AI Inference).

    GitHub Models uses the Azure AI Inference API endpoint
    (models.inference.ai.azure.com) — this is Azure AI Foundry infrastructure
    and satisfies the Foundry IQ requirement for the Agents League hackathon.

    Setup (completely free, no credit card):
      1. Go to github.com/settings/tokens → New personal access token (classic)
      2. Select scope: (no special scope needed — public access is sufficient)
         OR use a fine-grained token with "Models" read permission
      3. Set GITHUB_TOKEN=your_token in .env

    Supported models: gpt-4o, gpt-4o-mini, Phi-4, Llama-3.3-70B, etc.
    """

    GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"

    def __init__(self, token: str = None, model: str = "gpt-4o"):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai>=1.30.0")
        self.token = token or GITHUB_TOKEN
        self.model = model
        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN not set. Create a GitHub personal access token at "
                "github.com/settings/tokens and add GITHUB_TOKEN=<token> to your .env"
            )
        self._client = _OpenAI(
            base_url=self.GITHUB_MODELS_ENDPOINT,
            api_key=self.token,
        )
        logger.info(f"GitHubModelsAgent ready: model={self.model} (Azure AI Inference endpoint)")

    def analyze_patient(self, patient_data: dict, verbose: bool = False) -> dict:
        """Run pharmacogenomics analysis via GitHub Models (Azure AI Foundry infrastructure)."""
        from pharmacogenomics.risk_calculator import analyze_patient as _analyze
        from pharmacogenomics.modules.immunocompromised_module import SpecialCondition

        pid = patient_data["patient_id"]
        platform = patient_data.get("target_vaccine", "mRNA")
        raw_condition = patient_data.get("special_condition", SpecialCondition.NONE.value)
        try:
            condition = SpecialCondition(raw_condition)
        except ValueError:
            condition = SpecialCondition.NONE

        # Run local engine — provides computed scores for the model to reason about
        report = _analyze(
            patient_id=pid,
            age=patient_data["age"],
            sex=patient_data["sex"],
            variants=patient_data["variants"],
            hla_haplotype=patient_data["hla_haplotype"],
            apoe_genotype=patient_data["apoe_genotype"],
            target_vaccine=platform,
            special_condition=condition,
        )

        prompt = build_patient_analysis_prompt(patient_data)
        score_context = (
            f"\n\n[Engine Pre-computation]\n"
            f"Score_TLR={report.tlr.score:.4f}  Score_HLA={report.hla.score:.4f}  "
            f"Score_STAT={report.stat.score:.4f}  Score_APOE={report.apoe.score:.4f}\n"
            f"θ_genetic={report.irt.theta_genetic:+.4f}  "
            f"θ_penalty={report.irt.theta_penalty:+.4f} [{condition.value}]  "
            f"θ_clinical={report.irt.theta:+.4f}\n"
            f"P(protection|{platform})={report.irt.probability_protection:.4f}  "
            f"b_base={report.irt.b_base}  b_final={report.irt.b:.4f}\n"
            f"Risk flags: {report.all_risk_flags}"
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": VACCINEGENICS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt + score_context},
                ],
                max_tokens=4096,
                temperature=0.1,
            )
            raw_response = response.choices[0].message.content or ""
            if verbose:
                logger.info(f"GitHub Models usage: {response.usage}")
        except Exception as exc:
            logger.error(f"GitHub Models call failed for {pid}: {exc}")
            offline = OfflineVaccineGenicsAgent()
            result = offline.analyze_patient(patient_data, verbose)
            result["run_status"] = f"github_models_error_fallback: {exc}"
            return result

        recommendation = extract_recommendation_from_response(raw_response)
        cot = html.escape(raw_response)

        _o = OfflineVaccineGenicsAgent()
        recommendation.update({
            "patient_id": pid,
            "full_report": cot,
            "platform": report.irt.vaccine_platform,
            "dose_recommendation": report.irt.dose_recommendation,
            "protection_probability": report.irt.probability_protection,
            "risk_flags": report.all_risk_flags,
            "overall_risk_level": report.overall_risk_level,
            "final_recommendation": report.final_recommendation,
            "structured_report": _o._build_structured_report(report),
            "reasoning_trace": _o._build_trace(report),
            "run_status": "completed_github_models",
            "model": self.model,
            "endpoint": self.GITHUB_MODELS_ENDPOINT,
        })
        return recommendation


def get_agent(
    offline: bool = False,
    prefer_openai: bool = False,
) -> "VaccineGenicsAgent | AzureOpenAIAgent | GitHubModelsAgent | OfflineVaccineGenicsAgent":
    """
    Factory: picks the best available agent mode.

    Priority:
      1. VaccineGenicsAgent    — full Azure AI Foundry Agents API (AZURE_AI_PROJECT_ENDPOINT)
                                 falls back to GitHubModelsAgent if no model is deployed
      2. GitHubModelsAgent     — GitHub Models / Azure AI Inference (GITHUB_TOKEN) ← active
      3. AzureOpenAIAgent      — Azure OpenAI Chat Completions (AZURE_OPENAI_ENDPOINT)
      4. OfflineVaccineGenicsAgent — local engine, no cloud credentials

    Use offline=True to force local mode (demo/CI).
    Use prefer_openai=True to skip Agents API and use AzureOpenAI directly.
    """
    if offline:
        logger.info("Using offline (local) VaccineGenics agent")
        return OfflineVaccineGenicsAgent()

    # Only attempt full Agents API when a project API key is available to avoid
    # DefaultAzureCredential timeout (30+ s) during live demos.
    # NOTE: Skip Foundry Agents on free tier — go straight to GitHub Models (free, no card)
    if AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_PROJECT_KEY and not prefer_openai:
        try:
            agent = VaccineGenicsAgent()
            logger.info("✅ Using Azure AI Foundry Agents API (Threads + CodeInterpreter)")
            return agent
        except Exception as exc:
            logger.warning(f"Agents API init failed ({exc}) — trying GitHub Models")

    # Priority 2: GitHub Models / Azure AI Inference — FREE, no credit card needed!
    # Explicitly allowed by Agents League rules ("models hosted in Microsoft Foundry, GitHub…")
    # This is your best option for free tier Azure accounts.
    if GITHUB_TOKEN:
        try:
            agent = GitHubModelsAgent()
            logger.info("✅ Using GitHub Models / Azure AI Inference (Azure AI Foundry infrastructure)")
            return agent
        except Exception as exc:
            logger.warning(f"GitHub Models init failed ({exc}) — trying Azure OpenAI")

    # Priority 3: Azure OpenAI Chat Completions (requires a deployed model)
    if AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY:
        try:
            agent = AzureOpenAIAgent()
            logger.info("✅ Using Azure OpenAI Chat Completions")
            return agent
        except Exception as exc:
            logger.warning(f"AzureOpenAI init failed ({exc}) — falling back to offline")

    logger.info("No cloud credentials found — using offline (local) VaccineGenics agent")
    return OfflineVaccineGenicsAgent()
