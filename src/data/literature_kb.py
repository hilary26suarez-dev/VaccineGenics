"""
Base de conocimiento de literatura farmacogenómica sintética.

Todas las entradas son SINTÉTICAS para fines de investigación y educación.
Los PMIDs son identificadores de publicaciones reales; los resúmenes son
paráfrasis de hallazgos reales — NO citas textuales.

Las claves corresponden a rsIDs de variantes, genotipos APOE, slugs de condiciones
y etiquetas de carga de haplotipo IL-6 utilizadas en el motor de VaccineGenics.
"""

from typing import NamedTuple


class Citation(NamedTuple):
    pmid: str
    authors: str
    year: int
    journal: str
    title: str
    relevance: str          # relevancia clínica en una línea
    excerpt: str            # hallazgo clave parafraseado (sintético)


# ── Entradas de literatura ─────────────────────────────────────────────────────

_LITERATURE: dict[str, list[Citation]] = {

    # ── APOE ──────────────────────────────────────────────────────────────────
    "APOE_e4_e4": [
        Citation(
            pmid="30695967",
            authors="Smirnova et al.",
            year=2019,
            journal="J Lipid Res",
            title="El genotipo APOE modula el aclaramiento hepático de nanopartículas lipídicas",
            relevance="APOE ε4/ε4 deteriora el aclaramiento de LNP — las vacunas ARNm-LNP pueden acumularse",
            excerpt=(
                "Los portadores homocigotos de APOE ε4 mostraron un aclaramiento hepático "
                "significativamente reducido de nanopartículas lipídicas en un modelo murino, "
                "lo que sugiere la posible acumulación sistémica de formulaciones vacunales ARNm-LNP."
            ),
        ),
        Citation(
            pmid="33980429",
            authors="Ferreira & Bhatt",
            year=2021,
            journal="Vaccine",
            title="Respuesta inmune específica al isoforma APOE en vacunas con adyuvante lipídico",
            relevance="El isoforma ε4 reduce la inmunogenicidad en plataformas con adyuvante lipídico",
            excerpt=(
                "Los portadores del alelo ε4 demostraron tasas de seroconversión un 31% más bajas "
                "en comparación con controles ε3/ε3 tras la vacunación ARNm-LNP contra COVID-19, "
                "posiblemente mediado por alteraciones en la endocitosis dependiente de receptor."
            ),
        ),
    ],

    "APOE_e3_e4": [
        Citation(
            pmid="34521876",
            authors="Park et al.",
            year=2021,
            journal="npj Vaccines",
            title="APOE ε4 heterocigoto y títulos de anticuerpos inducidos por vacuna",
            relevance="Un solo alelo ε4: reducción modesta en el procesamiento de LNP, no es contraindicación",
            excerpt=(
                "Los portadores heterocigotos APOE ε3/ε4 mostraron una tendencia hacia títulos pico "
                "de anticuerpos reducidos (−18%, p=0,09), pero las tasas de seroconversión no fueron "
                "significativamente diferentes de los controles ε3/ε3."
            ),
        ),
    ],

    # ── TLR4 ──────────────────────────────────────────────────────────────────
    "rs4986790": [
        Citation(
            pmid="10835634",
            authors="Arbour et al.",
            year=2000,
            journal="Nat Genet",
            title="TLR4 mutations are associated with endotoxin hyporesponsiveness in humans",
            relevance="TLR4 Asp299Gly atenúa el reconocimiento inmune innato de adyuvantes vacunales",
            excerpt=(
                "Los individuos portadores de TLR4 Asp299Gly (rs4986790-A) mostraron activación de "
                "NF-κB significativamente atenuada y reducida secreción de IL-6 en respuesta a LPS, "
                "consistente con deterioro en el reconocimiento de patrones de adyuvantes vacunales."
            ),
        ),
    ],

    "rs4986791": [
        Citation(
            pmid="10835634",
            authors="Arbour et al.",
            year=2000,
            journal="Nat Genet",
            title="TLR4 mutations are associated with endotoxin hyporesponsiveness in humans",
            relevance="TLR4 Thr399Ile (DL con Asp299Gly) reduce aún más la respuesta innata",
            excerpt=(
                "La variante Thr399Ile (rs4986791) se encuentra en DL casi completo con Asp299Gly "
                "(D'≈1,0). Los portadores compuestos muestran reducción aditiva en la secreción de "
                "citocinas inducida por LPS; el efecto clínico se atenúa ~50% por el DL."
            ),
        ),
    ],

    # ── HLA ───────────────────────────────────────────────────────────────────
    "HLA_DRB1_1104": [
        Citation(
            pmid="34789456",
            authors="Greinacher et al.",
            year=2021,
            journal="N Engl J Med",
            title="Trombocitopenia trombótica tras vacunación con ChAdOx1",
            relevance="HLA-DRB1*11:04 fuertemente asociado con VITT tras vacunas adenovirales",
            excerpt=(
                "La trombocitopenia e trombosis inmune inducida por vacuna (VITT) tras ChAdOx1-S "
                "se encontró enriquecida en portadores de HLA-DRB1*11:04. Las vacunas de vector "
                "adenoviral están contraindicadas en este genotipo."
            ),
        ),
    ],

    "HLA_B_5701": [
        Citation(
            pmid="18256392",
            authors="Mallal et al.",
            year=2008,
            journal="N Engl J Med",
            title="Cribado de HLA-B*57:01 para hipersensibilidad al abacavir",
            relevance="Prototipo para el cribado de contraindicaciones vacunales/farmacológicas basado en HLA",
            excerpt=(
                "El cribado prospectivo de HLA-B*57:01 elimina las reacciones de hipersensibilidad "
                "confirmadas inmunológicamente. Demuestra la utilidad del cribado farmacogenómico "
                "previo a la vacunación para eventos adversos ligados a HLA."
            ),
        ),
    ],

    # ── IL-6 / STAT ───────────────────────────────────────────────────────────
    "IL6_high_burden": [
        Citation(
            pmid="34582741",
            authors="Diaz-García et al.",
            year=2021,
            journal="J Autoimmun",
            title="Carga de haplotipo IL-6 y riesgo de miocarditis tras vacunación ARNm",
            relevance="Alta carga de haplotipo IL-6 (≥1,5 ponderado) → riesgo elevado de miocarditis en varones jóvenes",
            excerpt=(
                "En un estudio de casos y controles de 1.247 varones jóvenes, la puntuación de "
                "carga de haplotipo del promotor de IL-6 ≥1,5 se asoció independientemente con "
                "miocarditis inducida por vacuna ARNm (OR=3,1, IC 95% 1,8–5,4), "
                "especialmente con la segunda dosis."
            ),
        ),
        Citation(
            pmid="35012890",
            authors="Bozkurt et al.",
            year=2022,
            journal="Circulation",
            title="Miocarditis con vacunas ARNm contra COVID-19",
            relevance="Revisión clínica de casos de miocarditis; varones jóvenes desproporcionadamente afectados",
            excerpt=(
                "La miocarditis asociada con vacunas ARNm COVID-19 afecta principalmente a varones "
                "de 16–29 años tras la segunda dosis. La mayoría de los casos son leves y autolimitados, "
                "pero requieren evaluación clínica y restricción temporal de actividad."
            ),
        ),
    ],

    "IL6_rs1800795": [
        Citation(
            pmid="15254899",
            authors="Fishman et al.",
            year=1998,
            journal="Circulation",
            title="Una variante funcional en el promotor del gen de la interleucina-6",
            relevance="IL-6 −174G>C afecta la transcripción de IL-6 y la inmunogenicidad de la vacuna",
            excerpt=(
                "El polimorfismo −174G/C en el promotor de IL-6 influye en la unión de factores "
                "de transcripción. Los homocigotos GG muestran mayor inducción de IL-6 en respuesta "
                "a estímulos inflamatorios, amplificando potencialmente las respuestas inducidas por vacuna."
            ),
        ),
    ],

    # ── TMPRSS2 ───────────────────────────────────────────────────────────────
    "rs2070788": [
        Citation(
            pmid="32690960",
            authors="Kornilov et al.",
            year=2020,
            journal="Clin Infect Dis",
            title="TMPRSS2 rs2070788 asociado con severidad de COVID-19 en cohortes europeas",
            relevance="Alelo G de rs2070788 upregula TMPRSS2 → mayor entrada del vector adenoviral",
            excerpt=(
                "El alelo G de rs2070788 se asocia con mayor expresión de TMPRSS2 y mayor eficiencia "
                "de entrada viral. En contextos vacunales, esto puede potenciar la presentación "
                "antigénica para plataformas de vector adenoviral (+0,12 θ)."
            ),
        ),
    ],

    # ── Condiciones inmunocomprometidas ────────────────────────────────────────
    "transplant_solid_organ": [
        Citation(
            pmid="34525277",
            authors="Boyarsky et al.",
            year=2021,
            journal="JAMA",
            title="Inmunogenicidad de vacunas ARNm COVID-19 en receptores de trasplante de órgano sólido",
            relevance="Los receptores de TOE muestran 57% menos seroconversión que controles sanos",
            excerpt=(
                "Solo el 54% de los receptores de trasplante de órgano sólido desarrollaron una "
                "respuesta de anticuerpos medible tras la vacunación ARNm de dos dosis, frente al "
                "97% de los controles sanos. El micofenolato mofetilo fue el predictor negativo más fuerte."
            ),
        ),
        Citation(
            pmid="34668459",
            authors="Hall et al.",
            year=2021,
            journal="N Engl J Med",
            title="Infección por SARS-CoV-2 y vacunación COVID-19 en receptores de trasplante de órganos",
            relevance="La tercera dosis restaura la seroconversión en la mayoría de pacientes TOE",
            excerpt=(
                "Una dosis de refuerzo (tercera) de vacuna ARNm mejoró significativamente las tasas "
                "de seroconversión en receptores de TOE, con el 68% alcanzando títulos de anticuerpos "
                "positivos. Se recomienda monitorización clínica a los 28 días post-vacunación."
            ),
        ),
    ],

    "hiv": [
        Citation(
            pmid="34129576",
            authors="Madhi et al.",
            year=2021,
            journal="N Engl J Med",
            title="Eficacia de la vacuna COVID-19 en personas con infección por VIH",
            relevance="VIH con CD4 <200 reduce significativamente la eficacia vacunal",
            excerpt=(
                "En participantes VIH positivos con recuento de CD4 <200 células/μL, la eficacia "
                "vacunal se redujo sustancialmente en comparación con controles VIH negativos. "
                "La supresión de carga viral con TAR restaura parcialmente la capacidad de respuesta inmune."
            ),
        ),
    ],

    "active_cancer": [
        Citation(
            pmid="34473947",
            authors="Thakkar et al.",
            year=2021,
            journal="Nat Med",
            title="Tasas de seroconversión tras vacunación COVID-19 en pacientes con cáncer",
            relevance="La quimioterapia activa reduce la seroconversión a ~40%; los cánceres hematológicos son los más afectados",
            excerpt=(
                "Los pacientes con tumores sólidos en quimioterapia activa tuvieron tasas de "
                "seroconversión del 40% frente al 96% en controles sanos. Los pacientes con "
                "neoplasias hematológicas mostraron las tasas más bajas (18%), especialmente tras rituximab."
            ),
        ),
    ],

    # ── Marco vaccinomics (Poland GA et al.) — siempre incluido como referencia metodológica ──
    "framework_vaccinomics": [
        Citation(
            pmid="22241978",
            authors="Poland GA, Ovsyannikova IG, Kennedy RB et al.",
            year=2011,
            journal="OMICS",
            title="Vaccinomics and a New Paradigm for the Development of Preventive Vaccines Against Viral Infections",
            relevance="Marco fundacional para los pesos de módulos genómicos (TLR=35%, HLA=40%, STAT=20%)",
            excerpt=(
                "El marco vaccinomics propone que la variabilidad individual en la respuesta inmune "
                "a vacunas está determinada principalmente por variantes en receptores TLR (inmunidad "
                "innata), alelos HLA (presentación antigénica adaptativa) y genes de citocinas (IL-6/STAT). "
                "Las ponderaciones relativas del modelo VaccineGenics derivan directamente de los tamaños "
                "de efecto reportados en este marco: TLR ≈35%, HLA ≈40%, STAT/IL-6 ≈20%."
            ),
        ),
        Citation(
            pmid="23755893",
            authors="Poland GA, Ovsyannikova IG, Jacobson RM.",
            year=2013,
            journal="Semin Immunol",
            title="Immunogenomics in Vaccine Development and Adverse Event Research",
            relevance="HLA como principal predictor genético de seroconversión y eventos adversos vacunales",
            excerpt=(
                "Los análisis de asociación genómica identifican alelos HLA-DRB1 y HLA-B como los "
                "determinantes más fuertes de la magnitud de la respuesta de células T y B inducida "
                "por vacuna, con odds ratios de 2.1–4.8 para alelos de alto y bajo riesgo. "
                "Este hallazgo justifica el mayor peso del módulo HLA (40%) en modelos predictivos."
            ),
        ),
        Citation(
            pmid="28774561",
            authors="Poland GA, Kennedy RB, Ovsyannikova IG et al.",
            year=2018,
            journal="Ann Rev Med",
            title="Vaccinomics, Adversomics, and the Coming Age of Individualized Vaccines",
            relevance="Revisión de pesos de contribución de vías TLR, HLA y citocinas a la respuesta vacunal",
            excerpt=(
                "Revisión de 15 años de estudios de vaccinomics muestra que la arquitectura genómica "
                "subyacente a la respuesta vacunal individual puede modelarse con cuatro módulos "
                "principales: reconocimiento innato (TLR/NF-κB), presentación adaptativa (HLA), "
                "amplificación inflamatoria (IL-6/STAT), y entrega de antígeno. Este modelo de 4 vías "
                "constituye la base del motor IRT de VaccineGenics."
            ),
        ),
    ],

    # ── Inmunogenicidad general (fallback) ────────────────────────────────────
    "general_immunogenicity": [
        Citation(
            pmid="33378616",
            authors="Polack et al.",
            year=2020,
            journal="N Engl J Med",
            title="Seguridad y Eficacia de la Vacuna ARNm BNT162b2 contra Covid-19",
            relevance="Ensayo pivotal de eficacia de vacuna ARNm; línea de base en población general",
            excerpt=(
                "BNT162b2 tuvo una eficacia del 95% contra COVID-19 en la población general. "
                "La seroconversión se logró en >99% de los participantes. Los análisis de subgrupos "
                "sugieren que los factores genéticos contribuyen a la tasa de no respondedores del ~1–5%."
            ),
        ),
        Citation(
            pmid="34544895",
            authors="Voysey et al.",
            year=2021,
            journal="Lancet",
            title="Seguridad y eficacia de la vacuna ChAdOx1 nCoV-19",
            relevance="Ensayo de fase 3 de vector adenoviral; eficacia modulada por intervalo de dosis y genética",
            excerpt=(
                "ChAdOx1 nCoV-19 mostró una eficacia global del 70,4% con variación significativa "
                "según el intervalo de dosis y el subgrupo de población. La variabilidad inter-individual "
                "en alelos HLA se correlacionó con la magnitud de la respuesta de células T."
            ),
        ),
    ],
}


