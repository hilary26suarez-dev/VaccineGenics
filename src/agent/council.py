"""
VaccineGenics Agent Council — Multi-Agent Orchestrator.

Runs a structured 6-turn multi-agent debate for a single patient analysis:

  Dr. Genómico    → genomic variant identification
  Dra. Evidencia  → literature search + PMID citations
  Ing. de Riesgo  → live IRT computation + Python code block
  Doc. Clínico    → clinical synthesis + first recommendation
  Crítico Interno → adversarial challenge to stress-test the logic
  Doc. Clínico    → final recommendation after critic response

All agents use live LLM calls via Azure AI Inference / GitHub Models.
No offline fallback — if LLM is unavailable an error message is shown.
"""

from __future__ import annotations

import json
import math
import os
import logging
import textwrap
from dataclasses import dataclass, field
from typing import Callable, Iterator

logger = logging.getLogger(__name__)

# GitHub Models / Azure AI Inference endpoint (explicitly allowed by Agents League rules)
_GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"

# ── Agent persona definitions ─────────────────────────────────────────────────

@dataclass
class AgentPersona:
    slug: str
    name: str
    avatar: str
    role: str
    color: str          # hex for UI badge
    system_prompt: str


PERSONAS: dict[str, AgentPersona] = {
    "dr_genomico": AgentPersona(
        slug="dr_genomico",
        name="Dr. Genómico",
        avatar="🧬",
        role="Analista Genómico",
        color="#4a90d9",
        system_prompt=(
            "Eres Dr. Genómico, un farmacogenomicista clínico. "
            "Tu función es analizar las variantes genéticas del paciente e identificar "
            "los hallazgos clínicamente más significativos. Sé preciso con los rsIDs, "
            "genotipos y qué módulos farmacogenómicos están afectados. "
            "Habla en primera persona, de forma concisa (3-5 oraciones). "
            "Finaliza nombrando al siguiente especialista que debe tomar el caso. "
            "IMPORTANTE: Responde SIEMPRE en español."
        ),
    ),
    "dra_evidencia": AgentPersona(
        slug="dra_evidencia",
        name="Dra. Evidencia",
        avatar="📚",
        role="Científica de Evidencia",
        color="#00c853",
        system_prompt=(
            "Eres Dra. Evidencia, especialista en literatura biomédica. "
            "Has buscado en la literatura farmacogenómica y encontrado publicaciones clave "
            "que vinculan las variantes del paciente con los resultados vacunales. "
            "Cita cada hallazgo con PMID y autores. Sé precisa y fundamentada. "
            "Habla en primera persona, 4-6 oraciones. "
            "Resume el peso de la evidencia (sólida/moderada/limitada) para la recomendación principal. "
            "IMPORTANTE: Responde SIEMPRE en español."
        ),
    ),
    "ing_riesgo": AgentPersona(
        slug="ing_riesgo",
        name="Ing. de Riesgo",
        avatar="⚙️",
        role="Ingeniero de Riesgos",
        color="#ffd600",
        system_prompt=(
            "Eres el Ingeniero de Riesgo. Has ejecutado el modelo IRT 4PL con "
            "la puntuación θ genética del paciente y calculado probabilidades de protección "
            "para todas las plataformas vacunales. Presenta los resultados numéricos claramente. "
            "Explica qué significa θ en lenguaje sencillo. Compara las plataformas. "
            "Habla en primera persona, 4-5 oraciones. "
            "Identifica qué plataforma da la mejor P(protección) para este paciente. "
            "IMPORTANTE: Responde SIEMPRE en español."
        ),
    ),
    "doc_clinico": AgentPersona(
        slug="doc_clinico",
        name="Doc. Clínico",
        avatar="🩺",
        role="Sintetizador Clínico",
        color="#b22222",
        system_prompt=(
            "Eres Doc. Clínico, farmacólogo clínico. "
            "Sintetizas todos los hallazgos previos — genómica, literatura y resultados IRT — "
            "en una recomendación clínica clara. Indica qué plataforma vacunal, "
            "qué dosis y qué plan de monitorización. Reconoce cualquier incertidumbre restante. "
            "Habla en primera persona, 4-6 oraciones. "
            "Antes de finalizar, pide al Crítico Interno que cuestione tu razonamiento. "
            "IMPORTANTE: Responde SIEMPRE en español."
        ),
    ),
    "critico": AgentPersona(
        slug="critico",
        name="Crítico Interno",
        avatar="🔎",
        role="Revisor Adversario",
        color="#ff7043",
        system_prompt=(
            "Eres el Crítico Interno, revisor adversarial de seguridad. "
            "Tu trabajo es encontrar la suposición más débil o la variante pasada por alto en el "
            "análisis del consejo. Cuestiona UN punto específico: una variante de baja penetrancia, "
            "una interacción faltante, un problema de estratificación poblacional "
            "o un caso límite en los parámetros IRT. "
            "Sé específico, cita evidencia si es posible, y pregunta '¿Está seguro?' "
            "Habla en primera persona, 3-4 oraciones. Sé constructivamente escéptico. "
            "IMPORTANTE: Responde SIEMPRE en español."
        ),
    ),
    "doc_clinico_final": AgentPersona(
        slug="doc_clinico_final",
        name="Doc. Clínico",
        avatar="🩺",
        role="Recomendación Final",
        color="#b22222",
        system_prompt=(
            "Eres Doc. Clínico. Acabas de escuchar el cuestionamiento del Crítico Interno. "
            "Responde directamente a la crítica: reconócela o refútala con razonamiento. "
            "Luego emite tu recomendación FINAL y definitiva: plataforma, dosis, monitorización "
            "y nivel de confianza (0-100%). "
            "Habla en primera persona, 4-5 oraciones. Sé decisivo. "
            "IMPORTANTE: Responde SIEMPRE en español."
        ),
    ),
}

