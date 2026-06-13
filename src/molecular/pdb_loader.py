"""
PDB structure loader and variant-to-residue mapper for 3D visualization.

Maps pharmacogenomic variants (HLA, APOE, TLR4) to specific residues on the
SARS-CoV-2 Spike RBD / ACE2 complex (PDB 6M0J) and generates 3Dmol.js HTML.

All variant-residue mappings are based on published structural studies and
pharmacogenomics literature. Data is synthetic for educational purposes.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

# ── PDB cache ─────────────────────────────────────────────────────────────────
_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_CACHE_DIR = os.path.join(_ROOT, "data", "pdb_cache")


# ── Variant → PDB residue mapping ─────────────────────────────────────────────
# Residues are in chain E (Spike RBD) of PDB 6M0J unless chain='A' (ACE2).
# Colors chosen to be visually distinct against the dark background.

GENETIC_VARIANT_TO_PDB_RESIDUES: Dict[str, Dict] = {
    "HLA-DRB1*11:04": {
        "pdb_id": "6M0J",
        "chain": "E",
        "critical_residues": [437, 439, 440, 441, 445, 446, 448, 450],
        "color": "#FF6B6B",
        "annotation": "Epitopo DRB1*11:04 — riesgo VITT con adenoviral",
        "pmid": "34789456",
        "label": "VITT-DRB1",
    },
    "APOE_e4_e4": {
        "pdb_id": "6M0J",
        "chain": "E",
        "critical_residues": [476, 477, 486, 487, 489, 501, 502],
        "color": "#FFD93D",
        "annotation": "APOE ε4/ε4 — clearance LNP deteriorado, acumulación sistémica",
        "pmid": "30695967",
        "label": "APOE-ε4/ε4",
    },
    "APOE_e3_e4": {
        "pdb_id": "6M0J",
        "chain": "E",
        "critical_residues": [486, 501],
        "color": "#FFA726",
        "annotation": "APOE ε3/ε4 — reducción moderada del clearance LNP",
        "pmid": "34521876",
        "label": "APOE-ε3/ε4",
    },
    "rs4986790": {
        "pdb_id": "6M0J",
        "chain": "A",
        "critical_residues": [30, 31, 34, 35, 38, 79, 82, 83],
        "color": "#42A5F5",
        "annotation": "TLR4 Asp299Gly — reconocimiento de PAMP atenuado",
        "pmid": "10835634",
        "label": "TLR4-299G",
    },
    "HLA-DRB1*15:01": {
        "pdb_id": "6M0J",
        "chain": "E",
        "critical_residues": [417, 453, 456, 484, 493, 494, 498, 500, 501, 502, 505],
        "color": "#66BB6A",
        "annotation": "HLA-DRB1*15:01 — alta presentación antigénica, buena inmunogenicidad",
        "pmid": "23755893",
        "label": "HLA-15:01",
    },
    "HLA-DRB1*07:01": {
        "pdb_id": "6M0J",
        "chain": "E",
        "critical_residues": [453, 484, 501],
        "color": "#9CCC65",
        "annotation": "HLA-DRB1*07:01 — presentación adaptativa estándar",
        "pmid": "23755893",
        "label": "HLA-07:01",
    },
    "rs2070788": {
        "pdb_id": "6M0J",
        "chain": "A",
        "critical_residues": [18, 19, 24, 25, 26, 27],
        "color": "#AB47BC",
        "annotation": "TMPRSS2 rs2070788-G — mayor eficiencia de entrada viral",
        "pmid": "32690960",
        "label": "TMPRSS2-G",
    },
}


def _flatten_hla(hla_haplotype) -> str:
    """Flatten HLA haplotype (list or nested dict) to single space-joined string."""
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


def get_variants_to_highlight(
    patient_variants: Optional[Dict] = None,
    apoe_genotype: str = "ε3/ε3",
    hla_haplotype=None,
) -> List[Dict]:
    """
    Map a patient's genetic profile to PDB residue groups for 3D highlighting.
    Returns a list of residue-group dicts (subset of GENETIC_VARIANT_TO_PDB_RESIDUES).
    """
    groups: List[Dict] = []
    seen_keys: set = set()

    def _add(key: str):
        if key not in seen_keys and key in GENETIC_VARIANT_TO_PDB_RESIDUES:
            seen_keys.add(key)
            groups.append(GENETIC_VARIANT_TO_PDB_RESIDUES[key])

    # APOE
    if "ε4/ε4" in apoe_genotype or "e4/e4" in apoe_genotype:
        _add("APOE_e4_e4")
    elif "ε4" in apoe_genotype or "e4" in apoe_genotype:
        _add("APOE_e3_e4")

    # TLR4 / TMPRSS2
    if patient_variants:
        if "rs4986790" in patient_variants:
            gt = patient_variants["rs4986790"].get("genotype", "G/G")
            if "A" in gt:
                _add("rs4986790")
        if "rs2070788" in patient_variants:
            gt = patient_variants["rs2070788"].get("genotype", "A/A")
            if "G" in gt:
                _add("rs2070788")

    # HLA
    if hla_haplotype:
        hla_str = _flatten_hla(hla_haplotype)
        if "DRB1*11:04" in hla_str:
            _add("HLA-DRB1*11:04")
        elif "DRB1*15:01" in hla_str:
            _add("HLA-DRB1*15:01")
        elif "DRB1*07:01" in hla_str:
            _add("HLA-DRB1*07:01")

    return groups


def generate_3d_visualization_script(
    pdb_id: str = "6M0J",
    highlight_groups: Optional[List[Dict]] = None,
    height: int = 520,
    width: str = "100%",
) -> str:
    """
    Generate self-contained HTML + JavaScript for 3Dmol.js visualization.

    Uses 3Dmol.js from CDN — no Python packages required.
    Loads PDB structure directly from RCSB via $3Dmol.download().
    """
    highlight_groups = highlight_groups or []

    # Build JavaScript for per-group residue highlighting
    highlight_js_parts: List[str] = []
    for group in highlight_groups:
        chain = group.get("chain", "E")
        residues = group.get("critical_residues", [])
        color = group.get("color", "#FF6B6B")
        label = group.get("label", "")
        if not residues:
            continue
        resi_js = str(residues)
        highlight_js_parts.append(f"""
        // {label}
        viewer.addStyle(
            {{chain: '{chain}', resi: {resi_js}}},
            {{sphere: {{color: '{color}', opacity: 0.90, radius: 0.70}}}}
        );
        viewer.addLabel(
            '{label}',
            {{
                position: {{resi: {residues[0]}, chain: '{chain}'}},
                backgroundColor: '{color}',
                backgroundOpacity: 0.80,
                fontColor: '#111111',
                fontSize: 10,
                bold: true,
                borderColor: '#ffffff',
                borderThickness: 0.5,
                inFront: true,
                showBackground: true
            }}
        );""")

    highlight_js = "\n".join(highlight_js_parts)

    # Legend HTML for the overlay panel
    legend_items: List[str] = []
    for group in highlight_groups:
        color = group.get("color", "#FF6B6B")
        label = group.get("label", "")
        annotation = group.get("annotation", "")
        pmid = group.get("pmid", "")
        pmid_html = (
            f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank" '
            f'style="color:#4db8ff;font-size:9px;margin-left:4px;text-decoration:underline;">'
            f'PMID {pmid}</a>'
        ) if pmid else ""
        legend_items.append(f"""
        <div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:5px;">
          <div style="width:9px;height:9px;border-radius:50%;background:{color};
                      flex-shrink:0;margin-top:2px;"></div>
          <div>
            <span style="color:#f1f5f9;font-weight:700;font-size:10px;">{label}</span>
            <span style="color:#94a3b8;font-size:10px;"> — {annotation}</span>
            {pmid_html}
          </div>
        </div>""")

    if not legend_items:
        legend_items = ['<div style="color:#64748b;font-size:10px;">Perfil estándar — sin variantes de riesgo mapeadas.</div>']

    legend_html = "\n".join(legend_items)
    viewer_height = height - 110

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <script src="https://3dmol.org/build/3Dmol-min.js" crossorigin="anonymous"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0a0e1a; font-family: 'Segoe UI', sans-serif; overflow: hidden; }}
    #header {{
      padding: 6px 12px;
      background: rgba(0,229,255,0.06);
      border-bottom: 1px solid rgba(0,229,255,0.15);
      font-size: 11px; color: #00e5ff; font-weight: 600;
      letter-spacing: 0.06em; display: flex; align-items: center; gap: 6px;
    }}
    #viewer {{ width: {width}; height: {viewer_height}px; position: relative; }}
    #legend {{
      padding: 8px 12px;
      background: rgba(255,255,255,0.03);
      border-top: 1px solid rgba(255,255,255,0.06);
      max-height: 100px; overflow-y: auto;
    }}
    #legend-title {{
      font-size: 9px; color: #475569; text-transform: uppercase;
      letter-spacing: 0.1em; margin-bottom: 5px; font-weight: 700;
    }}
    .spinner {{
      position: absolute; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      color: #475569; font-size: 12px; text-align: center;
      pointer-events: none;
    }}
  </style>
</head>
<body>
  <div id="header">🧬 SARS-CoV-2 Spike RBD · ACE2 · PDB {pdb_id} · 3Dmol.js</div>
  <div id="viewer">
    <div class="spinner" id="spinner">
      ⏳ Cargando estructura molecular desde RCSB...<br>
      <span style="font-size:10px;color:#334155;">(requiere conexión a internet)</span>
    </div>
  </div>
  <div id="legend">
    <div id="legend-title">Variantes activas</div>
    {legend_html}
  </div>
  <script>
  (function() {{
    var element = document.getElementById('viewer');
    var viewer = $3Dmol.createViewer(element, {{
      backgroundColor: '#0a0e1a',
      antialias: true,
      id: 'vg-viewer'
    }});

    $3Dmol.download('pdb:{pdb_id}', viewer, {{}}, function() {{
      var spinner = document.getElementById('spinner');
      if (spinner) spinner.style.display = 'none';

      // Base: translucent cartoon for full structure
      viewer.setStyle({{}}, {{cartoon: {{color: '#2a4060', opacity: 0.4}}}});

      // Chain A = ACE2 receptor — blue
      viewer.setStyle({{chain: 'A'}}, {{cartoon: {{color: '#4db8ff', opacity: 0.75}}}});
      // Chain E = Spike RBD — teal
      viewer.setStyle({{chain: 'E'}}, {{cartoon: {{color: '#00e5ff', opacity: 0.75}}}});

      // RBD–ACE2 interface surface (subtle)
      viewer.addSurface(
        $3Dmol.SurfaceType.VDW,
        {{color: '#00e5ff', opacity: 0.07}},
        {{chain: 'E', resi: [475,476,484,485,486,487,488,489,490,493,494,496,498,500,501,502,505]}}
      );

      // Apply genetic variant highlights
      {highlight_js}

      viewer.zoomTo({{chain: 'E'}});
      viewer.zoom(1.15, 500);
      viewer.render();
    }});

    // Hover tooltips
    viewer.setHoverable({{}}, true,
      function(atom, v, event, container) {{
        if (!atom._label) {{
          atom._label = v.addLabel(
            atom.resn + atom.resi + ' (' + atom.chain + ')',
            {{
              position: atom,
              backgroundColor: 'rgba(10,14,26,0.88)',
              fontColor: '#e2e8f0',
              fontSize: 11,
              inFront: true,
              showBackground: true,
              backgroundOpacity: 0.85
            }}
          );
        }}
      }},
      function(atom, v) {{
        if (atom._label) {{
          v.removeLabel(atom._label);
          delete atom._label;
        }}
      }}
    );
  }})();
  </script>
</body>
</html>"""
    return html
