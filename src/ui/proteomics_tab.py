"""
Proteomics visualization tab — VaccineGenics
Shows protein structures (3Dmol.js PDB), variant-protein networks,
vaccine mechanism pathways, and variant×protein impact heatmaps.
Bilingual ES/EN support via lang parameter.
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import numpy as np

# ── Protein database ───────────────────────────────────────────────────────────

_PROTEINS = {
    "TLR4": {
        "full_name": "Toll-Like Receptor 4",
        "pdb_id": "3FXI",
        "color": "#63b3ed", "emoji": "🛡️", "module": "TLR",
        "function": {
            "es": ("Receptor de reconocimiento de patrones de la inmunidad innata. "
                   "Detecta LPS bacteriano y adyuvantes vacunales (AS01, MF59, MPLA). "
                   "Activa NF-κB → TNF-α, IL-6, IL-12 → inflamación y activación DC."),
            "en": ("Pattern recognition receptor of innate immunity. "
                   "Detects bacterial LPS and vaccine adjuvants (AS01, MF59, MPLA). "
                   "Activates NF-κB → TNF-α, IL-6, IL-12 → inflammation and DC activation."),
        },
        "vaccine_role": {
            "mRNA": {
                "es": "Detecta el LNP como señal de peligro (DAMP) → activa DCs",
                "en": "Detects LNP as a danger signal (DAMP) → activates DCs",
            },
            "adenoviral_vector": {
                "es": "Reconoce la cápside adenoviral → respuesta innata inicial",
                "en": "Recognizes adenoviral capsid → initial innate response",
            },
            "protein_subunit": {
                "es": "Crítico: activa el adyuvante AS01/MF59 en células dendríticas",
                "en": "Critical: activates AS01/MF59 adjuvant in dendritic cells",
            },
        },
        "variants_impact": {
            "rs4986790": ("Asp299Gly", {
                "es": "Señalización TLR4 reducida ~40% → menor respuesta innata",
                "en": "TLR4 signaling reduced ~40% → decreased innate response",
            }, -0.40),
            "rs4986791": ("Thr399Ile", {
                "es": "Señalización TLR4 reducida ~30% → sinergia con rs4986790",
                "en": "TLR4 signaling reduced ~30% → synergy with rs4986790",
            }, -0.30),
        },
        "highlight": ("A", 299),
        "highlight_residue": "Asp299",
        "highlight_mutation": "Asp299Gly (rs4986790)",
        "region_name": {"es": "Dominio extracelular LRR — sitio Asp299Gly", "en": "LRR ectodomain — Asp299Gly site"},
        "y_pos": 4.5,
    },
    "HLA-DRB1": {
        "full_name": "MHC Class II — HLA DRβ1",
        "pdb_id": "2SEB",
        "color": "#48bb78", "emoji": "🎯", "module": "HLA",
        "function": {
            "es": ("Complejo Mayor de Histocompatibilidad clase II. Presenta péptidos antigénicos "
                   "de 13–25 aa a linfocitos T CD4+ helper. El alelo DRB1*11:04 se asocia a VITT "
                   "(Vaccine-Induced Thrombocytopenia and Thrombosis) con vectores adenovirales."),
            "en": ("Major Histocompatibility Complex class II. Presents antigenic peptides "
                   "of 13–25 aa to CD4+ helper T lymphocytes. The DRB1*11:04 allele is associated "
                   "with VITT (Vaccine-Induced Thrombocytopenia and Thrombosis) with adenoviral vectors."),
        },
        "vaccine_role": {
            "mRNA": {
                "es": "Presenta péptidos del spike a CD4+ → ayuda a células B → IgG",
                "en": "Presents spike peptides to CD4+ → helps B cells → IgG",
            },
            "adenoviral_vector": {
                "es": "Presenta péptidos + riesgo VITT si DRB1*11:04",
                "en": "Presents peptides + VITT risk if DRB1*11:04",
            },
            "protein_subunit": {
                "es": "Contacto directo con RBD → presentación eficiente",
                "en": "Direct contact with RBD → efficient presentation",
            },
        },
        "variants_impact": {
            "HLA-DRB1*11:04": ("DRB1*11:04", {
                "es": "Riesgo VITT con adenoviral vector — contraindicación relativa",
                "en": "VITT risk with adenoviral vector — relative contraindication",
            }, -0.60),
            "HLA-DRB1*15:01": ("DRB1*15:01", {
                "es": "Alta respuesta con mRNA y proteína subunidad",
                "en": "High response with mRNA and protein subunit",
            }, +0.35),
            "HLA-DRB1*01:01": ("DRB1*01:01", {
                "es": "Respuesta óptima con plataformas basadas en proteína",
                "en": "Optimal response with protein-based platforms",
            }, +0.25),
        },
        "highlight": ("B", 74),
        "highlight_residue": "β74",
        "highlight_mutation": "Peptide-binding groove — β74 polymorphic site",
        "region_name": {"es": "Surco de unión peptídica — residuo β74 polimórfico", "en": "Peptide-binding groove — β74 polymorphic residue"},
        "y_pos": 3.5,
    },
    "APOE": {
        "full_name": "Apolipoprotein E",
        "pdb_id": "3R4L",
        "color": "#ed8936", "emoji": "📦", "module": "APOE",
        "function": {
            "es": ("Glicoproteína de 299 aa. Opsoniza nanopartículas lipídicas (LNP) para "
                   "clearance hepático vía receptor LDL. El alelo ε4 tiene mayor afinidad "
                   "por los receptores hepáticos → clearance ultra-rápido del LNP → menor "
                   "tiempo de contacto del ARNm con células inmunes → menor inmunogenicidad."),
            "en": ("299 aa glycoprotein. Opsonizes lipid nanoparticles (LNP) for "
                   "hepatic clearance via LDL receptor. The ε4 allele has higher affinity "
                   "for hepatic receptors → ultra-fast LNP clearance → less "
                   "contact time of mRNA with immune cells → lower immunogenicity."),
        },
        "vaccine_role": {
            "mRNA": {
                "es": "CRÍTICO: ε4/ε4 → clearance ~3× más rápido → LNP-mRNA contraindicado",
                "en": "CRITICAL: ε4/ε4 → clearance ~3× faster → LNP-mRNA contraindicated",
            },
            "adenoviral_vector": {
                "es": "Sin efecto: no usa LNP",
                "en": "No effect: does not use LNP",
            },
            "protein_subunit": {
                "es": "Sin efecto: proteína libre, no LNP",
                "en": "No effect: free protein, not LNP",
            },
        },
        "variants_impact": {
            "ε4/ε4": ("APOE ε4/ε4", {
                "es": "Clearance LNP ultra-rápido → contraindica mRNA-LNP",
                "en": "Ultra-fast LNP clearance → contraindicates mRNA-LNP",
            }, -0.85),
            "ε3/ε4": ("APOE ε3/ε4", {
                "es": "Clearance moderadamente aumentado → precaución mRNA",
                "en": "Moderately increased clearance → mRNA caution",
            }, -0.35),
            "ε3/ε3": ("APOE ε3/ε3", {
                "es": "Clearance normal — óptimo para todas las plataformas",
                "en": "Normal clearance — optimal for all platforms",
            }, 0.0),
        },
        "highlight": ("A", 112),
        "highlight_residue": "Cys112",
        "highlight_mutation": "Cys112Arg (ε4 defining — rs429358)",
        "region_name": {"es": "Dominio de unión al receptor — Cys112→Arg define alelo ε4", "en": "Receptor-binding domain — Cys112→Arg defines ε4 allele"},
        "y_pos": 2.5,
    },
    "IL-6": {
        "full_name": "Interleukin-6",
        "pdb_id": "1ALU",
        "color": "#f56565", "emoji": "🔥", "module": "STAT",
        "function": {
            "es": ("Citocina pleitrópica de 184 aa. Regula respuesta inflamatoria aguda, "
                   "diferenciación de células B plasmáticas y activación del eje JAK1/STAT3. "
                   "El polimorfismo -174G>C (rs1800795) en el promotor aumenta la transcripción: "
                   "C/C produce hasta 3× más IL-6 basal → mayor reactogenicidad post-vacunal."),
            "en": ("Pleiotropic 184 aa cytokine. Regulates acute inflammatory response, "
                   "plasma B-cell differentiation and JAK1/STAT3 axis activation. "
                   "The -174G>C promoter polymorphism (rs1800795) increases transcription: "
                   "C/C produces up to 3× more basal IL-6 → greater post-vaccine reactogenicity."),
        },
        "vaccine_role": {
            "mRNA": {
                "es": "Alta IL-6 (C/C) → síntomas sistémicos severos post-vacuna",
                "en": "High IL-6 (C/C) → severe systemic symptoms post-vaccine",
            },
            "adenoviral_vector": {
                "es": "Igual que mRNA — ambas inducen IL-6",
                "en": "Same as mRNA — both induce IL-6",
            },
            "protein_subunit": {
                "es": "Menor inducción de IL-6 — mejor tolerado en C/C",
                "en": "Lower IL-6 induction — better tolerated in C/C",
            },
        },
        "variants_impact": {
            "rs1800795_CC": ("IL6 -174 C/C", {
                "es": "Producción IL-6 3× mayor → hiperinflamación potencial",
                "en": "3× higher IL-6 production → potential hyperinflammation",
            }, -0.45),
            "rs1800795_GC": ("IL6 -174 G/C", {
                "es": "Producción IL-6 moderadamente aumentada",
                "en": "Moderately increased IL-6 production",
            }, -0.15),
            "rs1800795_GG": ("IL6 -174 G/G", {
                "es": "Producción IL-6 basal — respuesta normal",
                "en": "Basal IL-6 production — normal response",
            }, 0.0),
        },
        "highlight": ("A", 57),
        "highlight_residue": "His57",
        "highlight_mutation": "Helix D — receptor-binding site",
        "region_name": {"es": "Hélice D — sitio de unión al receptor IL-6R/gp130", "en": "Helix D — IL-6R/gp130 receptor binding site"},
        "y_pos": 1.5,
    },
    "TMPRSS2": {
        "full_name": "Transmembrane Serine Protease 2",
        "pdb_id": "7MEQ",
        "color": "#4fd1c5", "emoji": "✂️", "module": "TLR",
        "function": {
            "es": ("Proteasa de membrana tipo II de 529 aa. Activa el spike SARS-CoV-2 por "
                   "clivaje proteolítico en la región S1/S2, facilitando la fusión viral. "
                   "El alelo G (rs2070788) aumenta la expresión de TMPRSS2 y correlaciona "
                   "con mayor respuesta a vacunas anti-SARS-CoV-2 en estudios de cohorte."),
            "en": ("529 aa type II membrane protease. Activates SARS-CoV-2 spike by "
                   "proteolytic cleavage at the S1/S2 region, facilitating viral fusion. "
                   "The G allele (rs2070788) increases TMPRSS2 expression and correlates "
                   "with greater response to anti-SARS-CoV-2 vaccines in cohort studies."),
        },
        "vaccine_role": {
            "mRNA": {
                "es": "Alta expresión (G/G) → mejor respuesta anti-spike, mayor inmunogenicidad",
                "en": "High expression (G/G) → better anti-spike response, higher immunogenicity",
            },
            "adenoviral_vector": {
                "es": "Igual que mRNA",
                "en": "Same as mRNA",
            },
            "protein_subunit": {
                "es": "Bajo impacto — no involucrado en el delivery de la proteína",
                "en": "Low impact — not involved in protein delivery",
            },
        },
        "variants_impact": {
            "rs2070788_GG": ("TMPRSS2 G/G", {
                "es": "Mayor expresión → predictor positivo de respuesta anti-CoV2",
                "en": "Higher expression → positive predictor of anti-CoV2 response",
            }, +0.30),
            "rs2070788_AG": ("TMPRSS2 A/G", {
                "es": "Expresión intermedia",
                "en": "Intermediate expression",
            }, +0.12),
            "rs2070788_AA": ("TMPRSS2 A/A", {
                "es": "Expresión basal",
                "en": "Basal expression",
            }, 0.0),
        },
        "highlight": ("A", 256),
        "highlight_residue": "Ser256",
        "highlight_mutation": "Catalytic Ser256 — serine protease active site",
        "region_name": {"es": "Tríada catalítica — Ser256 del sitio activo de serina-proteasa", "en": "Catalytic triad — Ser256 of serine protease active site"},
        "y_pos": 0.5,
    },
}

# ── Vaccine mechanism steps ────────────────────────────────────────────────────

def _step(emoji, label_es, label_en, desc_es, desc_en, prot):
    return (
        emoji,
        {"es": label_es, "en": label_en},
        {"es": desc_es, "en": desc_en},
        prot,
    )


_VAX_STEPS = {
    "mRNA": [
        _step("💊", "1. LNP-ARNm", "1. LNP-mRNA",
              "Nanopartícula lipídica\nencapsula el ARNm", "Lipid nanoparticle\nencapsulates mRNA", "APOE"),
        _step("📦", "2. APOE Opsoniza", "2. APOE Opsonizes",
              "APOE recubre la LNP\n→ captación por CD", "APOE coats LNP\n→ uptake by DCs", "APOE"),
        _step("⚙️", "3. Endosoma → ARNm", "3. Endosome → mRNA",
              "Escape endosomal\n→ ARNm libre en citoplasma", "Endosomal escape\n→ free mRNA in cytoplasm", None),
        _step("🔬", "4. Traducción", "4. Translation",
              "El ribosoma sintetiza\nla proteína Spike", "Ribosome synthesizes\nSpike protein", None),
        _step("🛡️", "5. Señal TLR4/7", "5. TLR4/7 Signal",
              "La LNP activa TLR4/7\nen células dendríticas", "LNP activates TLR4/7\nin dendritic cells", "TLR4"),
        _step("🎯", "6. Presentación HLA", "6. HLA Presentation",
              "Péptidos Spike → HLA-I/II\n→ linfocitos T CD8+/CD4+", "Spike peptides → HLA-I/II\n→ CD8+ and CD4+ T cells", "HLA-DRB1"),
        _step("🔥", "7. IL-6 Amplifica", "7. IL-6 Amplifies",
              "IL-6 amplifica la respuesta\n(C/C = riesgo sistémico)", "IL-6 amplifies response\n(C/C = systemic risk)", "IL-6"),
        _step("💉", "8. IgG Anti-Spike", "8. IgG Anti-Spike",
              "Linfocitos B → anticuerpos\nIgG neutralizantes", "B cells → neutralizing\nIgG antibodies", None),
    ],
    "adenoviral_vector": [
        _step("🧬", "1. Cápside Ad/ChAdOx", "1. Ad/ChAdOx Capsid",
              "Vector adenoviral\ncon gen del antígeno", "Adenoviral vector\nwith antigen gene", "TLR4"),
        _step("🔗", "2. Receptor CAR", "2. CAR Receptor",
              "Fibra viral → CAR\n→ endocitosis", "Fiber-knob → CAR\n→ endocytosis", None),
        _step("🛡️", "3. TLR4 Detecta", "3. TLR4 Detects",
              "La cápside adenoviral\nactiva TLR4", "Adenoviral capsid\nactivates TLR4", "TLR4"),
        _step("🏛️", "4. Núcleo → ADN", "4. Nucleus → DNA",
              "ADN episomal\n→ transcripción del antígeno", "Episomal DNA\n→ antigen transcription", None),
        _step("⚙️", "5. ARNm → Spike", "5. mRNA → Spike",
              "Síntesis y traducción\ndel antígeno vacunal", "Synthesis and translation\nof vaccine antigen", None),
        _step("⚠️", "6. HLA ± VITT", "6. HLA ± VITT",
              "HLA-II presenta antígenos\n(DRB1*11:04 → riesgo VITT)", "HLA-II presents antigens\n(DRB1*11:04 → VITT risk)", "HLA-DRB1"),
        _step("🔥", "7. Respuesta IL-6", "7. IL-6 Response",
              "IL-6 coordina\nla inflamación", "IL-6 coordinates\ninflammation", "IL-6"),
        _step("💉", "8. IgG + CD8+", "8. IgG + CD8+",
              "Anticuerpos + linfocitos T\ncitotóxicos", "Antibodies + cytotoxic\nT cells", None),
    ],
    "protein_subunit": [
        _step("🧪", "1. RBD + Adyuvante", "1. RBD + Adjuvant",
              "Proteína RBD purificada\n+ adyuvante AS01/MF59", "Purified RBD protein\n+ AS01/MF59 adjuvant", "TLR4"),
        _step("🛡️", "2. TLR4/9 Activa", "2. TLR4/9 Activates",
              "El adyuvante activa TLR4/TLR9\nen CD → maduración", "Adjuvant activates TLR4/TLR9\nin DCs → maturation", "TLR4"),
        _step("🔬", "3. CD Captura RBD", "3. DC Captures RBD",
              "La célula dendrítica procesa\nla proteína RBD", "Dendritic cell processes\nRBD protein", None),
        _step("🎯", "4. HLA-II → CD4+", "4. HLA-II → CD4+",
              "RBD → péptidos → HLA-DRB1\n→ linfocitos T colaboradores", "RBD → peptides → HLA-DRB1\n→ T helper cells", "HLA-DRB1"),
        _step("🔥", "5. Soporte IL-6", "5. IL-6 Support",
              "IL-6 favorece la\ndiferenciación de células B", "IL-6 supports\nplasma B-cell differentiation", "IL-6"),
        _step("🌀", "6. Centro Germinal", "6. GC B cells",
              "Centro germinal:\nmaduración de afinidad", "Germinal center:\naffinity maturation", None),
        _step("💉", "7. IgG Alta Afinidad", "7. High-Affinity IgG",
              "Anticuerpos de alta afinidad\nprotección duradera", "High-affinity antibodies\nlasting protection", None),
    ],
}


# ── i18n helpers ──────────────────────────────────────────────────────────────

def _p(lang: str, d, fallback=""):
    """Get translated string from a {es/en} dict or plain string."""
    if isinstance(d, dict):
        return d.get(lang, d.get("es", fallback))
    return d or fallback

_UI = {
    "es": {
        "header": "🔬 Proteómica",
        "subtitle": "Proteínas clave en la respuesta vacunal · Estructuras 3D reales (PDB) · Impacto de variantes del paciente",
        "synth": "⚠️ DATOS 100% SINTÉTICOS — Solo investigación educativa. No usar para decisiones clínicas.",
        "no_patient": "💡 Analiza un paciente en el **Dashboard** o en **Mi Perfil** para ver el impacto de sus variantes en las proteínas.",
        "network_hdr": "🕸️ Red Variante → Proteína → Plataforma",
        "viewer_hdr": "🧬 Estructura 3D de Proteínas (PDB Real)",
        "mechanism_hdr": "⚗️ Mecanismo de Acción por Plataforma",
        "heatmap_hdr": "🌡️ Mapa de Calor — Impacto del Paciente",
        "protein_cards_hdr": "📋 Proteínas Clave",
        "select_protein": "Seleccionar proteína:",
        "patient_impact": "Impacto en este paciente:",
        "pdb_loading": "Cargando estructura PDB:{}…",
        "pdb_controls": "PDB: {} · Arrastra para rotar · Scroll para zoom · Pasa el cursor sobre los residuos para ver su nombre",
        "role_label": "Rol de {} en cada plataforma vacunal:",
        "impact_label": "impacto paciente",
        "legend": "▲ impacto positivo · ▼ impacto negativo · ● neutro · Basado en el perfil genético del paciente",
        "network_var": "Variantes del Paciente",
        "network_prot": "Proteínas Clave",
        "network_vax": "Plataformas Vacunales",
        "network_title": "<b>Red Variante → Proteína → Vacuna</b>  (impacto del paciente)",
        "heatmap_title": "<b>Impacto del Paciente</b> — Proteína × Plataforma Vacunal",
        "heatmap_impact": "Impacto",
        "heatmap_ticks": ["−Alto", "−Mod", "Neutro", "+Mod", "+Alto"],
        "hover_residue": "Residuo",
        "hover_chain": "Cadena",
        "hover_variant_site": "Sitio variante",
        "hover_wildtype": "Tipo silvestre",
        "vax_selected": "✅ Seleccionada",
        "platform_label": "Plataforma",
        "mrna_lbl": "💊 ARNm", "adeno_lbl": "🧬 Adenoviral", "prot_lbl": "🧪 Subunidad",
        "mech_title_prefix": "Mecanismo de Acción",
    },
    "en": {
        "header": "🔬 Proteomics",
        "subtitle": "Key proteins in vaccine response · Real 3D structures (PDB) · Patient variant impact",
        "synth": "⚠️ 100% SYNTHETIC DATA — Educational research only. Not for clinical decisions.",
        "no_patient": "💡 Analyze a patient in the **Dashboard** or **My Profile** to see their variant impact on proteins.",
        "network_hdr": "🕸️ Variant → Protein → Platform Network",
        "viewer_hdr": "🧬 3D Protein Structures (Real PDB Data)",
        "mechanism_hdr": "⚗️ Mechanism of Action by Platform",
        "heatmap_hdr": "🌡️ Patient Impact Heatmap",
        "protein_cards_hdr": "📋 Key Proteins",
        "select_protein": "Select protein:",
        "patient_impact": "Patient impact:",
        "pdb_loading": "Loading PDB structure:{}…",
        "pdb_controls": "PDB: {} · Drag to rotate · Scroll to zoom · Hover over residues to see their name",
        "role_label": "Role of {} in each vaccine platform:",
        "impact_label": "patient impact",
        "legend": "▲ positive impact · ▼ negative impact · ● neutral · Based on patient genetic profile",
        "network_var": "Patient Variants",
        "network_prot": "Key Proteins",
        "network_vax": "Vaccine Platforms",
        "network_title": "<b>Variant → Protein → Vaccine Network</b>  (patient impact)",
        "heatmap_title": "<b>Patient Impact</b> — Protein × Vaccine Platform",
        "heatmap_impact": "Impact",
        "heatmap_ticks": ["−High", "−Mod", "Neutral", "+Mod", "+High"],
        "hover_residue": "Residue",
        "hover_chain": "Chain",
        "hover_variant_site": "Variant site",
        "hover_wildtype": "Wildtype",
        "vax_selected": "✅ Selected",
        "platform_label": "Platform",
        "mrna_lbl": "💊 mRNA", "adeno_lbl": "🧬 Adenoviral", "prot_lbl": "🧪 Subunit",
        "mech_title_prefix": "Mechanism of Action",
    },
}

def _u(key: str, lang: str = "es", *args) -> str:
    s = _UI.get(lang, _UI["es"]).get(key, _UI["es"].get(key, f"[{key}]"))
    return s.format(*args) if args else s


# ── Helpers ────────────────────────────────────────────────────────────────────

def _patient_protein_impacts(patient_dict: dict) -> dict[str, float]:
    apoe = patient_dict.get("apoe_genotype", "ε3/ε3")
    variants = patient_dict.get("variants", {})
    hla = patient_dict.get("hla_haplotype", {}) or {}
    if not isinstance(hla, dict): hla = {}
    hla_alleles = []
    for cls in hla.values():
        for alleles in cls.values():
            hla_alleles.extend(alleles)

    impacts = {k: 0.0 for k in _PROTEINS}

    tlr4_score = 0.0
    if variants.get("rs4986790", {}).get("genotype", "G/G") == "A/A": tlr4_score -= 0.40
    elif variants.get("rs4986790", {}).get("genotype", "G/G") == "A/G": tlr4_score -= 0.20
    if variants.get("rs4986791", {}).get("genotype", "C/C") == "T/T": tlr4_score -= 0.30
    elif variants.get("rs4986791", {}).get("genotype", "C/C") == "C/T": tlr4_score -= 0.15
    impacts["TLR4"] = tlr4_score

    hla_score = 0.0
    if any("DRB1*11:04" in a for a in hla_alleles): hla_score -= 0.60
    elif any("DRB1*15:01" in a for a in hla_alleles): hla_score += 0.35
    elif any("DRB1*01:01" in a for a in hla_alleles): hla_score += 0.25
    impacts["HLA-DRB1"] = hla_score

    apoe_map = {"ε4/ε4": -0.85, "ε2/ε4": -0.50, "ε3/ε4": -0.35,
                "ε3/ε3": 0.0, "ε2/ε3": +0.10, "ε2/ε2": +0.15}
    impacts["APOE"] = apoe_map.get(apoe, 0.0)

    il6_gt = variants.get("rs1800795", {}).get("genotype", "G/G")
    il6_map = {"C/C": -0.45, "G/C": -0.15, "C/G": -0.15, "G/G": 0.0}
    impacts["IL-6"] = il6_map.get(il6_gt, 0.0)

    tmpr_gt = variants.get("rs2070788", {}).get("genotype", "A/A")
    tmpr_map = {"G/G": +0.30, "A/G": +0.12, "G/A": +0.12, "A/A": 0.0}
    impacts["TMPRSS2"] = tmpr_map.get(tmpr_gt, 0.0)

    return impacts


def _impact_color(score: float) -> str:
    if score > 0.2:  return "#48bb78"
    if score > 0.05: return "#68d391"
    if score > -0.1: return "#a0aec0"
    if score > -0.3: return "#ed8936"
    return "#f56565"


def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _get_variant_site_label(protein_name: str, patient_dict: dict, lang: str) -> str:
    """Build a concise label for the highlighted variant sphere in the 3D viewer."""
    p = _PROTEINS[protein_name]
    vi = p.get("variants_impact", {})
    variants = patient_dict.get("variants", {})
    apoe = patient_dict.get("apoe_genotype", "ε3/ε3")
    hla_alleles = []
    for cls in patient_dict.get("hla_haplotype", {}).values():
        for alleles in (cls or {}).values():
            hla_alleles.extend(alleles or [])

    base = p.get("highlight_residue", f"Res{p.get('highlight', ('A',0))[1]}")
    mutation = p.get("highlight_mutation", "")
    region = _p(lang, p.get("region_name", {}), mutation)

    if protein_name == "TLR4":
        gt = variants.get("rs4986790", {}).get("genotype", "G/G")
        impact_str = "↓40% signaling" if gt == "A/A" else ("↓20% signaling" if gt == "A/G" else "WT")
        return f"{base} — {impact_str}\\n{region}"
    elif protein_name == "HLA-DRB1":
        vitt = any("DRB1*11:04" in a for a in hla_alleles)
        high = any("DRB1*15:01" in a for a in hla_alleles)
        note = "⚠️ VITT risk" if vitt else ("↑ High responder" if high else "Standard")
        return f"{base} — {note}\\n{region}"
    elif protein_name == "APOE":
        apoe_impact = {"ε4/ε4":"↓↓↓ LNP clearance","ε3/ε4":"↓ LNP clearance","ε2/ε4":"↓ LNP clearance",
                       "ε3/ε3":"Normal clearance","ε2/ε3":"↑ clearance","ε2/ε2":"↑↑ clearance"}.get(apoe,"?")
        return f"{base} ({apoe}) — {apoe_impact}\\n{region}"
    elif protein_name == "IL-6":
        gt = variants.get("rs1800795", {}).get("genotype", "G/G")
        note = "3× IL-6 ↑" if gt == "C/C" else ("1.5× IL-6 ↑" if gt in ("G/C","C/G") else "Basal IL-6")
        return f"{base} — {note}\\n{region}"
    elif protein_name == "TMPRSS2":
        gt = variants.get("rs2070788", {}).get("genotype", "A/A")
        note = "↑ Expression (G/G)" if gt == "G/G" else ("Mid expression" if gt in ("A/G","G/A") else "Basal expression")
        return f"{base} — {note}\\n{region}"
    return f"{base}\\n{region}"


# ── Plot 1: Protein-Variant Network ───────────────────────────────────────────

def _plot_protein_network(patient_dict: dict, impacts: dict[str, float], platform: str, lang: str = "es"):
    proteins = list(_PROTEINS.keys())
    n_prot = len(proteins)

    nodes_x, nodes_y, node_labels, node_colors, node_sizes, node_hover = [], [], [], [], [], []

    for i, name in enumerate(proteins):
        p = _PROTEINS[name]
        nodes_x.append(1.5)
        nodes_y.append(i * 1.2)
        node_labels.append(f"{p['emoji']} {name}")
        sc = impacts.get(name, 0.0)
        node_colors.append(_impact_color(sc))
        node_sizes.append(28)
        fn = _p(lang, p["function"])[:140]
        node_hover.append(
            f"<b>{p['full_name']}</b><br>"
            f"PDB: {p['pdb_id']} · Module: {p['module']}<br>"
            f"Patient impact: {sc:+.2f}<br>"
            f"Region: {_p(lang, p.get('region_name', {}))}<br><br>"
            f"{fn}…"
        )

    vax_names  = ["mRNA", "adenoviral_vector", "protein_subunit"]
    vax_labels = [_u("mrna_lbl", lang), _u("adeno_lbl", lang), _u("prot_lbl", lang)]
    vax_colors = ["#63b3ed", "#ed8936", "#48bb78"]
    vax_y      = [3.5, 2.0, 0.5]
    for j, (vn, vl, vc, vy) in enumerate(zip(vax_names, vax_labels, vax_colors, vax_y)):
        nodes_x.append(3.2)
        nodes_y.append(vy)
        node_labels.append(vl)
        node_colors.append(vc)
        node_sizes.append(34 if vn == platform else 24)
        node_hover.append(f"<b>{_u('platform_label', lang)}: {vn}</b><br>{_u('vax_selected', lang) if vn == platform else ''}")

    var_entries = []
    apoe = patient_dict.get("apoe_genotype", "ε3/ε3")
    var_entries.append(("APOE", apoe, impacts.get("APOE", 0.0)))
    variants = patient_dict.get("variants", {})
    if variants.get("rs4986790", {}).get("genotype", "G/G") != "G/G":
        var_entries.append(("TLR4", "rs4986790 " + variants["rs4986790"]["genotype"], impacts.get("TLR4", 0.0)))
    if variants.get("rs1800795", {}).get("genotype", "G/G") != "G/G":
        var_entries.append(("IL-6", "IL-6 " + variants["rs1800795"]["genotype"], impacts.get("IL-6", 0.0)))
    hla = patient_dict.get("hla_haplotype", {})
    for alleles in (hla.get("class_II", {}) or {}).values():
        for a in (alleles or []):
            if any(risk in a for risk in ["*11:04","*15:01","*04:01"]):
                var_entries.append(("HLA-DRB1", a, impacts.get("HLA-DRB1", 0.0)))

    for k, (prot, label, sc) in enumerate(var_entries[:6]):
        nodes_x.append(0.0)
        nodes_y.append(k * 1.0)
        node_labels.append(f"◆ {label}")
        node_colors.append(_impact_color(sc))
        node_sizes.append(16)
        node_hover.append(f"<b>{label}</b><br>Protein: {prot}<br>Impact: {sc:+.2f}")

    edge_x, edge_y = [], []
    prot_idx = {name: i for i, name in enumerate(proteins)}
    n_vax_nodes = len(vax_names)
    for k, (prot, _, sc) in enumerate(var_entries[:6]):
        pi = prot_idx.get(prot)
        if pi is None: continue
        vx0, vy0 = 0.0, k * 1.0
        vx1, vy1 = 1.5, pi * 1.2
        edge_x += [vx0, (vx0+vx1)/2, vx1, None]
        edge_y += [vy0, (vy0+vy1)/2, vy1, None]

    for i, pname in enumerate(proteins):
        for j, vname in enumerate(vax_names):
            role = _p(lang, _PROTEINS[pname]["vaccine_role"].get(vname, {}))
            if "Sin efecto" in role or "No effect" in role or not role: continue
            px0, py0 = 1.5, i * 1.2
            px1, py1 = 3.2, vax_y[j]
            edge_x += [px0, (px0+px1)/2, px1, None]
            edge_y += [py0, (py0+py1)/2, py1, None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1.2, color="rgba(99,179,237,0.25)"),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=nodes_x, y=nodes_y, mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors,
                    line=dict(color="#0a0f1a", width=2),
                    symbol=["circle"]*n_prot + ["hexagon"]*n_vax_nodes + ["diamond"]*len(var_entries[:6])),
        text=node_labels, textposition="middle right",
        textfont=dict(size=11, color="#e2e8f0"),
        hovertext=node_hover, hoverinfo="text",
        showlegend=False,
    ))
    for cx, lbl in [(0.0, _u("network_var", lang)), (1.5, _u("network_prot", lang)), (3.2, _u("network_vax", lang))]:
        fig.add_annotation(x=cx, y=n_prot*1.2+0.3, text=f"<b>{lbl}</b>",
                           showarrow=False, font=dict(size=11, color="#63b3ed"), xanchor="center")
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=480,
        xaxis=dict(visible=False, range=[-0.5, 4.0]),
        yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(text=_u("network_title", lang), font=dict(size=13, color="#e2e8f0")),
        font=dict(family="Inter,sans-serif", color="#e2e8f0"),
        hoverlabel=dict(bgcolor="#1a2332", font_size=12),
    )
    return fig


# ── Plot 2: Enhanced 3D Protein Viewer (3Dmol.js) with residue hover ─────────

def _render_3d_viewer(pdb_id: str, protein_name: str, highlight: tuple | None,
                      color_scheme: str = "#63b3ed", height: int = 440,
                      variant_label: str = "", lang: str = "es"):
    hl_js = ""
    if highlight:
        chain, resi = highlight
        safe_label = variant_label.replace("\\n", "&#10;").replace("'", "\\'").replace('"', '\\"') if variant_label else f"Site {chain}{resi}"

        hl_js = f"""
        // Highlight variant site sphere
        viewer.addSphere({{
            center: {{resi: {resi}, chain: '{chain}'}},
            radius: 1.8, color: '#ff6b6b', opacity: 0.88
        }});
        // Variant site label with clinical info
        viewer.addLabel('{safe_label}', {{
            position: {{resi: {resi}, chain: '{chain}'}},
            backgroundColor: 'rgba(229,62,62,0.96)',
            fontColor: 'white', fontSize: 10,
            borderThickness: 1.5, borderColor: '#ff6b6b',
            padding: 3, inFront: true,
        }});

        // Residue-level hover tooltip — shows amino acid name + number + chain
        viewer.setHoverable({{}}, true,
            function(atom, viewer, event, container) {{
                if (!atom || atom.resi === undefined) return;
                var aa3 = {{
                    ALA:'Ala',ARG:'Arg',ASN:'Asn',ASP:'Asp',CYS:'Cys',
                    GLN:'Gln',GLU:'Glu',GLY:'Gly',HIS:'His',ILE:'Ile',
                    LEU:'Leu',LYS:'Lys',MET:'Met',PHE:'Phe',PRO:'Pro',
                    SER:'Ser',THR:'Thr',TRP:'Trp',TYR:'Tyr',VAL:'Val',
                    HOH:'Water',HEM:'Heme',ZN:'Zn²⁺',CA:'Ca²⁺',NA:'Na⁺'
                }};
                var name3 = aa3[atom.resn] || atom.resn || '?';
                var isVariant = (atom.resi === {resi} && atom.chain === '{chain}');
                var tooltip = name3 + atom.resi + ' (Chain ' + atom.chain + ')';
                if (isVariant) {{
                    tooltip = '⚠️ ' + tooltip + ' — Variant site';
                }}
                viewer.addLabel(tooltip, {{
                    position: atom,
                    backgroundColor: isVariant ? 'rgba(229,62,62,0.96)' : 'rgba(26,35,50,0.95)',
                    fontColor: isVariant ? 'white' : '#e2e8f0',
                    fontSize: 11,
                    borderColor: isVariant ? '#ff6b6b' : '#63b3ed',
                    borderThickness: 1,
                    inFront: true,
                }}, undefined, true);
            }},
            function(atom, viewer) {{
                viewer.removeAllLabels();
                // Re-add the permanent variant site label after hover ends
                viewer.addLabel('{safe_label}', {{
                    position: {{resi: {resi}, chain: '{chain}'}},
                    backgroundColor: 'rgba(229,62,62,0.96)',
                    fontColor: 'white', fontSize: 10,
                    borderThickness: 1.5, borderColor: '#ff6b6b',
                    padding: 3, inFront: true,
                }});
                viewer.render();
            }}
        );
        """

    pdb_txt    = _u("pdb_loading", lang, pdb_id)
    ctrl_txt   = _u("pdb_controls", lang, pdb_id)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://3Dmol.org/build/3Dmol-min.js"></script>
<style>
  html, body {{ margin:0; padding:0; background:#0a0f1a; overflow:hidden; }}
  #viewer {{ width:100%; height:{height}px; position:relative; }}
  #info {{ position:absolute; bottom:8px; left:12px; color:#a0aec0;
           font:500 11px/1.4 Inter,sans-serif; pointer-events:none; max-width:90%; }}
  #loading {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
              color:#63b3ed; font:600 13px Inter,sans-serif; text-align:center; }}
  #hover-tip {{ position:absolute; top:8px; right:12px; color:#63b3ed;
                font:600 10px Inter,sans-serif; opacity:0.7; pointer-events:none; }}
</style>
</head>
<body>
<div id="viewer">
  <div id="loading">{pdb_txt}</div>
</div>
<div id="info">{ctrl_txt}</div>
<script>
window.addEventListener('load', function() {{
  var attempts = 0;
  var init = setInterval(function() {{
    attempts++;
    if (typeof $3Dmol !== 'undefined') {{
      clearInterval(init);
      document.getElementById('loading').style.display = 'none';
      var viewer = $3Dmol.createViewer(
        document.getElementById('viewer'),
        {{ backgroundColor: '#0a0f1a', antialias: true, cartoonQuality: 8 }}
      );
      $3Dmol.download('pdb:{pdb_id}', viewer, {{}}, function() {{
        viewer.setStyle({{}}, {{
          cartoon: {{
            color: 'spectrum',
            opacity: 0.92,
            thickness: 0.4,
            arrows: true,
          }}
        }});
        viewer.setStyle({{hetflag:true}}, {{
          stick: {{radius: 0.25, colorscheme: 'Jmol'}},
          sphere: {{radius: 0.4, opacity: 0.7}}
        }});
        {hl_js}
        viewer.zoomTo();
        viewer.render();
        viewer.spin('y', 1);
        setTimeout(function() {{ viewer.spin(false); }}, 4000);
      }});
    }} else if (attempts > 30) {{
      clearInterval(init);
      document.getElementById('loading').innerHTML =
        '⚠️ 3Dmol.js loading… Check internet connection.';
    }}
  }}, 200);
}});
</script>
</body>
</html>"""
    components.html(html, height=height + 10, scrolling=False)