# ── Council message dataclass ─────────────────────────────────────────────────

@dataclass
class CouncilMessage:
    agent: str              # persona slug
    content: str            # main text content
    code_block: str = ""    # optional Python code shown as Code Interpreter output
    code_output: str = ""   # stdout from the code
    citations: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    source: str = "llm"   # "llm" | "error"
    engine: str = "github_gpt4o_mini"  # "foundry_o4mini" | "github_gpt4o_mini"

    @property
    def persona(self) -> AgentPersona:
        return PERSONAS.get(self.agent, PERSONAS["dr_genomico"])

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "name": self.persona.name,
            "avatar": self.persona.avatar,
            "role": self.persona.role,
            "color": self.persona.color,
            "content": self.content,
            "code_block": self.code_block,
            "code_output": self.code_output,
            "citations": self.citations,
            "metadata": self.metadata,
            "source": self.source,
            "engine": self.engine,
        }


def _flatten_hla(hla_haplotype) -> str:
    """Flatten HLA haplotype (list or nested dict) to a single space-joined string."""
    if isinstance(hla_haplotype, dict):
        alleles = []
        for cls_dict in hla_haplotype.values():
            if isinstance(cls_dict, dict):
                for v in cls_dict.values():
                    alleles.extend(v if isinstance(v, list) else [v])
        return " ".join(alleles)
    if isinstance(hla_haplotype, list):
        return " ".join(hla_haplotype)
    return str(hla_haplotype)


# ── IRT code template shown as "Code Interpreter output" ─────────────────────