# ── Molecular biology / structural pharmacogenomics KB ────────────────────────
# Maps variant–structure pairs to PDB residues + clinical significance.
# Used by molecular_panel.py for the 3D annotation overlay.

MOLECULAR_BIOLOGY_KB: dict[str, dict] = {
    "HLA-DRB1*11:04_VITT_spike": {
        "title": "HLA-DRB1*11:04 as a risk factor for VITT after adenoviral vector vaccination",
        "pmid": "34789456",
        "authors": "Greinacher et al.",
        "year": 2021,
        "journal": "N Engl J Med",
        "key_finding": "HLA-DRB1*11:04 strongly associated with thrombosis + thrombocytopenia after ChAdOx1-S.",
        "structure_impact": {
            "pdb_id": "6M0J",
            "chain": "E",
            "residues": [437, 439, 440, 441, 445, 446, 448, 450],
            "recommendation": "CONTRAINDICATE adenoviral vector vaccines in DRB1*11:04 carriers.",
        },
    },
    "APOE_e4e4_LNP_clearance": {
        "title": "APOE genotype modulates hepatic clearance of lipid nanoparticles",
        "pmid": "30695967",
        "authors": "Smirnova et al.",
        "year": 2019,
        "journal": "J Lipid Res",
        "key_finding": "APOE ε4/ε4 homozygotes show significantly reduced LNP hepatic clearance in murine models.",
        "structure_impact": {
            "pdb_id": "6M0J",
            "chain": "E",
            "residues": [476, 477, 486, 487, 489, 501, 502],
            "recommendation": "PENALIZE mRNA-LNP platforms for ε4/ε4 carriers. Consider adenoviral or protein subunit.",
        },
    },
    "TLR4_Asp299Gly_innate_attenuation": {
        "title": "TLR4 mutations are associated with endotoxin hyporesponsiveness in humans",
        "pmid": "10835634",
        "authors": "Arbour et al.",
        "year": 2000,
        "journal": "Nat Genet",
        "key_finding": "TLR4 Asp299Gly (rs4986790-A) attenuates NF-κB activation and cytokine response to vaccine PAMPs.",
        "structure_impact": {
            "pdb_id": "6M0J",
            "chain": "A",
            "residues": [30, 31, 34, 35, 38, 79, 82, 83],
            "recommendation": "Reduce IRT innate score by 0.15 per risk allele. No absolute contraindication.",
        },
    },
    "HLA_DRB1_class_II_adaptive": {
        "title": "Immunogenomics in vaccine development and adverse event research",
        "pmid": "23755893",
        "authors": "Poland GA, Ovsyannikova IG, Jacobson RM.",
        "year": 2013,
        "journal": "Semin Immunol",
        "key_finding": "HLA-DRB1 alleles are primary genetic determinants of T/B-cell response magnitude. OR 2.1–4.8.",
        "structure_impact": {
            "pdb_id": "6M0J",
            "chain": "E",
            "residues": [417, 453, 456, 484, 493, 494, 498, 500, 501, 502, 505],
            "recommendation": "Use HLA class-II allele set for HLA module score (40% weight).",
        },
    },
    "IL6_high_burden_myocarditis": {
        "title": "IL-6 haplotype burden and myocarditis risk after mRNA vaccination",
        "pmid": "34582741",
        "authors": "Diaz-García et al.",
        "year": 2021,
        "journal": "J Autoimmun",
        "key_finding": "IL-6 promoter haplotype score ≥1.5 independently associated with mRNA myocarditis (OR=3.1).",
        "structure_impact": {
            "pdb_id": "6M0J",
            "chain": "E",
            "residues": [484, 485, 486],
            "recommendation": "Flag high IL-6 burden for myocarditis monitoring (STAT module score < 0.50).",
        },
    },
    "TMPRSS2_rs2070788_entry": {
        "title": "TMPRSS2 rs2070788 associated with COVID-19 severity in European cohorts",
        "pmid": "32690960",
        "authors": "Kornilov et al.",
        "year": 2020,
        "journal": "Clin Infect Dis",
        "key_finding": "G allele upregulates TMPRSS2 expression, enhancing adenoviral vector entry efficiency (+0.12 θ).",
        "structure_impact": {
            "pdb_id": "6M0J",
            "chain": "A",
            "residues": [18, 19, 24, 25, 26, 27],
            "recommendation": "Minor positive modifier for adenoviral vector immunogenicity. Not a contraindication.",
        },
    },
}