# ── Plot 3: Vaccine Mechanism Pathway ─────────────────────────────────────────

def _plot_vaccine_mechanism(platform: str, impacts: dict[str, float], lang: str = "es"):
    steps = _VAX_STEPS[platform]
    n = len(steps)

    fig = go.Figure()
    # Steps are drawn in list order, one per column. The 5th tuple field is
    # ignored for layout — several platforms reuse the same value on more
    # than one step, which previously made two steps render on top of each
    # other at the same (x, y) position.
    x_vals = list(range(n))
    max_x = max(x_vals) + 1

    xs_sorted = sorted(set(x_vals))
    for xi in range(len(xs_sorted) - 1):
        x0, x1 = xs_sorted[xi] + 0.55, xs_sorted[xi + 1] - 0.55
        fig.add_annotation(
            x=x1, y=0, ax=x0, ay=0,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.2,
            arrowwidth=1.5, arrowcolor="rgba(99,179,237,0.4)",
        )

    for xi, (emoji, label_d, desc_d, prot) in enumerate(steps):
        label = _p(lang, label_d)
        desc = _p(lang, desc_d)
        sc = impacts.get(prot, 0.0) if prot else 0.0
        box_color  = _impact_color(sc)
        fill_alpha = 0.10 if sc == 0.0 else 0.18
        line_alpha = 0.35 if sc == 0.0 else 0.60

        fig.add_shape(type="rect",
            x0=xi - 0.5, y0=-0.9, x1=xi + 0.5, y1=0.9,
            fillcolor=_hex_rgba(box_color, fill_alpha),
            line=dict(color=_hex_rgba(box_color, line_alpha), width=1.5),
            layer="below",
        )
        if prot:
            tag_sc  = impacts.get(prot, 0.0)
            tag_sym = "▲" if tag_sc > 0.1 else ("▼" if tag_sc < -0.1 else "●")
            tag_col = _impact_color(tag_sc)
            fig.add_annotation(
                x=xi, y=1.15, text=f"<span style='color:{tag_col};font-size:10px'>{tag_sym} {prot}</span>",
                showarrow=False, font=dict(size=9.5, color=tag_col), align="center",
            )

        fig.add_annotation(
            x=xi, y=0.45, text=f"<b>{emoji} {label}</b>",
            showarrow=False, font=dict(size=10, color="#e2e8f0"), align="center",
        )
        for li, line in enumerate(desc.split("\n")):
            fig.add_annotation(
                x=xi, y=0.05 - li * 0.38, text=f"<span style='color:#a0aec0;font-size:9px'>{line}</span>",
                showarrow=False, font=dict(size=9, color="#a0aec0"), align="center",
            )

    _VAX_LABELS = {"mRNA": _u("mrna_lbl", lang), "adenoviral_vector": _u("adeno_lbl", lang),
                   "protein_subunit": _u("prot_lbl", lang)}
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=300,
        xaxis=dict(visible=False, range=[-0.8, max_x + 0.3]),
        yaxis=dict(visible=False, range=[-1.3, 1.6]),
        margin=dict(l=10, r=10, t=45, b=10),
        title=dict(
            text=f"<b>{_u('mech_title_prefix', lang)}</b> — {_VAX_LABELS.get(platform, platform)}",
            font=dict(size=13, color="#e2e8f0"),
        ),
        font=dict(family="Inter,sans-serif"),
        showlegend=False,
    )
    return fig


