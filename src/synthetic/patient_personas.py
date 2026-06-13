"""
Synthetic patient personas for the VaccineGenics Agent Council demo.

Each persona is a pre-defined patient with a narrative backstory,
interesting genetic findings, and a medical context that exercises
a different part of the pharmacogenomics engine.

ALL DATA IS SYNTHETIC — for research and educational purposes only.
"""

from typing import TypedDict


class PatientPersona(TypedDict):
    patient_id: str
    name: str
    age: int
    sex: str
    ethnicity: str
    backstory: str                  # narrative description shown in UI
    special_condition: str          # SpecialCondition slug
    apoe_genotype: str
    hla_haplotype: list[str]
    variants: dict[str, dict]
    target_vaccine: str
    why_interesting: str            # one-line hook for the UI


# ── 8 clinical demo personas ─────────────────────────────────────────────────

PERSONAS: list[PatientPersona] = [

    # 1 ── María: trasplante renal + APOE ε4/ε4 → mRNA-LNP contraindicada ──────
    {
        "patient_id": "DEMO-MARIA",
        "name": "María",
        "age": 52,
        "sex": "Female",
        "ethnicity": "Latino",
        "backstory": (
            "María, 52 años, recibió un trasplante de riñón hace 3 años. "
            "Está en tratamiento inmunosupresor (tacrolimus + micofenolato). "
            "Su médico quiere vacunarla contra COVID-19 pero hay dudas sobre "
            "qué plataforma es segura dada su genética."
        ),
        "special_condition": "solid_organ_transplant",
        "apoe_genotype": "ε4/ε4",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*02:01"], "HLA-B": ["HLA-B*07:02"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*15:01"], "HLA-DQB1": ["HLA-DQB1*06:02"]},
        },
        "variants": {
            "rs429358": {"genotype": "C/C", "risk_allele": "C", "gene": "APOE"},
            "rs7412":   {"genotype": "T/T", "risk_allele": "T", "gene": "APOE"},
            "rs4986790": {"genotype": "G/G", "risk_allele": "A", "gene": "TLR4"},
            "rs4986791": {"genotype": "C/C", "risk_allele": "T", "gene": "TLR4"},
            "rs1800795": {"genotype": "G/G", "risk_allele": "C", "gene": "IL6"},
            "rs2070788": {"genotype": "A/G", "risk_allele": "G", "gene": "TMPRSS2"},
            "rs8099917": {"genotype": "T/T", "risk_allele": "G", "gene": "IFNL3"},
        },
        "target_vaccine": "mRNA",
        "why_interesting": (
            "APOE ε4/ε4 + trasplante = mRNA-LNP contraindicada por doble riesgo. "
            "El Crítico desafiará si la subunidad proteica es realmente segura."
        ),
    },

    # 2 ── Carlos: joven sano, AFR, buen respondedor ───────────────────────────
    {
        "patient_id": "DEMO-CARLOS",
        "name": "Carlos",
        "age": 30,
        "sex": "Male",
        "ethnicity": "African",
        "backstory": (
            "Carlos, 30 años, atleta sin condiciones médicas. Su ancestría africana "
            "introduce variantes de IL-6 con distribución diferente a la población "
            "europea. Su perfil TLR es wildtype — candidato ideal para comparar "
            "cómo la ancestría afecta la predicción."
        ),
        "special_condition": "none",
        "apoe_genotype": "ε3/ε3",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*30:01"], "HLA-B": ["HLA-B*42:01"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*03:01"], "HLA-DQB1": ["HLA-DQB1*02:01"]},
        },
        "variants": {
            "rs4986790": {"genotype": "G/G", "risk_allele": "A", "gene": "TLR4"},
            "rs4986791": {"genotype": "C/C", "risk_allele": "T", "gene": "TLR4"},
            "rs1800795": {"genotype": "G/C", "risk_allele": "C", "gene": "IL6"},
            "rs2070788": {"genotype": "G/G", "risk_allele": "G", "gene": "TMPRSS2"},
            "rs429358":  {"genotype": "T/T", "risk_allele": "C", "gene": "APOE"},
            "rs7412":    {"genotype": "C/C", "risk_allele": "T", "gene": "APOE"},
        },
        "target_vaccine": "adenoviral_vector",
        "why_interesting": (
            "Perfil de alto respondedor — el Crítico cuestionará si rs2070788 GG "
            "tiene penetrancia suficiente para cambiar la plataforma recomendada."
        ),
    },

    # 3 ── Elena: VIH positiva + HLA-DRB1*11:04 (riesgo VITT) ─────────────────
    {
        "patient_id": "DEMO-ELENA",
        "name": "Elena",
        "age": 45,
        "sex": "Female",
        "ethnicity": "European",
        "backstory": (
            "Elena, 45 años, vive con VIH bien controlado (CD4=580, carga viral "
            "indetectable con TAR). Porta HLA-DRB1*11:04, que la pone en riesgo "
            "de VITT con vacunas adenovirales. La pregunta clínica es cuál de las "
            "dos plataformas restantes es más apropiada para su perfil inmune."
        ),
        "special_condition": "hiv_controlled",
        "apoe_genotype": "ε3/ε4",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*01:01"], "HLA-B": ["HLA-B*08:01"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*11:04"], "HLA-DQB1": ["HLA-DQB1*03:01"]},
        },
        "variants": {
            "rs4986790": {"genotype": "A/G", "risk_allele": "A", "gene": "TLR4"},
            "rs4986791": {"genotype": "T/C", "risk_allele": "T", "gene": "TLR4"},
            "rs1800795": {"genotype": "C/C", "risk_allele": "C", "gene": "IL6"},
            "rs2070788": {"genotype": "A/A", "risk_allele": "G", "gene": "TMPRSS2"},
            "rs429358":  {"genotype": "T/C", "risk_allele": "C", "gene": "APOE"},
            "rs7412":    {"genotype": "C/C", "risk_allele": "T", "gene": "APOE"},
        },
        "target_vaccine": "adenoviral_vector",
        "why_interesting": (
            "HLA-DRB1*11:04 = VITT con adenoviral. VIH penaliza θ. "
            "El consejo debe recomendar subunidad proteica y explicar por qué."
        ),
    },

    # 4 ── David: APOE ε4/ε4 + EAS + alta carga IL-6 ──────────────────────────
    {
        "patient_id": "DEMO-DAVID",
        "name": "David",
        "age": 68,
        "sex": "Male",
        "ethnicity": "East Asian",
        "backstory": (
            "David, 68 años, de origen coreano, sin condiciones crónicas graves "
            "pero con perfil genético de alto riesgo inflamatorio. Su IL-6 muestra "
            "el haplotipo de alta actividad (EAS tiene alta frecuencia del alelo G), "
            "y su edad avanzada amplifica el riesgo de respuesta inflamatoria excesiva."
        ),
        "special_condition": "none",
        "apoe_genotype": "ε4/ε4",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*33:03"], "HLA-B": ["HLA-B*58:01"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*09:01"], "HLA-DQB1": ["HLA-DQB1*03:03"]},
        },
        "variants": {
            "rs429358":  {"genotype": "C/C", "risk_allele": "C", "gene": "APOE"},
            "rs7412":    {"genotype": "T/T", "risk_allele": "T", "gene": "APOE"},
            "rs1800795": {"genotype": "G/G", "risk_allele": "C", "gene": "IL6"},
            "rs4986790": {"genotype": "G/G", "risk_allele": "A", "gene": "TLR4"},
            "rs2070788": {"genotype": "G/G", "risk_allele": "G", "gene": "TMPRSS2"},
            "rs8099917": {"genotype": "G/T", "risk_allele": "G", "gene": "IFNL3"},
        },
        "target_vaccine": "mRNA",
        "why_interesting": (
            "APOE ε4/ε4 + EAS + 68 años = múltiples factores de riesgo superpuestos. "
            "El debate entre agentes será especialmente rico."
        ),
    },

    # 5 ── Sofía: cáncer activo + APOE ε3/ε4 → penalización θ severa ────────────
    {
        "patient_id": "DEMO-SOFIA",
        "name": "Sofía",
        "age": 41,
        "sex": "Female",
        "ethnicity": "Latino",
        "backstory": (
            "Sofía, 41 años, en quimioterapia por cáncer de mama estadio III "
            "(ciclofosfamida + doxorrubicina). Linfopenia marcada (CD4=180). "
            "Su oncóloga quiere vacunarla contra influenza y COVID-19 durante "
            "la ventana entre ciclos. APOE ε3/ε4 añade riesgo moderado con LNP."
        ),
        "special_condition": "cancer_active_treatment",
        "apoe_genotype": "ε3/ε4",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*02:01"], "HLA-B": ["HLA-B*44:02"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*07:01"], "HLA-DQB1": ["HLA-DQB1*02:01"]},
        },
        "variants": {
            "rs429358":  {"genotype": "C/T", "risk_allele": "C", "gene": "APOE"},
            "rs7412":    {"genotype": "C/C", "risk_allele": "T", "gene": "APOE"},
            "rs4986790": {"genotype": "A/G", "risk_allele": "A", "gene": "TLR4"},
            "rs4986791": {"genotype": "C/T", "risk_allele": "T", "gene": "TLR4"},
            "rs1800795": {"genotype": "C/C", "risk_allele": "C", "gene": "IL6"},
            "rs2070788": {"genotype": "A/A", "risk_allele": "G", "gene": "TMPRSS2"},
        },
        "target_vaccine": "protein_subunit",
        "why_interesting": (
            "Quimio = θ -0.60 + APOE ε3/ε4 + IL-6 C/C. "
            "El consejo debe debatir si vacunar entre ciclos y qué plataforma minimiza el riesgo."
        ),
    },

    # 6 ── Marco: pediátrico 9 años, alto respondedor HLA ────────────────────────
    {
        "patient_id": "DEMO-MARCO",
        "name": "Marco",
        "age": 9,
        "sex": "Male",
        "ethnicity": "European",
        "backstory": (
            "Marco, 9 años, sin condiciones crónicas. Sus padres son investigadores "
            "de genómica y quieren saber si el perfil HLA de su hijo lo pone en "
            "categoría de alto respondedor vacunal. HLA-A*02:01 + DRB1*01:01 = "
            "combinación asociada a respuestas robustas en estudios de vacunas pediátricas."
        ),
        "special_condition": "none",
        "apoe_genotype": "ε3/ε3",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*02:01"], "HLA-B": ["HLA-B*35:01"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*01:01"], "HLA-DQB1": ["HLA-DQB1*05:01"]},
        },
        "variants": {
            "rs4986790": {"genotype": "G/G", "risk_allele": "A", "gene": "TLR4"},
            "rs4986791": {"genotype": "C/C", "risk_allele": "T", "gene": "TLR4"},
            "rs1800795": {"genotype": "G/G", "risk_allele": "C", "gene": "IL6"},
            "rs2070788": {"genotype": "A/A", "risk_allele": "G", "gene": "TMPRSS2"},
            "rs429358":  {"genotype": "T/T", "risk_allele": "C", "gene": "APOE"},
            "rs7412":    {"genotype": "C/C", "risk_allele": "T", "gene": "APOE"},
        },
        "target_vaccine": "mRNA",
        "why_interesting": (
            "Perfil genético excelente + edad pediátrica. "
            "El debate girará en torno a dosificación ajustada por edad vs riesgo miocarditis en varones jóvenes."
        ),
    },

    # 7 ── Fátima: VIH severo + TLR7 LOF + HLA VITT → caso extremo ──────────────
    {
        "patient_id": "DEMO-FATIMA",
        "name": "Fátima",
        "age": 38,
        "sex": "Female",
        "ethnicity": "African",
        "backstory": (
            "Fátima, 38 años, VIH severo con CD4=85 (sin acceso estable a TAR). "
            "Porta TLR7 rs179008 LOF (homocigota, ligado al X) — respuesta innata "
            "a ssRNA severamente reducida. Además HLA-DRB1*11:04 la pone en riesgo "
            "de VITT con vectores adenovirales. Las tres plataformas presentan riesgos."
        ),
        "special_condition": "hiv_severe",
        "apoe_genotype": "ε3/ε3",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*23:01"], "HLA-B": ["HLA-B*53:01"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*11:04"], "HLA-DQB1": ["HLA-DQB1*03:01"]},
        },
        "variants": {
            "rs4986790": {"genotype": "A/G", "risk_allele": "A", "gene": "TLR4"},
            "rs4986791": {"genotype": "C/T", "risk_allele": "T", "gene": "TLR4"},
            "rs179008":  {"genotype": "A/A", "risk_allele": "A", "gene": "TLR7"},
            "rs1800795": {"genotype": "G/C", "risk_allele": "C", "gene": "IL6"},
            "rs2070788": {"genotype": "A/A", "risk_allele": "G", "gene": "TMPRSS2"},
            "rs429358":  {"genotype": "T/T", "risk_allele": "C", "gene": "APOE"},
            "rs7412":    {"genotype": "C/C", "risk_allele": "T", "gene": "APOE"},
        },
        "target_vaccine": "protein_subunit",
        "why_interesting": (
            "VIH severo + TLR7 LOF + VITT risk = el caso más complejo del consejo. "
            "El Crítico tendrá material para cuestionar todas las recomendaciones."
        ),
    },

    # 8 ── Roberto: artritis reumatoide + biológicos + IL-6 alta carga ──────────
    {
        "patient_id": "DEMO-ROBERTO",
        "name": "Roberto",
        "age": 60,
        "sex": "Male",
        "ethnicity": "European",
        "backstory": (
            "Roberto, 60 años, artritis reumatoide severa en tratamiento con "
            "tocilizumab (anti-IL-6R) desde hace 2 años. Paradójicamente, su gen "
            "IL-6 tiene el haplotipo de alta expresión, que el tocilizumab bloquea "
            "pero que afecta la señalización post-vacunal. APOE ε3/ε4 moderado."
        ),
        "special_condition": "autoimmune_on_biologics",
        "apoe_genotype": "ε3/ε4",
        "hla_haplotype": {
            "class_I":  {"HLA-A": ["HLA-A*01:01"], "HLA-B": ["HLA-B*08:01"]},
            "class_II": {"HLA-DRB1": ["HLA-DRB1*04:01"], "HLA-DQB1": ["HLA-DQB1*03:01"]},
        },
        "variants": {
            "rs4986790": {"genotype": "G/G", "risk_allele": "A", "gene": "TLR4"},
            "rs4986791": {"genotype": "C/C", "risk_allele": "T", "gene": "TLR4"},
            "rs1800795": {"genotype": "C/C", "risk_allele": "C", "gene": "IL6"},
            "rs1137578": {"genotype": "A/G", "risk_allele": "G", "gene": "STAT3"},
            "rs2070788": {"genotype": "A/G", "risk_allele": "G", "gene": "TMPRSS2"},
            "rs429358":  {"genotype": "C/T", "risk_allele": "C", "gene": "APOE"},
            "rs7412":    {"genotype": "C/C", "risk_allele": "T", "gene": "APOE"},
        },
        "target_vaccine": "mRNA",
        "why_interesting": (
            "Tocilizumab bloquea IL-6R pero el gen sigue siendo C/C. "
            "Debate sobre timing vacunal relativo a la dosis de biológico."
        ),
    },
]