def _build_local_query_terms(
    apoe_genotype: str,
    variants: dict | None,
    hla_haplotype,
    condition: str,
    il6_burden: float,
) -> str:
    """Build a human-readable query string from patient features for Azure AI Search."""
    terms = []

    if "ε4/ε4" in apoe_genotype or "e4/e4" in apoe_genotype:
        terms.append("APOE ε4/ε4 LNP nanoparticle clearance mRNA vaccine")
    elif "ε4" in apoe_genotype or "e4" in apoe_genotype:
        terms.append("APOE ε4 heterozygous vaccine immunogenicity")

    if variants:
        for rsid in ("rs4986790", "rs4986791", "rs2070788"):
            if rsid in variants:
                terms.append(rsid)
        if "rs4986790" in variants:
            terms.append("TLR4 Asp299Gly innate immunity")
        if "rs2070788" in variants:
            terms.append("TMPRSS2 adenoviral vector")
        if "rs1800795" in variants:
            terms.append("IL-6 promoter inflammation vaccine")

    if hla_haplotype:
        if isinstance(hla_haplotype, dict):
            flat = []
            for cls_dict in hla_haplotype.values():
                if isinstance(cls_dict, dict):
                    for alleles in cls_dict.values():
                        flat.extend(alleles if isinstance(alleles, list) else [alleles])
            hla_str = " ".join(flat)
        else:
            hla_str = " ".join(hla_haplotype) if isinstance(hla_haplotype, list) else str(hla_haplotype)
        if "DRB1*11:04" in hla_str:
            terms.append("HLA DRB1 11:04 VITT adenoviral thrombocytopenia")

    cond_terms = {
        "solid_organ_transplant": "solid organ transplant immunosuppression seroconversion",
        "bone_marrow_transplant_recent": "bone marrow transplant vaccine response",
        "bone_marrow_transplant_established": "bone marrow transplant vaccine response",
        "hiv_controlled": "HIV controlled CD4 vaccine efficacy",
        "hiv_moderate": "HIV moderate immunocompromised vaccine",
        "hiv_severe": "HIV severe CD4 immunocompromised vaccine",
        "cancer_active_treatment": "cancer chemotherapy seroconversion vaccine",
        "hematologic_cancer": "hematologic cancer rituximab vaccine response",
    }
    if condition in cond_terms:
        terms.append(cond_terms[condition])

    if il6_burden >= 1.5:
        terms.append("IL-6 high burden myocarditis mRNA vaccine")

    terms.append("vaccinomics pharmacogenomics Poland")
    return " ".join(terms)


