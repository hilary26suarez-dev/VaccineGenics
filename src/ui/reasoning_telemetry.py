"""
Reasoning telemetry and evaluation scores panel for VaccineGenics.

Provides:
  render_reasoning_trace() — vertical agent-step timeline with latency, tools, PMIDs
  render_eval_scores()     — load & display eval_cases.json results with accuracy
"""

from __future__ import annotations

import json
import os
import time
import streamlit as st

# ── Colour map (mirrors app.py _COUNCIL_COLORS) ──────────────────────────────
_AGENT_COLORS = {
    "dr_genomico":       "#4a90d9",
    "dra_evidencia":     "#00c853",
    "ing_riesgo":        "#ffd600",
    "doc_clinico":       "#b22222",
    "critico":           "#ff7043",
    "doc_clinico_final": "#b22222",
}

_AGENT_TOOLS = {
    "dr_genomico":       ["GENETIC_VARIANT_MAPPER", "HLA_CLASSIFIER"],
    "dra_evidencia":     ["PUBMED_RETRIEVAL", "AZURE_AI_SEARCH"],
    "ing_riesgo":        ["IRT_4PL_ENGINE", "CODE_INTERPRETER"],
    "doc_clinico":       ["CLINICAL_SYNTHESIZER"],
    "critico":           ["ADVERSARIAL_CHECKER"],
    "doc_clinico_final": ["FOUNDRY_O4_MINI", "FINAL_SYNTHESIZER"],
}

# Simulated latencies (ms) for offline demo mode
_OFFLINE_LATENCIES = {
    "dr_genomico":       820,
    "dra_evidencia":     1540,
    "ing_riesgo":        390,
    "doc_clinico":       710,
    "critico":           620,
    "doc_clinico_final": 1850,
}