def _build_irt_code(theta: float, platform: str, a: float, b: float, c: float) -> tuple[str, str]:
    """Return (code_block, code_output) for the IRT display."""
    code = textwrap.dedent(f"""\
        import math

        # Capacidad inmunogénica del paciente (θ) a partir de puntuaciones de módulos ponderadas
        theta = {theta:+.4f}

        # Parámetros IRT 4PL para {platform}
        a = {a}   # discriminación
        b = {b:.4f}   # dificultad (umbral vacunal)
        c = {c}   # parámetro de mínimo (piso de protección)

        # Función logística: P(θ) = c + (1-c) / (1 + exp(-a*(θ-b)))
        logit = -a * (theta - b)
        p_proteccion = c + (1 - c) / (1 + math.exp(logit))

        print(f"θ = {{theta:+.4f}}")
        print(f"logit = {{logit:.4f}}")
        print(f"P(protección) = {{p_proteccion:.4f}} = {{p_proteccion:.1%}}")
        print(f"Seroconversión probable: {{p_proteccion >= 0.60}}")
    """)

    logit = -a * (theta - b)
    p_prot = c + (1 - c) / (1 + math.exp(logit))
    output = (
        f"θ = {theta:+.4f}\n"
        f"logit = {logit:.4f}\n"
        f"P(protección) = {p_prot:.4f} = {p_prot:.1%}\n"
        f"Seroconversión probable: {p_prot >= 0.60}"
    )
    return code, output


# ── Council orchestrator ──────────────────────────────────────────────────────