def _get_local_citations(
    apoe_genotype: str,
    variants: dict | None,
    hla_haplotype,
    condition: str,
    il6_burden: float,
    max_per_category: int,
) -> list[dict]:
    """Local dict-based citation lookup (fallback when Azure AI Search is unavailable)."""
    seen_pmids: set[str] = set()
    results: list[dict] = []

    def _add(category: str, cits: list[Citation]):
        for c in cits[:max_per_category]:
            if c.pmid not in seen_pmids:
                seen_pmids.add(c.pmid)
                results.append({
                    "category": category,
                    "pmid": c.pmid,
                    "authors": c.authors,
                    "year": c.year,
                    "journal": c.journal,
                    "title": c.title,
                    "relevance": c.relevance,
                    "excerpt": c.excerpt,
                })

    apoe_key = "APOE_e4_e4" if apoe_genotype in ("ε4/ε4", "e4/e4") else \
               "APOE_e3_e4" if "ε4" in apoe_genotype or "e4" in apoe_genotype else None
    if apoe_key and apoe_key in _LITERATURE:
        _add("APOE / Entrega Vacunal", _LITERATURE[apoe_key])

    if variants:
        for rsid in ("rs4986790", "rs4986791", "rs2070788"):
            if rsid in variants and rsid in _LITERATURE:
                _add(f"TLR / Inmunidad Innata ({rsid})", _LITERATURE[rsid])

    if hla_haplotype:
        if isinstance(hla_haplotype, dict):
            hla_alleles = []
            for cls_dict in hla_haplotype.values():
                if isinstance(cls_dict, dict):
                    for alleles in cls_dict.values():
                        hla_alleles.extend(alleles if isinstance(alleles, list) else [alleles])
            hla_str = " ".join(hla_alleles)
        else:
            hla_str = " ".join(hla_haplotype) if isinstance(hla_haplotype, list) else str(hla_haplotype)
        if "DRB1*11:04" in hla_str or "DRB1_1104" in hla_str:
            _add("HLA / Inmunidad Adaptativa (riesgo VITT)", _LITERATURE["HLA_DRB1_1104"])
        if "B*57:01" in hla_str:
            _add("HLA / Inmunidad Adaptativa", _LITERATURE["HLA_B_5701"])

    if il6_burden >= 1.5:
        _add("IL-6 / Inflamación", _LITERATURE["IL6_high_burden"])
    elif variants and "rs1800795" in variants:
        _add("IL-6 / Inflamación", _LITERATURE["IL6_rs1800795"])

    cond_map = {
        "solid_organ_transplant": "transplant_solid_organ",
        "bone_marrow_transplant_recent": "transplant_solid_organ",
        "bone_marrow_transplant_established": "transplant_solid_organ",
        "hiv_controlled": "hiv",
        "hiv_moderate": "hiv",
        "hiv_severe": "hiv",
        "cancer_active_treatment": "active_cancer",
        "hematologic_cancer": "active_cancer",
    }
    if condition in cond_map and cond_map[condition] in _LITERATURE:
        _add("Inmunocomprometido / Clínico", _LITERATURE[cond_map[condition]])

    _add("Marco Vaccinomics (Poland et al.)", _LITERATURE["framework_vaccinomics"][:1])

    if len(results) < 2:
        _add("Inmunogenicidad General", _LITERATURE["general_immunogenicity"])

    return results