def render_reasoning_trace(council_session: dict) -> None:
    """
    Render a vertical timeline of each agent's contribution.

    council_session: dict with keys:
      "steps"    — list of agent message dicts (from CouncilMessage.to_dict())
      "patient"  — patient_id string
      "platform" — vaccine platform string
    """
    steps = council_session.get("steps", [])
    patient = council_session.get("patient", "?")
    platform = council_session.get("platform", "?")

    if not steps:
        st.info("Ejecuta el consejo de agentes para ver la telemetría de razonamiento.")
        return

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:1.2rem;">
  <div style="font-size:1.5rem;">🔬</div>
  <div>
    <div style="font-size:1rem;font-weight:700;color:#f1f5f9;">
      Árbol de Decisiones — Consejo de Agentes
    </div>
    <div style="font-size:0.78rem;color:#64748b;margin-top:1px;">
      Paciente: <strong style="color:#94a3b8;">{patient}</strong>
      &nbsp;·&nbsp; Plataforma: <strong style="color:#94a3b8;">{platform}</strong>
      &nbsp;·&nbsp; {len(steps)} turnos de debate
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    total_ms = sum(_OFFLINE_LATENCIES.get(m.get("agent", ""), 800) for m in steps)

    for i, msg in enumerate(steps):
        agent = msg.get("agent", "")
        name = msg.get("name", agent)
        avatar = msg.get("avatar", "🤖")
        role = msg.get("role", "")
        color = _AGENT_COLORS.get(agent, "#4a90d9")
        latency_ms = _OFFLINE_LATENCIES.get(agent, 800)
        tools = _AGENT_TOOLS.get(agent, [])
        citations = msg.get("citations", [])
        pmids = [c.get("pmid", "") for c in citations if c.get("pmid")]
        content_preview = (msg.get("content", "")[:180] + "…") if len(msg.get("content", "")) > 180 else msg.get("content", "")
        has_code = bool(msg.get("code_block"))

        # Tool badges
        tool_badges = " ".join(
            f'<span style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);'
            f'border-radius:4px;padding:1px 6px;font-size:9px;color:#94a3b8;font-family:monospace;">'
            f'{t}</span>'
            for t in tools
        )

        # PMID badges
        pmid_badges = " ".join(
            f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank" '
            f'style="background:rgba(0,229,255,0.08);border:1px solid rgba(0,229,255,0.2);'
            f'border-radius:4px;padding:1px 6px;font-size:9px;color:#4db8ff;'
            f'text-decoration:none;font-family:monospace;">PMID {pmid}</a>'
            for pmid in pmids
        )

        # Code interpreter badge
        code_badge = (
            '<span style="background:rgba(255,214,0,0.1);border:1px solid rgba(255,214,0,0.3);'
            'border-radius:4px;padding:1px 6px;font-size:9px;color:#ffd600;font-family:monospace;">'
            '🖥️ CODE</span>'
        ) if has_code else ""

        # Timeline connector
        connector = (
            '<div style="width:2px;height:16px;background:rgba(255,255,255,0.07);'
            'margin-left:15px;margin-top:0;margin-bottom:0;"></div>'
        ) if i < len(steps) - 1 else ""

        with st.expander(f"{avatar} {name} — {role}  ({latency_ms}ms)", expanded=(i == 0)):
            st.markdown(f"""
<div style="border-left:3px solid {color};padding-left:10px;margin-bottom:0.6rem;">
  <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-bottom:6px;">
    <span style="font-size:10px;color:{color};font-weight:700;
                 background:{color}15;border:1px solid {color}30;
                 border-radius:999px;padding:1px 8px;">{name}</span>
    <span style="font-size:9px;color:#64748b;font-family:monospace;">⏱ {latency_ms}ms</span>
    {tool_badges}
    {code_badge}
  </div>
  <div style="font-size:0.82rem;color:#cbd5e1;line-height:1.55;margin-bottom:6px;">
    {content_preview}
  </div>
  {('<div style="margin-top:5px;display:flex;flex-wrap:wrap;gap:4px;">' + pmid_badges + '</div>') if pmid_badges else ''}
</div>
""", unsafe_allow_html=True)

        st.markdown(connector, unsafe_allow_html=True)

    # Summary bar
    st.markdown(f"""
<div style="margin-top:1.2rem;padding:0.7rem 1rem;
            background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:8px;display:flex;gap:1.5rem;flex-wrap:wrap;">
  <div style="font-size:0.8rem;color:#64748b;">
    Agentes: <strong style="color:#94a3b8;">{len(steps)}</strong>
  </div>
  <div style="font-size:0.8rem;color:#64748b;">
    Latencia total (simulada): <strong style="color:#94a3b8;">{total_ms:,}ms</strong>
  </div>
  <div style="font-size:0.8rem;color:#64748b;">
    PMIDs citados: <strong style="color:#4db8ff;">
      {sum(len(m.get('citations', [])) for m in steps)}
    </strong>
  </div>
  <div style="font-size:0.8rem;color:#64748b;">
    Intervención crítica: <strong style="color:#ff7043;">
      {"Sí — recomendación revisada" if any(m.get("agent") == "critico" for m in steps) else "No"}
    </strong>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Evaluation panel ──────────────────────────────────────────────────────────

_EVALS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "evals", "eval_cases.json"
)


def _load_eval_cases() -> list:
    """Load eval_cases.json. Returns empty list if file not found."""
    try:
        with open(_EVALS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("cases", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _run_single_eval(case: dict) -> dict:
    """
    Run a single eval case through the pharmacogenomics engine.
    Returns the case dict augmented with actual_platform and is_match.
    """
    try:
        import sys
        _src = os.path.join(os.path.dirname(__file__), "..")
        if _src not in sys.path:
            sys.path.insert(0, _src)
        from pharmacogenomics.risk_calculator import analyze_patient
        from pharmacogenomics.modules.immunocompromised_module import SpecialCondition

        profile = case.get("profile", {})
        condition_slug = profile.get("special_condition", "none")
        try:
            condition = SpecialCondition(condition_slug)
        except ValueError:
            condition = SpecialCondition.NONE

        # Build minimal variants dict from profile
        variants: dict = {}
        tlr4 = profile.get("tlr4_variant", "rs4986790_wt")
        if tlr4 and tlr4 != "rs4986790_wt":
            variants["rs4986790"] = {"genotype": "A/G", "risk_allele": "A", "gene": "TLR4"}

        hla_str = profile.get("hla_haplotype", "HLA-A*02:01,HLA-DRB1*07:01")
        # Build nested HLA dict required by the engine
        alleles = [h.strip() for h in hla_str.split(",") if h.strip()]
        class_i: dict = {}
        class_ii: dict = {}
        for a in alleles:
            base = a.split("*")[0]
            gene = base.replace("HLA-", "")
            if gene in ("A", "B", "C"):
                class_i.setdefault(base, []).append(a)
            else:
                class_ii.setdefault(base, []).append(a)
        if not class_i:
            class_i = {"HLA-A": ["HLA-A*02:01"]}
        if not class_ii:
            class_ii = {"HLA-DRB1": ["HLA-DRB1*07:01"]}
        hla_dict = {"class_I": class_i, "class_II": class_ii}
        target_vaccine = profile.get("target_vaccine", "mRNA")

        report = analyze_patient(
            patient_id=case.get("case_id", "EVAL"),
            age=profile.get("age", 35),
            sex=profile.get("sex", "Male"),
            variants=variants,
            hla_haplotype=hla_dict,
            apoe_genotype=profile.get("apoe_genotype", "ε3/ε3"),
            target_vaccine=target_vaccine,
            special_condition=condition,
            run_cross_platform=True,
        )
        report_dict = report.to_dict()

        # Determine best platform
        cp = report_dict.get("cross_platform", [])
        best = sorted(
            [r for r in cp if not r.get("contraindicated", False)],
            key=lambda x: x.get("rank", 99)
        )
        actual_platform = best[0].get("platform", "mRNA") if best else "mRNA"
        # Normalize platform name
        _plat_map = {
            "mRNA": "mRNA-LNP",
            "adenoviral_vector": "Adenoviral",
            "protein_subunit": "Subunidad Proteica",
        }
        actual_normalized = _plat_map.get(actual_platform, actual_platform)
        expected = case.get("expected_platform", "")
        is_match = actual_normalized == expected
        actual_p = best[0].get("probability_protection", 0.0) if best else 0.0

        return {
            **case,
            "actual_platform": actual_normalized,
            "actual_p_protection": actual_p,
            "is_match": is_match,
            "error": None,
        }
    except Exception as exc:
        return {**case, "actual_platform": "ERROR", "actual_p_protection": 0.0,
                "is_match": False, "error": str(exc)}


@st.cache_data(show_spinner=False)
def _cached_eval_results() -> list:
    cases = _load_eval_cases()
    if not cases:
        return []
    return [_run_single_eval(c) for c in cases]


def render_eval_scores() -> None:
    """
    Load eval cases, run them through the engine, and display results + accuracy.
    """
    st.markdown("""
<div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:1.2rem;">
  <div style="font-size:1.5rem;">✅</div>
  <div>
    <div style="font-size:1rem;font-weight:700;color:#f1f5f9;">
      Validation Set — 8 Casos Sintéticos
    </div>
    <div style="font-size:0.78rem;color:#64748b;margin-top:1px;">
      Objetivo: accuracy ≥ 80% en recomendación de plataforma vacunal
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    cases = _load_eval_cases()
    if not cases:
        st.warning("No se encontró `evals/eval_cases.json`. Verifica la ruta del archivo.")
        return

    with st.spinner("Corriendo eval set…"):
        results = _cached_eval_results()

    correct = sum(1 for r in results if r.get("is_match", False))
    total = len(results)
    accuracy = correct / total if total else 0.0

    acc_color = "#00c853" if accuracy >= 0.80 else "#ff5252"
    acc_icon = "✅" if accuracy >= 0.80 else "❌"

    # Accuracy banner
    st.markdown(f"""
<div style="padding:0.8rem 1.2rem;background:rgba(255,255,255,0.02);
            border:2px solid {acc_color};border-radius:10px;
            display:flex;align-items:center;gap:1.5rem;margin-bottom:1.2rem;
            box-shadow:0 0 12px {acc_color}20;">
  <div style="font-size:2rem;">{acc_icon}</div>
  <div>
    <div style="font-size:1.4rem;font-weight:800;color:{acc_color};">
      {accuracy:.1%} accuracy
    </div>
    <div style="font-size:0.82rem;color:#94a3b8;margin-top:2px;">
      {correct}/{total} casos correctos
      &nbsp;·&nbsp;
      {"Meta ≥ 80% alcanzada" if accuracy >= 0.80 else "Meta ≥ 80% no alcanzada"}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Per-case results table
    rows_html = ""
    for r in results:
        case_id = r.get("case_id", "?")
        expected = r.get("expected_platform", "?")
        actual = r.get("actual_platform", "?")
        exp_p = r.get("expected_p_protection", 0.0)
        act_p = r.get("actual_p_protection", 0.0)
        ok = r.get("is_match", False)
        explanation = r.get("explanation", "")
        err = r.get("error")
        status_icon = "✅" if ok else "❌"
        status_color = "#00c853" if ok else "#ff5252"

        rows_html += f"""
<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
  <td style="padding:6px 8px;font-family:monospace;font-size:0.8rem;color:#94a3b8;">{case_id}</td>
  <td style="padding:6px 8px;font-size:0.8rem;color:#e2e8f0;font-weight:600;">{expected}</td>
  <td style="padding:6px 8px;font-size:0.8rem;color:#e2e8f0;">{actual}</td>
  <td style="padding:6px 8px;font-size:0.8rem;color:#94a3b8;">{exp_p:.0%}</td>
  <td style="padding:6px 8px;font-size:0.8rem;color:#94a3b8;">{act_p:.0%}</td>
  <td style="padding:6px 8px;text-align:center;font-size:1rem;color:{status_color};">{status_icon}</td>
  <td style="padding:6px 8px;font-size:0.75rem;color:#64748b;max-width:200px;">{explanation if not err else f'ERROR: {err}'}</td>
</tr>"""

    st.markdown(f"""
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
            border-radius:8px;overflow-x:auto;">
  <table style="width:100%;border-collapse:collapse;font-family:sans-serif;">
    <thead>
      <tr style="background:rgba(255,255,255,0.04);">
        <th style="padding:6px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;">Caso</th>
        <th style="padding:6px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;">Esperado</th>
        <th style="padding:6px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;">Obtenido</th>
        <th style="padding:6px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;">P(esp.)</th>
        <th style="padding:6px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;">P(real)</th>
        <th style="padding:6px 8px;text-align:center;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;">OK</th>
        <th style="padding:6px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;">Contexto</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
""", unsafe_allow_html=True)

    st.caption(
        "Los casos de validación son sintéticos. "
        "La plataforma recomendada se determina por la simulación IRT cross-platform del motor."
    )