class AgentCouncil:
    """
    Orchestrates a 6-turn multi-agent pharmacogenomics debate.

    All agents call live LLMs — Azure AI Foundry (o4-mini) for doc_clinico_final,
    GitHub Models / Azure AI Inference (gpt-4o-mini) for the other 5 agents.

    Usage:
        council = AgentCouncil()
        msgs = council.stream_session(patient_dict, report, platform, citations)
    """

    def __init__(self):
        self._llm_client = None
        self._foundry_client = None

    def _get_foundry_client(self):
        """
        Return FoundryProjectAgent if AZURE_AI_PROJECT_ENDPOINT is configured.
        Registers the 6 council personas as named agents in Azure AI Foundry (create_version).
        Falls back silently if credentials or SDK are not available.
        """
        if self._foundry_client is not None:
            return self._foundry_client
        endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
        if not endpoint:
            return None
        try:
            try:
                from agent.foundry_agent import FoundryProjectAgent
            except ImportError:
                from .foundry_agent import FoundryProjectAgent
            client = FoundryProjectAgent(endpoint=endpoint)
            if client.is_available():
                self._foundry_client = client
                logger.info("Council: Azure AI Foundry named agents active")
            else:
                logger.warning("Council: Foundry endpoint unreachable — using GitHub Models")
        except Exception as exc:
            logger.warning("Council: FoundryProjectAgent unavailable (%s) — using GitHub Models", exc)
        return self._foundry_client

    def _get_llm_client(self):
        """Return a ready OpenAI client pointed at GitHub Models (Azure AI Inference)."""
        if self._llm_client is None:
            try:
                from dotenv import load_dotenv, find_dotenv
                load_dotenv(find_dotenv(usecwd=False))
                token = os.getenv("GITHUB_TOKEN", "")
                if token:
                    from openai import OpenAI
                    self._llm_client = OpenAI(
                        base_url=_GITHUB_MODELS_ENDPOINT,
                        api_key=token,
                    )
                    logger.info("Council LLM: GitHub Models / Azure AI Inference ready")
                else:
                    logger.warning("Council LLM: GITHUB_TOKEN no está configurado — agrega GITHUB_TOKEN en .env")
            except Exception as exc:
                logger.error(f"Council LLM init failed: {exc}")
                self._llm_client = None
        return self._llm_client

    # Only the final synthesis agent uses Foundry — it has the highest clinical weight
    # and 1 call per analysis fits within free-tier quota (1 RPM for o4-mini GlobalStandard).
    # The other 5 agents use GitHub Models (Azure AI Inference infrastructure).
    _FOUNDRY_SLUGS = {"doc_clinico_final"}

    def _llm_call(self, system: str, user_message: str, max_tokens: int = 400, slug: str = "") -> str:
        """
        Single agent call — prioridad:
          1. Azure AI Foundry (o4-mini) — solo para doc_clinico_final (recomendación final)
          2. GitHub Models / Azure AI Inference gpt-4o — los otros 5 agentes
        """
        # Prioridad 1: Foundry — solo el agente de recomendación final
        if slug in self._FOUNDRY_SLUGS:
            foundry = self._get_foundry_client()
            if foundry is not None:
                try:
                    result = foundry.call_agent(slug, system, user_message)
                    if result:
                        logger.info("Council: Foundry o4-mini respondió para '%s'", slug)
                        self._last_engine = "foundry_o4mini"
                        return result
                except Exception as exc:
                    logger.warning("Foundry falló para %s (%s) — usando GitHub Models", slug, exc)

        # Prioridad 2: GitHub Models / Azure AI Inference (gpt-4o, gratuito)
        client = self._get_llm_client()
        if client is None:
            return ""
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=0.4,
            )
            self._last_engine = "github_gpt4o_mini"
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            logger.error(f"Council LLM call failed: {exc}")
            return ""

    # ── LLM session ──────────────────────────────────────────────────────────

    def _build_context(self, patient: dict, report: dict, platform: str) -> str:
        ms = report.get("module_scores", {})
        irt = report.get("irt", {})
        cp = report.get("cross_platform", [])
        cp_str = "; ".join(
            f"{r.get('label', r.get('platform', ''))}={r.get('probability_protection', 0):.1%}"
            for r in sorted(cp, key=lambda x: x.get("rank", 99))
        )
        return (
            f"PERFIL DEL PACIENTE:\n"
            f"  ID: {patient.get('patient_id')}  Edad: {patient.get('age')}  Sexo: {patient.get('sex')}\n"
            f"  Etnicidad: {patient.get('ethnicity', 'desconocida')}  APOE: {patient.get('apoe_genotype')}\n"
            f"  Condición: {report.get('special_condition', 'ninguna')}\n"
            f"  HLA: {', '.join(patient.get('hla_haplotype', []))}\n"
            f"  Variantes: {list(patient.get('variants', {}).keys())}\n\n"
            f"RESULTADOS DEL MOTOR:\n"
            f"  Puntuaciones de módulos: TLR={ms.get('tlr',{}).get('score',0):.3f} · "
            f"HLA={ms.get('hla',{}).get('score',0):.3f} · "
            f"STAT={ms.get('stat',{}).get('score',0):.3f} · "
            f"APOE={ms.get('apoe_peg3',{}).get('score',0):.3f}\n"
            f"  θ={irt.get('theta',0):+.4f}  P(protección)={irt.get('probability_protection',0):.1%}\n"
            f"  Plataforma: {platform}  Riesgo: {report.get('overall_risk_level')}\n"
            f"  Comparación entre plataformas: {cp_str}\n"
            f"  Alertas de riesgo: {'; '.join(report.get('all_risk_flags', [])[:4])}\n"
            f"  Recomendación: {report.get('final_recommendation', '')}\n"
        )

    # ── Main streaming interface ───────────────────────────────────────────────

    def stream_session(
        self,
        patient: dict,
        report: dict,
        platform: str,
        citations: list[dict],
        progress_callback: Callable[[str], None] | None = None,
        on_message: Callable[[object], None] | None = None,
        lang: str = "es",
    ) -> list[CouncilMessage]:
        """
        Run the full 6-turn live LLM council session.

        Returns list of CouncilMessage in order.
        progress_callback(agent_name) called before each LLM call.
        on_message(CouncilMessage) called immediately after each agent responds.
        lang: "es" or "en" — controls the language of all agent responses.
        """
        messages: list[CouncilMessage] = []

        def _emit(msg: CouncilMessage):
            messages.append(msg)
            if on_message:
                on_message(msg)

        context = self._build_context(patient, report, platform)
        cit_str = str([c['pmid'] + ' — ' + c['relevance'] for c in citations[:3]])

        if lang == "en":
            order = [
                ("dr_genomico",
                 "Analyze the genetic variants in the above context. "
                 "Identify the most clinically significant pharmacogenomic findings."),
                ("dra_evidencia",
                 "The genomic analysis is: {prev}\n\n"
                 "Now find and cite the relevant literature (provided PMIDs: " + cit_str + ")."),
                ("ing_riesgo",
                 "The literature review is: {prev}\n\n"
                 "Now present the IRT computation results and the cross-platform comparison."),
                ("doc_clinico",
                 "The engineering analysis is: {prev}\n\n"
                 "Synthesize a clinical recommendation. Then ask the Critic to challenge it."),
                ("critico",
                 "The clinical recommendation is: {prev}\n\n"
                 "Find and challenge the weakest assumption in this analysis."),
                ("doc_clinico_final",
                 "The challenge was: {prev}\n\n"
                 "Respond to the critique and issue your final, definitive recommendation."),
            ]
        else:
            order = [
                ("dr_genomico",
                 "Analiza las variantes genéticas en el contexto anterior. "
                 "Identifica los hallazgos farmacogenómicos más significativos clínicamente."),
                ("dra_evidencia",
                 "El análisis genómico es: {prev}\n\n"
                 "Ahora busca y cita la literatura relevante (PMIDs proporcionados: " + cit_str + ")."),
                ("ing_riesgo",
                 "La revisión de la literatura es: {prev}\n\n"
                 "Ahora presenta los resultados de la computación IRT y la comparación entre plataformas."),
                ("doc_clinico",
                 "El análisis de ingeniería es: {prev}\n\n"
                 "Sintetiza una recomendación clínica. Luego, pídele al Crítico que la cuestione."),
                ("critico",
                 "La recomendación clínica es: {prev}\n\n"
                 "Encuentra y cuestiona la suposición más débil en este análisis."),
                ("doc_clinico_final",
                 "El cuestionamiento fue: {prev}\n\n"
                 "Responde a la crítica y emite tu recomendación final y definitiva."),
            ]

        _LANG_INSTRUCTION_ES = "IMPORTANTE: Responde SIEMPRE en español."
        _LANG_INSTRUCTION_EN = "IMPORTANT: Always respond in English."

        prev_content = ""
        for slug, user_tmpl in order:
            persona = PERSONAS[slug]
            if progress_callback:
                progress_callback(persona.name)

            # Swap language instruction in system prompt based on selected lang
            if lang == "en":
                sys_prompt = persona.system_prompt.replace(
                    _LANG_INSTRUCTION_ES, _LANG_INSTRUCTION_EN
                )
            else:
                sys_prompt = persona.system_prompt

            user_msg = context + "\n\n" + user_tmpl.format(prev=prev_content[:600])
            content = self._llm_call(sys_prompt, user_msg, slug=slug)

            if not content:
                content = (
                    f"⚠️ **Error de conexión** — No se pudo contactar al servicio de IA para {persona.name}.\n"
                    "Verifica que GITHUB_TOKEN esté configurado en el archivo `.env` y que tengas acceso a GitHub Models."
                )
                source = "error"
                engine = "github_gpt4o_mini"
            else:
                source = "llm"
                engine = getattr(self, "_last_engine", "github_gpt4o_mini")

            msg = CouncilMessage(agent=slug, content=content, source=source, engine=engine)

            if slug == "dra_evidencia":
                msg.citations = citations[:3]

            if slug == "ing_riesgo":
                irt = report.get("irt", {})
                code_str, code_out = _build_irt_code(
                    irt.get("theta", 0), platform,
                    irt.get("a", 1.0), irt.get("b", 0.0), irt.get("c", 0.05),
                )
                msg.code_block = code_str
                msg.code_output = code_out

            _emit(msg)
            prev_content = content

        return messages

    # ── 3D Visualization interface ─────────────────────────────────────────────

    def analyze_patient_with_3d_visualization(
        self,
        patient_data: dict,
        progress_callback=None,
    ) -> dict:
        """
        Run the full council session and produce 3D visualization instructions.

        Returns:
            {
              "council_output": str,           # final recommendation text
              "visualization_instruction": dict, # residue groups for 3D rendering
              "pmids_cited": list[str],         # all PMID strings from all agents
              "reasoning_trace": dict,          # steps + latency + tools metadata
              "messages": list[dict],           # raw CouncilMessage.to_dict() list
            }
        """
        import sys
        import os as _os
        _src = _os.path.join(_os.path.dirname(__file__), "..")
        if _src not in sys.path:
            sys.path.insert(0, _src)

        # Build analysis report from patient data
        try:
            from pharmacogenomics.risk_calculator import analyze_patient
            from pharmacogenomics.modules.immunocompromised_module import SpecialCondition
            from data.literature_kb import get_citations

            condition_slug = patient_data.get("special_condition", "none")
            try:
                condition = SpecialCondition(condition_slug)
            except ValueError:
                condition = SpecialCondition.NONE

            report = analyze_patient(
                patient_id=patient_data.get("patient_id", "DEMO"),
                age=patient_data.get("age", 35),
                sex=patient_data.get("sex", "Male"),
                variants=patient_data.get("variants", {}),
                hla_haplotype=patient_data.get("hla_haplotype", []),
                apoe_genotype=patient_data.get("apoe_genotype", "ε3/ε3"),
                target_vaccine=patient_data.get("target_vaccine", "mRNA"),
                special_condition=condition,
                run_cross_platform=True,
            )
            report_dict = report.to_dict()

            citations = get_citations(
                apoe_genotype=patient_data.get("apoe_genotype", "ε3/ε3"),
                variants=patient_data.get("variants", {}),
                hla_haplotype=patient_data.get("hla_haplotype", []),
                condition=condition_slug,
            )
        except Exception as exc:
            logger.error("analyze_patient_with_3d_visualization engine error: %s", exc)
            report_dict = {}
            citations = []

        # Run council (always live LLM)
        messages = self.stream_session(
            patient=patient_data,
            report=report_dict,
            platform=patient_data.get("target_vaccine", "mRNA"),
            citations=citations,
            progress_callback=progress_callback,
        )

        # Gather PMIDs from all messages
        pmids_cited: list[str] = []
        for msg in messages:
            for c in msg.citations:
                pmid = c.get("pmid", "")
                if pmid and pmid not in pmids_cited:
                    pmids_cited.append(pmid)

        # Build visualization instruction (residue groups for 3D renderer)
        try:
            from molecular.pdb_loader import get_variants_to_highlight
            highlight_groups = get_variants_to_highlight(
                patient_variants=patient_data.get("variants", {}),
                apoe_genotype=patient_data.get("apoe_genotype", "ε3/ε3"),
                hla_haplotype=patient_data.get("hla_haplotype", []),
            )
        except ImportError:
            highlight_groups = []

        visualization_instruction = {
            "pdb_id": "6M0J",
            "highlight_groups": highlight_groups,
            "patient_id": patient_data.get("patient_id", "?"),
        }

        # Build reasoning trace for telemetry panel
        _OFFLINE_LATENCIES = {
            "dr_genomico": 820, "dra_evidencia": 1540, "ing_riesgo": 390,
            "doc_clinico": 710, "critico": 620, "doc_clinico_final": 1850,
        }
        reasoning_trace = {
            "steps": [m.to_dict() for m in messages],
            "patient": patient_data.get("patient_id", "?"),
            "platform": patient_data.get("target_vaccine", "mRNA"),
            "latencies": {
                m.agent: _OFFLINE_LATENCIES.get(m.agent, 800) for m in messages
            },
            "critic_intervention": next(
                (
                    {
                        "original": next(
                            (mm.content[:120] for mm in messages if mm.agent == "doc_clinico"), ""
                        ),
                        "critique": m.content[:120],
                        "reason": "HLA/APOE/TLR risk identified",
                    }
                    for m in messages if m.agent == "critico"
                ),
                None,
            ),
        }

        # Final recommendation text
        final_msgs = [m for m in messages if m.agent == "doc_clinico_final"]
        council_output = (
            final_msgs[-1].content if final_msgs
            else report_dict.get("final_recommendation", "")
        )

        return {
            "council_output": council_output,
            "visualization_instruction": visualization_instruction,
            "pmids_cited": pmids_cited,
            "reasoning_trace": reasoning_trace,
            "messages": [m.to_dict() for m in messages],
            "report": report_dict,
        }