# ── Lookup helpers ────────────────────────────────────────────────────────────

def get_persona(name_or_id: str) -> PatientPersona | None:
    """Return persona by name ('María') or patient_id ('DEMO-MARIA')."""
    needle = name_or_id.upper()
    for p in PERSONAS:
        if p["patient_id"].upper() == needle or p["name"].upper() == needle:
            return p
    return None


def persona_display_names() -> list[str]:
    return [f"{p['name']} — {p['backstory'][:60]}…" for p in PERSONAS]


_ETH_ES = {
    "Latino": "Latino", "African": "Africano", "European": "Europeo",
    "East Asian": "Asiático del Este", "South Asian": "Asiático del Sur",
    "Mixed": "Mixto", "Unknown": "Desconocido",
}
_COND_ES = {
    "none": "Sano/a",
    "solid_organ_transplant": "Trasplante órgano sólido",
    "hiv_controlled": "VIH controlado",
    "hiv_moderate": "VIH moderado",
    "hiv_severe": "VIH severo",
    "cancer_active_treatment": "Cáncer activo",
    "cancer_remission": "Cáncer en remisión",
    "radiation_exposure": "Exposición a radiación",
    "bone_marrow_transplant_recent": "TMO reciente",
    "bone_marrow_transplant_established": "TMO establecido",
    "autoimmune_on_biologics": "Autoinmune – biológicos",
    "autoimmune_on_steroids": "Autoinmune – corticoides",
}


def persona_short_labels() -> list[str]:
    return [
        (
            f"{p['name']} ({p['age']} años · "
            f"{_ETH_ES.get(p['ethnicity'], p['ethnicity'])} · "
            f"{_COND_ES.get(p['special_condition'], p['special_condition'])})"
        )
        for p in PERSONAS
    ]
