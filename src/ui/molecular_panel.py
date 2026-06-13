"""
Streamlit molecular visualization panel for VaccineGenics.

Renders the SARS-CoV-2 Spike RBD 3D structure with per-patient variant
highlights, a variant-impact table with PMID links, and a narrative explanation.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

try:
    from molecular.pdb_loader import get_variants_to_highlight, generate_3d_visualization_script
    _HAS_LOADER = True
except ImportError:
    _HAS_LOADER = False


def render_3d_spike_interaction(patient_dict: dict, height: int = 540) -> None:
    """
    Render interactive 3D Spike RBD + ACE2 with variant-specific residue highlights.

    Uses 3Dmol.js via CDN (no extra Python packages required).
    """
    if not _HAS_LOADER:
        st.warning("molecular.pdb_loader not importable — check PYTHONPATH.")
        return

    apoe = patient_dict.get("apoe_genotype", "ε3/ε3")
    variants = patient_dict.get("variants", {})
    hla = patient_dict.get("hla_haplotype", [])

    highlight_groups = get_variants_to_highlight(
        patient_variants=variants,
        apoe_genotype=apoe,
        hla_haplotype=hla,
    )

    html = generate_3d_visualization_script(
        pdb_id="6M0J",
        highlight_groups=highlight_groups,
        height=height,
    )
    components.html(html, height=height, scrolling=False)


def render_variant_impact_table(patient_dict: dict, irt_result: dict) -> None:
    """
    Render a compact table: Variante → Residuos PDB → Impacto clínico → PMID.
    """
    if not _HAS_LOADER:
        return

    from molecular.pdb_loader import get_variants_to_highlight

    apoe = patient_dict.get("apoe_genotype", "ε3/ε3")
    variants = patient_dict.get("variants", {})
    hla = patient_dict.get("hla_haplotype", [])

    groups = get_variants_to_highlight(
        patient_variants=variants,
        apoe_genotype=apoe,
        hla_haplotype=hla,
    )

    if not groups:
        st.caption("Sin variantes moleculares de riesgo mapeadas para este perfil.")
        return

    rows_html = ""
    for g in groups:
        color = g.get("color", "#ccc")
        label = g.get("label", "")
        residues = g.get("critical_residues", [])
        annotation = g.get("annotation", "")
        pmid = g.get("pmid", "")
        chain = g.get("chain", "E")
        chain_label = "Spike RBD" if chain == "E" else "ACE2"
        res_str = ", ".join(str(r) for r in residues[:5]) + ("…" if len(residues) > 5 else "")
        pmid_link = (
            f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank" '
            f'style="color:#4db8ff;font-weight:600;">PMID {pmid}</a>'
            if pmid else "—"
        )
        rows_html += f"""
<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
  <td style="padding:6px 8px;">
    <span style="display:inline-block;width:8px;height:8px;border-radius:50%;
                 background:{color};margin-right:5px;"></span>
    <strong style="color:{color};font-size:0.82rem;">{label}</strong>
  </td>
  <td style="padding:6px 8px;color:#94a3b8;font-size:0.78rem;font-family:monospace;">
    {chain_label}: {res_str}
  </td>
  <td style="padding:6px 8px;color:#e2e8f0;font-size:0.78rem;">{annotation}</td>
  <td style="padding:6px 8px;font-size:0.78rem;">{pmid_link}</td>
</tr>"""

    st.markdown(f"""
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
            border-radius:8px;overflow:hidden;margin-top:0.5rem;">
  <div style="padding:6px 10px;background:rgba(0,229,255,0.05);
              border-bottom:1px solid rgba(0,229,255,0.1);
              font-size:10px;color:#00e5ff;font-weight:700;
              text-transform:uppercase;letter-spacing:0.08em;">
    Evidencia Molecular
  </div>
  <table style="width:100%;border-collapse:collapse;font-family:sans-serif;">
    <thead>
      <tr style="background:rgba(255,255,255,0.03);">
        <th style="padding:5px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Variante</th>
        <th style="padding:5px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Residuos PDB</th>
        <th style="padding:5px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Impacto</th>
        <th style="padding:5px 8px;text-align:left;font-size:9px;color:#475569;
                   text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Ref.</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
""", unsafe_allow_html=True)


def explain_3d_scene(agent_recommendation: str, patient_dict: dict) -> None:
    """
    Display a short scientific narrative linking the 3D scene to the recommendation.
    """
    if not _HAS_LOADER:
        return

    from molecular.pdb_loader import get_variants_to_highlight

    apoe = patient_dict.get("apoe_genotype", "ε3/ε3")
    variants = patient_dict.get("variants", {})
    hla = patient_dict.get("hla_haplotype", [])
    patient_id = patient_dict.get("patient_id", "este paciente")

    groups = get_variants_to_highlight(
        patient_variants=variants,
        apoe_genotype=apoe,
        hla_haplotype=hla,
    )

    if not groups:
        narrative = (
            f"El perfil molecular de **{patient_id}** no muestra variantes de alto riesgo "
            "mapeadas en la estructura Spike-ACE2. La recomendación se basa principalmente "
            "en las puntuaciones IRT del sistema inmune."
        )
    else:
        labels = [g.get("label", "") for g in groups]
        narrative = (
            f"La escena 3D muestra la interfaz Spike RBD–ACE2 (PDB 6M0J). "
            f"Los residuos resaltados para **{patient_id}** corresponden a: "
            f"**{', '.join(labels)}**. "
            "Las esferas de colores indican posiciones aminoacídicas afectadas por las variantes "
            "farmacogenómicas. Esta topografía molecular apoya la recomendación del consejo."
        )

    st.caption(narrative)