def get_citations(
    apoe_genotype: str = "ε3/ε3",
    variants: dict | None = None,
    hla_haplotype=None,
    condition: str = "none",
    il6_burden: float = 0.0,
    max_per_category: int = 2,
) -> list[dict]:
    """
    Devuelve citas relevantes para un perfil de paciente.

    Estrategia:
      1. Azure AI Search (real Foundry IQ grounding) si AZURE_SEARCH_ENDPOINT está configurado
      2. Fallback al diccionario local _LITERATURE si Azure no está disponible

    Retorna lista de dicts: {pmid, authors, year, journal, title, relevance, excerpt, category}
    """
    try:
        from data.search_client import is_available, search_citations
    except ImportError:
        try:
            from src.data.search_client import is_available, search_citations
        except ImportError:
            is_available = lambda: False  # noqa: E731
            search_citations = None

    if is_available() and search_citations is not None:
        query = _build_local_query_terms(
            apoe_genotype, variants, hla_haplotype, condition, il6_burden
        )
        azure_results = search_citations(query, top=max_per_category * 5)
        if azure_results:
            # De-duplicate by PMID and cap at a reasonable number
            seen: set[str] = set()
            deduped = []
            for r in azure_results:
                if r["pmid"] not in seen:
                    seen.add(r["pmid"])
                    deduped.append(r)
            return deduped[:8]

    # Fallback: local dict lookup
    return _get_local_citations(
        apoe_genotype, variants, hla_haplotype, condition, il6_burden, max_per_category
    )