# ── Plot 4: Variant × Platform Heatmap ────────────────────────────────────────

def _plot_impact_heatmap(impacts: dict[str, float], lang: str = "es"):
    proteins   = list(_PROTEINS.keys())
    platforms  = ["mRNA", "adenoviral_vector", "protein_subunit"]
    plat_labels = [_u("mrna_lbl", lang), _u("adeno_lbl", lang), _u("prot_lbl", lang)]

    _VAX_WEIGHT = {
        "TLR4":    {"mRNA": 0.6, "adenoviral_vector": 0.7, "protein_subunit": 1.0},
        "HLA-DRB1":{"mRNA": 0.9, "adenoviral_vector": 0.8, "protein_subunit": 0.9},
        "APOE":    {"mRNA": 1.0, "adenoviral_vector": 0.05, "protein_subunit": 0.05},
        "IL-6":    {"mRNA": 0.7, "adenoviral_vector": 0.7, "protein_subunit": 0.4},
        "TMPRSS2": {"mRNA": 0.6, "adenoviral_vector": 0.6, "protein_subunit": 0.2},
    }

    z, text = [], []
    for prot in proteins:
        row, trow = [], []
        base = impacts.get(prot, 0.0)
        for plat in platforms:
            w = _VAX_WEIGHT.get(prot, {}).get(plat, 0.5)
            val = base * w
            row.append(val)
            sym = "▲" if val > 0.1 else ("▼" if val < -0.1 else "●")
            trow.append(f"{sym} {val:+.2f}")
        z.append(row)
        text.append(trow)

    prot_labels = [f"{_PROTEINS[p]['emoji']} {p}" for p in proteins]
    ticks = _UI.get(lang, _UI["es"])["heatmap_ticks"]
    fig = go.Figure(go.Heatmap(
        z=z, x=plat_labels, y=prot_labels,
        text=text, texttemplate="%{text}",
        textfont=dict(size=12, color="#e2e8f0"),
        colorscale=[
            [0.0, "#7B2D2D"], [0.35, "#f56565"], [0.48, "#ed8936"],
            [0.5, "#2d3748"],
            [0.52, "#48bb78"], [0.65, "#276749"], [1.0, "#1a4731"],
        ],
        zmid=0, zmin=-1, zmax=1,
        colorbar=dict(
            title=_u("heatmap_impact", lang),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=ticks,
            tickfont=dict(size=10), len=0.8,
        ),
        hoverongaps=False,
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=300,
        margin=dict(l=120, r=60, t=50, b=60),
        title=dict(text=_u("heatmap_title", lang), font=dict(size=13, color="#e2e8f0")),
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
        font=dict(family="Inter,sans-serif"),
    )
    return fig


# ── Main render function ───────────────────────────────────────────────────────

def render_proteomics_tab(platform: str, lang: str = "es"):
    patient_dict = None
    report = st.session_state.get("current_analysis_report")

    if report:
        pid = report.get("patient_id")
        cohort = st.session_state.get("cohort_dicts", [])
        patient_dict = next((p for p in cohort if p.get("patient_id") == pid), None)
        if not patient_dict:
            patient_dict = st.session_state.get("custom_profile_patient")
        if not patient_dict:
            from synthetic.patient_personas import PERSONAS
            patient_dict = next((dict(p) for p in PERSONAS if p["patient_id"] == pid), None)

    # ── Header ──
    st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; padding:0.5rem 0 0.8rem 0;">
  <div>
    <div style="font-size:1.6rem; font-weight:800; color:#e2e8f0;">{_u("header", lang)}</div>
    <div style="color:#a0aec0; font-size:0.9rem;">{_u("subtitle", lang)}</div>
  </div>
  <span style="background:rgba(99,179,237,0.1); border:1px solid rgba(99,179,237,0.3);
    border-radius:8px; padding:5px 12px; font-size:0.78rem; color:#63b3ed; font-weight:600;">
    🧬 3Dmol.js · RCSB PDB · Plotly
  </span>
</div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="synth-mini">{_u("synth", lang)}</div>', unsafe_allow_html=True)

    if not patient_dict:
        st.info(_u("no_patient", lang))
        patient_dict = {
            "patient_id": "DEMO",
            "apoe_genotype": "ε3/ε3",
            "variants": {},
            "hla_haplotype": {"class_I": {"HLA-A": ["HLA-A*02:01"]}, "class_II": {"HLA-DRB1": ["HLA-DRB1*15:01"]}},
        }

    impacts = _patient_protein_impacts(patient_dict)

    # ── Section 1: Protein Network ──
    st.markdown(f'<div class="section-header">{_u("network_hdr", lang)}</div>'
                '<div class="section-line"></div>', unsafe_allow_html=True)
    st.plotly_chart(_plot_protein_network(patient_dict, impacts, platform, lang),
                    use_container_width=True)

    # ── Section 2: 3D Viewer ──
    st.markdown(f'<div class="section-header">{_u("viewer_hdr", lang)}</div>'
                '<div class="section-line"></div>', unsafe_allow_html=True)

    prot_options = list(_PROTEINS.keys())
    prot_labels  = [f"{_PROTEINS[p]['emoji']} {_PROTEINS[p]['full_name']}" for p in prot_options]

    most_impactful = min(impacts, key=lambda k: impacts[k]) if any(v < -0.1 for v in impacts.values()) else "TLR4"
    default_idx    = prot_options.index(most_impactful)

    col_sel, col_info = st.columns([2, 3])
    with col_sel:
        selected_prot = st.selectbox(
            _u("select_protein", lang),
            prot_options, index=default_idx,
            format_func=lambda p: prot_labels[prot_options.index(p)],
            key="prot_3d_select",
        )

    p_data   = _PROTEINS[selected_prot]
    p_impact = impacts.get(selected_prot, 0.0)
    p_color  = _impact_color(p_impact)
    fn_text  = _p(lang, p_data["function"])

    with col_info:
        region_name = _p(lang, p_data.get("region_name", {}))
        st.markdown(f"""
<div class="vg-card" style="border-left:4px solid {p_data['color']}; padding:0.7rem 1rem; margin-top:0.3rem;">
  <div style="font-weight:700; color:{p_data['color']};">{p_data['emoji']} {p_data['full_name']}</div>
  <div style="font-size:0.78rem; color:#718096; margin-top:2px;">PDB: {p_data['pdb_id']} · Module: {p_data['module']}</div>
  <div style="font-size:0.78rem; color:#4fd1c5; margin-top:3px;">📍 {region_name}</div>
  <div style="font-size:0.83rem; color:#a0aec0; margin-top:6px;">{fn_text[:200]}…</div>
  <div style="margin-top:6px; font-size:0.8rem;">
    <span style="color:{p_color}; font-weight:700;">{_u("patient_impact", lang)} {p_impact:+.2f}</span>
  </div>
</div>""", unsafe_allow_html=True)

    variant_lbl = _get_variant_site_label(selected_prot, patient_dict, lang)
    _render_3d_viewer(p_data["pdb_id"], selected_prot,
                      p_data.get("highlight"), p_data["color"],
                      height=440, variant_label=variant_lbl, lang=lang)

    # Vaccine role table for selected protein
    st.markdown(f"**{_u('role_label', lang, selected_prot)}**")
    role_cols = st.columns(3)
    for col, (plat, plat_lbl) in zip(role_cols, [
        ("mRNA", _u("mrna_lbl", lang)),
        ("adenoviral_vector", _u("adeno_lbl", lang)),
        ("protein_subunit", _u("prot_lbl", lang)),
    ]):
        role = _p(lang, p_data["vaccine_role"].get(plat, {}))
        bc = "#63b3ed" if plat == platform else "#4a5568"
        col.markdown(f"""
<div style="background:#151c2c; border:1px solid {bc}40; border-left:3px solid {bc};
     border-radius:8px; padding:0.6rem 0.8rem; font-size:0.82rem;">
  <div style="color:{bc}; font-weight:700; margin-bottom:4px;">{plat_lbl}</div>
  <div style="color:#a0aec0;">{role}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 3: Vaccine Mechanism ──
    st.markdown(f'<div class="section-header">{_u("mechanism_hdr", lang)}</div>'
                '<div class="section-line"></div>', unsafe_allow_html=True)
    st.plotly_chart(_plot_vaccine_mechanism(platform, impacts, lang), use_container_width=True)
    st.caption(_u("legend", lang))

    # ── Section 4: Impact Heatmap ──
    st.markdown(f'<div class="section-header">{_u("heatmap_hdr", lang)}</div>'
                '<div class="section-line"></div>', unsafe_allow_html=True)
    st.plotly_chart(_plot_impact_heatmap(impacts, lang), use_container_width=True)

    # Protein cards row
    st.markdown(f'<div class="section-header" style="margin-top:0.5rem;">{_u("protein_cards_hdr", lang)}</div>'
                '<div class="section-line"></div>', unsafe_allow_html=True)
    prot_cols = st.columns(len(_PROTEINS))
    for col, (pname, pdata) in zip(prot_cols, _PROTEINS.items()):
        sc = impacts.get(pname, 0.0)
        bc = _impact_color(sc)
        col.markdown(f"""
<div class="vg-card" style="text-align:center; min-height:175px; border-top:3px solid {bc};">
  <div style="font-size:1.6rem;">{pdata['emoji']}</div>
  <div style="font-weight:700; color:{bc}; font-size:0.85rem; margin-top:4px;">{pname}</div>
  <div style="color:#718096; font-size:0.7rem; margin-top:2px;">PDB {pdata['pdb_id']}</div>
  <div style="font-size:0.65rem; color:#4fd1c5; margin-top:3px; line-height:1.3;">{pdata.get('highlight_residue','')}</div>
  <div style="font-size:1.2rem; font-weight:800; color:{bc}; margin-top:6px;">{sc:+.2f}</div>
  <div style="font-size:0.68rem; color:#4a5568;">{_u("impact_label", lang)}</div>
</div>""", unsafe_allow_html=True)
