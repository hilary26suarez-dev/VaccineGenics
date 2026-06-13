"""
VaccineGenics — Precision Vaccine Intelligence Dashboard
"""

import re, html as _html
import streamlit as st
import streamlit.components.v1 as _components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from synthetic.patient_generator import get_or_generate_cohort
from synthetic.patient_personas import PERSONAS as DEMO_PERSONAS, persona_short_labels
from pharmacogenomics.risk_calculator import analyze_patient
from pharmacogenomics.irt_model import irt_4pl
from pharmacogenomics.modules.immunocompromised_module import SpecialCondition
from agent.council import AgentCouncil, PERSONAS as COUNCIL_PERSONAS
from data.literature_kb import get_citations
from config import COHORT_SIZE, VACCINE_IRT_PARAMS
from ui.proteomics_tab import render_proteomics_tab
from ui.reasoning_telemetry import render_reasoning_trace

# ─── i18n ──────────────────────────────────────────────────────────────────
_TRANS: dict[str, dict[str, str]] = {
    "es": {
        "tab_dashboard": "📊 Dashboard de Cohorte",
        "tab_council":   "🎭 Consejo de Agentes IA",
        "tab_custom":    "🧬 Mi Perfil",
        "tab_consult":   "🔬 Consulta Genómica",
        "tab_proteo":    "🧫 Proteómica",
        "lang_btn":      "🌐 English",
        "cohort_size":   "Tamaño de cohorte",
        "vaccine_platform": "Plataforma vacunal",
        "run_analysis":  "▶ Ejecutar Análisis",
        "clear":         "🗑 Limpiar",
        "mrna":          "ARNm",
        "adenoviral":    "Vector Adenoviral",
        "protein_subunit": "Subunidad Proteica",
        "synth_banner":  "⚠️ DATOS 100% SINTÉTICOS — Simulación educativa únicamente · No se usan datos reales de pacientes · No tomar decisiones clínicas con estos resultados",
        "synth_mini":    "⚠️ DATOS 100% SINTÉTICOS — Solo investigación educativa. No usar para decisiones clínicas.",
        "demo_btn":      "⚡ Demo Rápido — 8 Casos Clínicos",
        "config_info":   "Configura los parámetros y presiona **▶ Ejecutar Análisis**.",
        "cohort_summary":"Resumen de la Cohorte",
        "patients_kpi":  "Pacientes",
        "avg_prob_kpi":  "P(Prot) Prom.",
        "seroconv_kpi":  "Seroconversión",
        "immunocomp_kpi":"Inmunocomp.",
        "low_risk_kpi":  "Riesgo Bajo",
        "high_crit_kpi": "Alto/Crítico",
        "patient_deepdive": "🔍 Análisis Profundo del Paciente",
        "cohort_table":  "Tabla Resumen de la Cohorte",
        "select_patient":"Seleccionar paciente:",
        "risk_low": "BAJO", "risk_moderate": "MODERADO",
        "risk_high": "ALTO", "risk_critical": "CRÍTICO",
        "risk_label": "Riesgo",
        "mod_tlr": "Inmunidad Innata", "mod_hla": "Inmunidad Adaptativa",
        "mod_stat": "Citocinas/STAT",  "mod_apoe": "Distribución Vacunal",
        "tab_immunogen": "🧬 Inmunogenicidad",
        "tab_platforms": "💉 Plataformas",
        "tab_rec":       "📋 Recomendación",
        "p_protection":  "P(Protección)",
        "solid_prot":    "Protección sólida",
        "mod_prot":      "Protección moderada",
        "low_prot":      "Protección baja",
        "council_header":"🎭 Consejo de Agentes IA",
        "council_subtitle": "6 especialistas debaten en tiempo real y dan una recomendación clínica.",
        "patient_source":"Fuente del paciente:",
        "demo_cases":    "Casos Demo Predefinidos",
        "cohort_cases":  "Pacientes de la Cohorte",
        "start_council": "▶ Iniciar Consejo",
        "select_demo":   "Seleccionar caso demo:",
        "select_cohort_patient": "Seleccionar paciente de la cohorte:",
        "official_verdict": "📋 Veredicto Oficial del Consejo",
        "followup_chat": "#### 💬 Consulta al Consejo",
        "followup_placeholder": "Pregunta al Consejo de Agentes...",
        "ai_live":       "IA en vivo",
        "conn_error":    "⚠️ Error de conexión",
        "waiting":       "esperando...",
        "generating":    "generando respuesta...",
        "gen_chat_header": "🔬 Consulta Genómica en Vivo",
        "gen_chat_subtitle": "Pregunta sobre genética, variantes y recomendaciones vacunales.",
        "gen_chat_placeholder": "Pregunta al genetista clínico...",
        "gen_chat_no_patient": "Selecciona un paciente en el Dashboard para dar contexto al genetista.",
        "custom_header": "🧬 Crear Perfil Genómico",
        "custom_subtitle": "Diseña un perfil sintético personalizado y analízalo con el motor completo + Consejo de IA.",
        "demo_data_label": "##### 👤 Datos Demográficos",
        "genetic_profile_label": "##### 🧬 Perfil Genómico",
        "name_label":    "Nombre (ficticio)",
        "age_label":     "Edad",
        "sex_label":     "Sexo biológico",
        "sex_female":    "Femenino",
        "sex_male":      "Masculino",
        "ancestry_label":"Ancestría",
        "anc_latino":    "Latino/Hispano",
        "anc_european":  "Europeo",
        "anc_african":   "Africano",
        "anc_asian":     "Asiático",
        "anc_other":     "Otra",
        "special_cond_label": "Condición especial",
        "target_platform_label": "Plataforma vacunal objetivo",
        "analyze_btn":   "🔬 Analizar Perfil Personalizado",
        "results_label": "#### 📊 Resultados del Análisis",
        "send_council_btn": "🎭 Enviar al Consejo de Agentes IA",
        "demo_loaded":   "{} casos demo cargados.",
        "patients_analyzed": "✅ {} pacientes analizados con éxito.",
        "loading_demo":  "Cargando casos demo...",
        "analyzing_cohort": "Analizando pacientes...",
        "analyzing_custom": "Analizando perfil personalizado con motor IRT 4PL...",
        "genetics_responding": "Genetista respondiendo...",
        "council_responding": "Respondiendo...",
        "no_llm": "Servicio LLM no disponible. Verifica GITHUB_TOKEN en .env.",
        "first_run_no_cohort": "Primero ejecuta el análisis de cohorte en el Dashboard.",
        "methodology_toggle": "📖 Ver metodología de datos sintéticos",
        "landing_title": "Tu ADN determina si una vacuna te protegerá. <em style='color:#63b3ed;'>VaccineGenics lo calcula.</em>",
        "landing_subtitle": "Motor farmacogenómico con Teoría de Respuesta al Item 4PL y debate multi-agente en Azure AI Foundry.",
        "synth_warn_title": "⚠️ TODOS LOS PERFILES DE PACIENTES SON 100% SINTÉTICOS",
        "synth_warn_body": "Generados computacionalmente para investigación y educación.<br>Ningún dato real de paciente es utilizado, almacenado ni procesado.<br><strong>No utilizar para decisiones clínicas.</strong>",
        "step1_title":   "1. Genotipado",
        "step1_desc":    "13+ variantes críticas (HLA, TLR4, APOE, STAT)",
        "step2_title":   "2. Validación RAG",
        "step2_desc":    "Referencias PubMed y ClinVar",
        "step3_title":   "3. Modelado IRT",
        "step3_desc":    "Curva 4PL de inmunogenicidad",
        "step4_title":   "4. Consejo IA",
        "step4_desc":    "6 agentes Azure AI Foundry debaten",
        "cond_none":     "Ninguna (sano/a)",
        "cond_radiation":"Exposición a radiación",
        "cond_cancer_active": "Cáncer (tratamiento activo)",
        "cond_cancer_remission": "Cáncer (remisión)",
        "cond_hiv_controlled": "VIH controlado",
        "cond_hiv_moderate":  "VIH moderado",
        "cond_hiv_severe":    "VIH severo",
        "cond_transplant":    "Trasplante órgano sólido",
        "cond_bmt_recent":    "TMO reciente (<2 años)",
        "cond_bmt_established":"TMO establecido (>2 años)",
        "cond_autoimmune_biologics": "Autoinmune - biológicos",
        "cond_autoimmune_steroids":  "Autoinmune - corticoides",
        "tlr4_normal":   "Normal (wildtype)",
        "tlr4_het":      "Heterocigoto",
        "tlr4_risk":     "Homocigoto de riesgo",
        "il6_normal":    "Normal (G/G)",
        "il6_het":       "Heterocigoto (G/C)",
        "il6_high":      "Alto burden (C/C)",
        "tmprss2_normal":"Normal (A/A)",
        "tmprss2_het":   "Heterocigoto",
        "tmprss2_var":   "Variante (G/G)",
        "hla_european":  "Estándar Europeo",
        "hla_highresp":  "Alto respondedor",
        "hla_vitt":      "Riesgo VITT (DRB1*11:04)",
        "hla_african":   "Ancestría Africana",
        "hla_latin":     "Ancestría Latinoamericana",
        "risk_alerts":   "#### ⚠️ Alertas Farmacogenómicas",
        "irt_xaxis":     "θ — Capacidad Inmunogénica",
        "irt_yaxis":     "P(Protección)",
        "seroconv_threshold": "60% — Seroconversión",
        "sex_m":         "Masculino",
        "sex_f":         "Femenino",
        "patient_label": "Paciente",
        "agent_live":    "EN VIVO",
        "legend_positive": "▲ impacto positivo · ▼ impacto negativo · ● neutro · Basado en el perfil genético del paciente",
        "avoid":         "⛔ EVITAR",
        "recommended":   "⭐ RECOMENDADA",
        "alternative":   "✔ Alternativa",
        "council_session": "Sesión del Consejo — {}",
        "analyze_council": "🎭 Analizar {} con Consejo de Agentes IA",
        "analyzing_genomics": "Analizando genómica de {}...",
        "error_engine":  "Error del motor: {}",
        "error_analysis":"Error al analizar: {}",
        "methodology_title": "Metodología de generación de pacientes sintéticos:",
        "risk_strat": "Estratificación de Riesgo",
        "dist_prot": "Distribución P(Protección)",
        "module_scores": "Puntuaciones de Módulos Genéticos",
        "score_label": "Puntuación (0-1)",
        "platform_compare": "Mismo ADN — 3 Plataformas Vacunales",
        "prot_threshold": "60% Umbral",
        "p_prot_label": "P(Protección)",
        "level_label": "Nivel",
        "patients_label": "Pacientes",
        "bajo": "Bajo", "moderado": "Mod", "alto": "Alto", "critico": "CRÍTICO",
        "copyright": "VaccineGenics · Precision Vaccine Intelligence · © 2026 Hilary Suárez",
        "geneticist_system": "Eres un genetista clínico experto en farmacogenómica y vacunas. Responde en español. Menciona que los datos son de simulación.",
        "geneticist_no_patient_ctx": "",
    },
    "en": {
        "tab_dashboard": "📊 Cohort Dashboard",
        "tab_council":   "🎭 AI Agent Council",
        "tab_custom":    "🧬 My Profile",
        "tab_consult":   "🔬 Genomic Consult",
        "tab_proteo":    "🧫 Proteomics",
        "lang_btn":      "🌐 Español",
        "cohort_size":   "Cohort size",
        "vaccine_platform": "Vaccine platform",
        "run_analysis":  "▶ Run Analysis",
        "clear":         "🗑 Clear",
        "mrna":          "mRNA",
        "adenoviral":    "Adenoviral Vector",
        "protein_subunit": "Protein Subunit",
        "synth_banner":  "⚠️ 100% SYNTHETIC DATA — Educational simulation only · No real patient data used, stored or processed · Not for clinical decisions",
        "synth_mini":    "⚠️ 100% SYNTHETIC DATA — Educational research only. Not for clinical decisions.",
        "demo_btn":      "⚡ Quick Demo — 8 Clinical Cases",
        "config_info":   "Configure parameters and press **▶ Run Analysis**.",
        "cohort_summary":"Cohort Summary",
        "patients_kpi":  "Patients",
        "avg_prob_kpi":  "Avg P(Prot.)",
        "seroconv_kpi":  "Seroconversion",
        "immunocomp_kpi":"Immunocomp.",
        "low_risk_kpi":  "Low Risk",
        "high_crit_kpi": "High/Critical",
        "patient_deepdive": "🔍 Patient Deep Dive",
        "cohort_table":  "Cohort Summary Table",
        "select_patient":"Select patient:",
        "risk_low": "LOW", "risk_moderate": "MODERATE",
        "risk_high": "HIGH", "risk_critical": "CRITICAL",
        "risk_label": "Risk",
        "mod_tlr": "Innate Immunity", "mod_hla": "Adaptive Immunity",
        "mod_stat": "Cytokines/STAT", "mod_apoe": "Vaccine Delivery",
        "tab_immunogen": "🧬 Immunogenicity",
        "tab_platforms": "💉 Platforms",
        "tab_rec":       "📋 Recommendation",
        "p_protection":  "P(Protection)",
        "solid_prot":    "Solid protection",
        "mod_prot":      "Moderate protection",
        "low_prot":      "Low protection",
        "council_header":"🎭 AI Agent Council",
        "council_subtitle": "6 specialists debate in real time and provide a clinical recommendation.",
        "patient_source":"Patient source:",
        "demo_cases":    "Pre-built Demo Cases",
        "cohort_cases":  "Cohort Patients",
        "start_council": "▶ Start Council",
        "select_demo":   "Select demo case:",
        "select_cohort_patient": "Select cohort patient:",
        "official_verdict": "📋 Official Council Verdict",
        "followup_chat": "#### 💬 Ask the Council",
        "followup_placeholder": "Ask the Agent Council...",
        "ai_live":       "AI Live",
        "conn_error":    "⚠️ Connection error",
        "waiting":       "waiting...",
        "generating":    "generating response...",
        "gen_chat_header": "🔬 Live Genomic Consult",
        "gen_chat_subtitle": "Ask about genetics, variants, and vaccine recommendations.",
        "gen_chat_placeholder": "Ask the clinical geneticist...",
        "gen_chat_no_patient": "Select a patient in the Dashboard to provide context to the geneticist.",
        "custom_header": "🧬 Create Genomic Profile",
        "custom_subtitle": "Design a custom synthetic profile and analyze it with the full engine + AI Council.",
        "demo_data_label": "##### 👤 Demographic Data",
        "genetic_profile_label": "##### 🧬 Genomic Profile",
        "name_label":    "Name (fictitious)",
        "age_label":     "Age",
        "sex_label":     "Biological sex",
        "sex_female":    "Female",
        "sex_male":      "Male",
        "ancestry_label":"Ancestry",
        "anc_latino":    "Latino/Hispanic",
        "anc_european":  "European",
        "anc_african":   "African",
        "anc_asian":     "Asian",
        "anc_other":     "Other",
        "special_cond_label": "Special condition",
        "target_platform_label": "Target vaccine platform",
        "analyze_btn":   "🔬 Analyze Custom Profile",
        "results_label": "#### 📊 Analysis Results",
        "send_council_btn": "🎭 Send to AI Agent Council",
        "demo_loaded":   "{} demo cases loaded.",
        "patients_analyzed": "✅ {} patients successfully analyzed.",
        "loading_demo":  "Loading demo cases...",
        "analyzing_cohort": "Analyzing patients...",
        "analyzing_custom": "Analyzing custom profile with IRT 4PL engine...",
        "genetics_responding": "Geneticist responding...",
        "council_responding": "Responding...",
        "no_llm": "LLM service unavailable. Check GITHUB_TOKEN in .env.",
        "first_run_no_cohort": "First run the cohort analysis in the Dashboard.",
        "methodology_toggle": "📖 View synthetic data methodology",
        "landing_title": "Your DNA determines whether a vaccine will protect you. <em style='color:#63b3ed;'>VaccineGenics calculates it.</em>",
        "landing_subtitle": "Pharmacogenomics engine with Item Response Theory 4PL and multi-agent Azure AI Foundry debate.",
        "synth_warn_title": "⚠️ ALL PATIENT PROFILES ARE 100% SYNTHETIC",
        "synth_warn_body": "Computationally generated for research and education.<br>No real patient data is used, stored, or processed.<br><strong>Not for clinical decisions.</strong>",
        "step1_title":   "1. Genotyping",
        "step1_desc":    "13+ critical variants (HLA, TLR4, APOE, STAT)",
        "step2_title":   "2. RAG Validation",
        "step2_desc":    "PubMed & ClinVar references",
        "step3_title":   "3. IRT Modeling",
        "step3_desc":    "4PL immunogenicity curve",
        "step4_title":   "4. AI Council",
        "step4_desc":    "6 Azure AI Foundry agents debate",
        "cond_none":     "None (healthy)",
        "cond_radiation":"Radiation exposure",
        "cond_cancer_active": "Active cancer (treatment)",
        "cond_cancer_remission": "Cancer (remission)",
        "cond_hiv_controlled": "HIV controlled",
        "cond_hiv_moderate":  "HIV moderate",
        "cond_hiv_severe":    "HIV severe",
        "cond_transplant":    "Solid organ transplant",
        "cond_bmt_recent":    "BMT recent (<2 years)",
        "cond_bmt_established":"BMT established (>2 years)",
        "cond_autoimmune_biologics": "Autoimmune - biologics",
        "cond_autoimmune_steroids":  "Autoimmune - steroids",
        "tlr4_normal":   "Normal (wildtype)",
        "tlr4_het":      "Heterozygous",
        "tlr4_risk":     "Homozygous risk",
        "il6_normal":    "Normal (G/G)",
        "il6_het":       "Heterozygous (G/C)",
        "il6_high":      "High burden (C/C)",
        "tmprss2_normal":"Normal (A/A)",
        "tmprss2_het":   "Heterozygous",
        "tmprss2_var":   "Variant (G/G)",
        "hla_european":  "Standard European",
        "hla_highresp":  "High responder",
        "hla_vitt":      "VITT risk (DRB1*11:04)",
        "hla_african":   "African ancestry",
        "hla_latin":     "Latin American ancestry",
        "risk_alerts":   "#### ⚠️ Pharmacogenomics Alerts",
        "irt_xaxis":     "θ — Immunogenic Capacity",
        "irt_yaxis":     "P(Protection)",
        "seroconv_threshold": "60% — Seroconversion",
        "sex_m":         "Male",
        "sex_f":         "Female",
        "patient_label": "Patient",
        "agent_live":    "LIVE",
        "legend_positive": "▲ positive impact · ▼ negative impact · ● neutral · Based on patient genetic profile",
        "avoid":         "⛔ AVOID",
        "recommended":   "⭐ RECOMMENDED",
        "alternative":   "✔ Alternative",
        "council_session": "Council Session — {}",
        "analyze_council": "🎭 Analyze {} with AI Agent Council",
        "analyzing_genomics": "Analyzing genomics of {}...",
        "error_engine":  "Engine error: {}",
        "error_analysis":"Error analyzing: {}",
        "methodology_title": "Synthetic patient generation methodology:",
        "risk_strat": "Risk Stratification",
        "dist_prot": "P(Protection) Distribution",
        "module_scores": "Genetic Module Scores",
        "score_label": "Score (0-1)",
        "platform_compare": "Same DNA — 3 Vaccine Platforms",
        "prot_threshold": "60% Threshold",
        "p_prot_label": "P(Protection)",
        "level_label": "Level",
        "patients_label": "Patients",
        "bajo": "Low", "moderado": "Mod", "alto": "High", "critico": "CRITICAL",
        "copyright": "VaccineGenics · Precision Vaccine Intelligence · © 2026 Hilary Suárez",
        "geneticist_system": "You are an expert clinical geneticist in pharmacogenomics and vaccines. Answer in English. Mention that data is from simulation.",
        "geneticist_no_patient_ctx": "",
    },
}

def _t(key: str, *args) -> str:
    lang = st.session_state.get("lang", "es")
    s = _TRANS.get(lang, _TRANS["es"]).get(key, _TRANS["es"].get(key, f"[{key}]"))
    return s.format(*args) if args else s

# ─── Condition labels (dynamic) ──────────────────────────────────────────────
_COND_KEY_MAP = {
    SpecialCondition.NONE.value:                "cond_none",
    SpecialCondition.RADIATION_EXPOSURE.value:  "cond_radiation",
    SpecialCondition.CANCER_ACTIVE.value:       "cond_cancer_active",
    SpecialCondition.CANCER_REMISSION.value:    "cond_cancer_remission",
    SpecialCondition.HIV_CONTROLLED.value:      "cond_hiv_controlled",
    SpecialCondition.HIV_MODERATE.value:        "cond_hiv_moderate",
    SpecialCondition.HIV_SEVERE.value:          "cond_hiv_severe",
    SpecialCondition.SOLID_ORGAN_TRANSPLANT.value: "cond_transplant",
    SpecialCondition.BMT_RECENT.value:          "cond_bmt_recent",
    SpecialCondition.BMT_ESTABLISHED.value:     "cond_bmt_established",
    SpecialCondition.AUTOIMMUNE_BIOLOGICS.value:"cond_autoimmune_biologics",
    SpecialCondition.AUTOIMMUNE_STEROIDS.value: "cond_autoimmune_steroids",
}

def _cond_label(cond_val: str) -> str:
    key = _COND_KEY_MAP.get(cond_val, "cond_none")
    return _t(key)

# Keep static dict for backward-compat lookups (Spanish stays as default fallback)
CONDITION_LABELS = {k: v for k, v in zip(
    _COND_KEY_MAP.keys(),
    ["Ninguna (sano/a)", "Exposicion a radiacion", "Cancer (tratamiento activo)",
     "Cancer (remision)", "VIH controlado", "VIH moderado", "VIH severo",
     "Trasplante organo solido", "TMO reciente (<2 anos)", "TMO establecido (>2 anos)",
     "Autoinmune - biologicos", "Autoinmune - corticoides"]
)}
_COND_VALUES = list(_COND_KEY_MAP.keys())

st.set_page_config(
    page_title="VaccineGenics — AI Pharmacogenomics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ───────────────────────────────────────────────────────────────────
_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');
* { font-family: 'Inter', system-ui, sans-serif !important; box-sizing: border-box; }
.material-symbols-rounded, span.material-symbols-rounded {
  font-family: 'Material Symbols Rounded' !important;
  font-style: normal !important; font-weight: normal !important;
  font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24 !important;
}
footer { display: none !important; }
#MainMenu { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
.viewerBadge_container__1QSob { display: none !important; }
.stApp, [data-testid="stAppViewContainer"], section[data-testid="stMain"] { background: #0a0f1a !important; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { max-width: 100% !important; padding: 1rem 2.5rem 2rem !important; }
.vg-banner { position:fixed; top:0; left:0; right:0; z-index:9999; background:rgba(15,10,0,0.98);
  border-bottom:2px solid rgba(236,201,75,0.55); color:#f6e05e; text-align:center;
  font-size:0.8rem; font-weight:700; padding:7px 16px; backdrop-filter:blur(12px);
  letter-spacing:0.03em; }
.synth-warning { background:rgba(236,201,75,0.08); border:1.5px solid rgba(236,201,75,0.4);
  border-radius:10px; padding:0.85rem 1.1rem; margin-bottom:1rem; }
.synth-mini { background:rgba(236,201,75,0.06); border:1px solid rgba(236,201,75,0.25);
  border-radius:8px; padding:0.45rem 0.9rem; margin-bottom:0.8rem;
  font-size:0.78rem; color:#d69e2e; font-weight:600; }
section.main > div:first-child { padding-top:3rem !important; }
::-webkit-scrollbar { width:5px; } ::-webkit-scrollbar-track { background:#0a0f1a; }
::-webkit-scrollbar-thumb { background:rgba(99,179,237,0.2); border-radius:3px; }
.live-badge { display:inline-flex; align-items:center; gap:5px; background:rgba(72,187,120,0.12);
  border:1px solid rgba(72,187,120,0.3); border-radius:20px; padding:3px 10px;
  font-size:0.72rem; font-weight:700; color:#48bb78; letter-spacing:0.03em; }
.live-badge::before { content:""; display:inline-block; width:7px; height:7px;
  background:#48bb78; border-radius:50%; animation:blink 1.4s ease-in-out infinite; }
.error-badge { display:inline-flex; align-items:center; gap:5px; background:rgba(245,101,101,0.1);
  border:1px solid rgba(245,101,101,0.3); border-radius:20px; padding:3px 10px;
  font-size:0.72rem; font-weight:600; color:#f56565; }
@keyframes blink { 0%,100%{opacity:0.5} 50%{opacity:1; box-shadow:0 0 6px #48bb78;} }
.main-title { font-size:2.8rem; font-weight:900; line-height:1.1;
  background:linear-gradient(135deg,#63b3ed,#4fd1c5,#68d391);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.vg-card { background:#151c2c; border:1px solid rgba(99,179,237,0.12); border-radius:12px;
  padding:1.2rem; margin-bottom:0.9rem; transition:border-color 0.2s ease; }
.vg-card:hover { border-color:rgba(99,179,237,0.28); }
.kpi-item { background:#151c2c; border:1px solid rgba(99,179,237,0.1); border-radius:10px;
  padding:1rem; text-align:center; border-top:3px solid #63b3ed; }
.kpi-value { font-size:1.9rem; font-weight:800; color:#fff; line-height:1.2; }
.kpi-label { font-size:0.75rem; color:#a0aec0; margin-top:0.3rem;
  text-transform:uppercase; letter-spacing:0.06em; }
.badge { display:inline-block; padding:3px 12px; border-radius:20px; font-size:0.73rem;
  font-weight:700; text-transform:uppercase; letter-spacing:0.05em; }
.badge-low      { background:rgba(72,187,120,0.15); color:#48bb78; }
.badge-moderate { background:rgba(237,137,54,0.15);  color:#ed8936; }
.badge-high     { background:rgba(245,101,101,0.15); color:#f56565; }
.badge-critical { background:rgba(229,62,62,0.2);   color:#fc8181;
  animation:pulse 2s infinite; }
.score-bar-bg { background:rgba(255,255,255,0.06); height:8px; border-radius:4px; overflow:hidden; }
.score-bar-fill { height:100%; border-radius:4px; }
.section-header { font-size:1.05rem; font-weight:700; color:#e2e8f0; margin-bottom:0.4rem;
  display:flex; align-items:center; gap:0.5rem; }
.section-line { height:2px; background:linear-gradient(90deg,#63b3ed,transparent); margin-bottom:0.9rem; }
.agent-bubble { background:#151c2c; border-radius:12px; padding:1rem 1.2rem;
  margin-bottom:0.8rem; border:1px solid rgba(255,255,255,0.06);
  animation: fadeIn 0.4s ease both; }
.agent-bubble-header { display:flex; align-items:center; justify-content:space-between;
  margin-bottom:0.6rem; padding-bottom:0.5rem; border-bottom:1px solid rgba(255,255,255,0.06); }
.agent-name { font-weight:700; font-size:0.92rem; }
.agent-role { font-size:0.72rem; color:#718096; }
@keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
@keyframes pulse { 0%,100%{opacity:0.8} 50%{opacity:1; box-shadow:0 0 12px rgba(229,62,62,0.3);} }
[data-testid="stTabs"] [role="tablist"] { gap:0.5rem; border-bottom:2px solid rgba(99,179,237,0.1) !important; }
[data-testid="stTabs"] button[role="tab"] { border-radius:8px 8px 0 0 !important; padding:0.5rem 1.4rem !important;
  font-weight:600 !important; font-size:0.88rem !important; color:#a0aec0 !important;
  background:transparent !important; border:none !important; transition:all 0.2s !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:#63b3ed !important;
  background:rgba(99,179,237,0.08) !important; border-bottom:3px solid #63b3ed !important; }
[data-testid="stSelectbox"] > div > div { background:#1a2332 !important;
  border:1px solid rgba(99,179,237,0.15) !important; border-radius:8px !important; color:#e2e8f0 !important; }
.stButton > button, [data-testid="baseButton-primary"] {
  background:linear-gradient(135deg,#2b6cb0,#63b3ed) !important; color:#fff !important;
  font-weight:700 !important; border:none !important; border-radius:8px !important;
  padding:0.5rem 1.4rem !important; font-size:0.85rem !important;
  text-transform:uppercase; letter-spacing:0.05em; transition:all 0.2s !important; }
.stButton > button:hover { transform:translateY(-1px) !important;
  box-shadow:0 4px 15px rgba(49,130,206,0.4) !important; }
.js-plotly-plot { border-radius:10px; overflow:hidden; }
[data-testid="stDataFrame"] { border-radius:8px; overflow:hidden; }
[data-testid="stChatInput"] { background:#1a2332 !important;
  border:1px solid rgba(99,179,237,0.2) !important; border-radius:10px !important; }
[data-testid="stChatMessage"] {
  background: #151c2c !important; border-radius: 12px !important;
  border: 1px solid rgba(99,179,237,0.08) !important;
  padding: 0.7rem 1rem !important; margin-bottom: 0.45rem !important; }
[data-testid="stChatMessage"][data-testid*="user"] {
  border-color: rgba(99,179,237,0.15) !important; }
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {
  background: transparent !important; }
/* Language badge */
.lang-badge { display:inline-flex; align-items:center; gap:4px; background:rgba(99,179,237,0.1);
  border:1px solid rgba(99,179,237,0.3); border-radius:6px; padding:3px 10px;
  font-size:0.78rem; font-weight:700; color:#63b3ed; cursor:pointer; }
</style>"""

_COUNCIL_COLORS = {
    "dr_genomico":       "#63b3ed",
    "dra_evidencia":     "#48bb78",
    "ing_riesgo":        "#ecc94b",
    "doc_clinico":       "#ed8936",
    "critico":           "#f56565",
    "doc_clinico_final": "#4fd1c5",
}

def _synth_mini():
    st.markdown(f'<div class="synth-mini">{_t("synth_mini")}</div>', unsafe_allow_html=True)


# ─── Custom profile presets (bilingual keys) ─────────────────────────────────
def _apoe_variants():
    return {
        "ε2/ε2": {"rs429358":{"genotype":"T/T","risk_allele":"C","gene":"APOE"},"rs7412":{"genotype":"T/T","risk_allele":"T","gene":"APOE"}},
        "ε2/ε3": {"rs429358":{"genotype":"T/T","risk_allele":"C","gene":"APOE"},"rs7412":{"genotype":"C/T","risk_allele":"T","gene":"APOE"}},
        "ε3/ε3": {"rs429358":{"genotype":"T/T","risk_allele":"C","gene":"APOE"},"rs7412":{"genotype":"C/C","risk_allele":"T","gene":"APOE"}},
        "ε3/ε4": {"rs429358":{"genotype":"C/T","risk_allele":"C","gene":"APOE"},"rs7412":{"genotype":"C/C","risk_allele":"T","gene":"APOE"}},
        "ε4/ε4": {"rs429358":{"genotype":"C/C","risk_allele":"C","gene":"APOE"},"rs7412":{"genotype":"T/T","risk_allele":"T","gene":"APOE"}},
        "ε2/ε4": {"rs429358":{"genotype":"C/T","risk_allele":"C","gene":"APOE"},"rs7412":{"genotype":"C/T","risk_allele":"T","gene":"APOE"}},
    }

def _tlr4_variants():
    return {
        _t("tlr4_normal"): {"rs4986790":{"genotype":"G/G","risk_allele":"A","gene":"TLR4"},"rs4986791":{"genotype":"C/C","risk_allele":"T","gene":"TLR4"}},
        _t("tlr4_het"):    {"rs4986790":{"genotype":"A/G","risk_allele":"A","gene":"TLR4"},"rs4986791":{"genotype":"C/T","risk_allele":"T","gene":"TLR4"}},
        _t("tlr4_risk"):   {"rs4986790":{"genotype":"A/A","risk_allele":"A","gene":"TLR4"},"rs4986791":{"genotype":"T/T","risk_allele":"T","gene":"TLR4"}},
    }

def _il6_variants():
    return {
        _t("il6_normal"): {"rs1800795":{"genotype":"G/G","risk_allele":"C","gene":"IL6"}},
        _t("il6_het"):    {"rs1800795":{"genotype":"G/C","risk_allele":"C","gene":"IL6"}},
        _t("il6_high"):   {"rs1800795":{"genotype":"C/C","risk_allele":"C","gene":"IL6"}},
    }

def _tmprss2_variants():
    return {
        _t("tmprss2_normal"): {"rs2070788":{"genotype":"A/A","risk_allele":"G","gene":"TMPRSS2"}},
        _t("tmprss2_het"):    {"rs2070788":{"genotype":"A/G","risk_allele":"G","gene":"TMPRSS2"}},
        _t("tmprss2_var"):    {"rs2070788":{"genotype":"G/G","risk_allele":"G","gene":"TMPRSS2"}},
    }

def _hla_presets():
    return {
        _t("hla_european"): {"class_I":{"HLA-A":["HLA-A*02:01"],"HLA-B":["HLA-B*07:02"]},"class_II":{"HLA-DRB1":["HLA-DRB1*15:01"],"HLA-DQB1":["HLA-DQB1*06:02"]}},
        _t("hla_highresp"): {"class_I":{"HLA-A":["HLA-A*02:01"],"HLA-B":["HLA-B*35:01"]},"class_II":{"HLA-DRB1":["HLA-DRB1*01:01"],"HLA-DQB1":["HLA-DQB1*05:01"]}},
        _t("hla_vitt"):     {"class_I":{"HLA-A":["HLA-A*03:01"],"HLA-B":["HLA-B*40:01"]},"class_II":{"HLA-DRB1":["HLA-DRB1*11:04"],"HLA-DQB1":["HLA-DQB1*03:01"]}},
        _t("hla_african"):  {"class_I":{"HLA-A":["HLA-A*23:01"],"HLA-B":["HLA-B*53:01"]},"class_II":{"HLA-DRB1":["HLA-DRB1*13:01"],"HLA-DQB1":["HLA-DQB1*06:03"]}},
        _t("hla_latin"):    {"class_I":{"HLA-A":["HLA-A*24:02"],"HLA-B":["HLA-B*35:01"]},"class_II":{"HLA-DRB1":["HLA-DRB1*04:01"],"HLA-DQB1":["HLA-DQB1*03:01"]}},
    }


def risk_color(level):
    return {"LOW":"#48bb78","MODERATE":"#ed8936","HIGH":"#f56565","CRITICAL":"#e53e3e"}.get(level,"#a0aec0")

def risk_badge(level):
    cls  = {"LOW":"badge-low","MODERATE":"badge-moderate","HIGH":"badge-high","CRITICAL":"badge-critical"}.get(level,"badge-low")
    lbl  = {"LOW":_t("risk_low"),"MODERATE":_t("risk_moderate"),"HIGH":_t("risk_high"),"CRITICAL":_t("risk_critical")}.get(level, level)
    return f'<span class="badge {cls}">{_t("risk_label")} {lbl}</span>'


@st.cache_data(show_spinner=False)
def _load_cohort(n):
    return [p.to_dict() for p in get_or_generate_cohort(n)]

def _clear_session():
    for k in ["reports","cohort_dicts","council_messages","council_report",
              "council_patient","council_platform","council_chat_history"]:
        st.session_state[k] = {} if k == "reports" else []
    if hasattr(_load_cohort, "clear"):
        _load_cohort.clear()

def _style_fig(fig, height=340):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter,system-ui,sans-serif", color="#e2e8f0", size=12),
        margin=dict(l=50, r=30, t=50, b=45), height=height,
    )
    fig.update_xaxes(gridcolor="rgba(99,179,237,0.06)", tickfont=dict(size=11))
    fig.update_yaxes(gridcolor="rgba(99,179,237,0.06)", tickfont=dict(size=11))


# ─── Charts ────────────────────────────────────────────────────────────────

def plot_irt_curve(platform, theta_highlight=None, height=360):
    params = VACCINE_IRT_PARAMS[platform]
    a, b, c = params["a"], params["b"], params["c"]
    thetas = np.linspace(-2.5, 1.5, 400)
    probs  = [irt_4pl(float(t), a, b, c) for t in thetas]
    hi = [irt_4pl(float(t)+0.1, a, b, c) for t in thetas]
    lo = [irt_4pl(float(t)-0.1, a, b, c) for t in thetas]
    _lbl = {"mRNA": _t("mrna"), "adenoviral_vector": _t("adenoviral"), "protein_subunit": _t("protein_subunit")}
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(thetas)+list(thetas[::-1]), y=hi+lo[::-1],
        fill="toself", fillcolor="rgba(99,179,237,0.08)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=list(thetas), y=probs, mode="lines", name=_t("p_protection"),
        line=dict(color="#63b3ed", width=2.5)))
    fig.add_hline(y=0.60, line_dash="dash", line_color="#48bb78", line_width=1.5,
        annotation_text=_t("seroconv_threshold"), annotation_font_size=11,
        annotation_position="bottom right")
    if theta_highlight is not None:
        ph = irt_4pl(float(theta_highlight), a, b, c)
        pc = "#48bb78" if ph >= 0.75 else ("#ed8936" if ph >= 0.55 else "#f56565")
        fig.add_vline(x=theta_highlight, line_color=pc, line_dash="dash", line_width=1.5)
        fig.add_trace(go.Scatter(x=[theta_highlight], y=[ph], mode="markers+text",
            name=_t("patient_label"), text=[f" {ph:.0%}"], textposition="top right",
            textfont=dict(color=pc, size=12),
            marker=dict(color=pc, size=14, symbol="diamond", line=dict(color="#fff", width=2))))
    fig.update_layout(
        title=dict(text=f"<b>IRT 4PL</b> — {_lbl.get(platform, platform)}", font=dict(size=13)),
        xaxis_title=_t("irt_xaxis"),
        yaxis=dict(range=[0,1.05], tickformat=".0%", title=_t("irt_yaxis")),
        showlegend=True, legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
    )
    _style_fig(fig, height=height)
    return fig

def plot_cross_platform(cross_platform_data):
    rows = sorted(cross_platform_data, key=lambda x: x.get("rank", 99))
    labels, probs, colors_list = [], [], []
    for row in rows:
        prob   = row.get("probability_protection", 0)
        contra = row.get("contraindicated", False)
        label  = row.get("label", row.get("platform","")).split("(")[0].strip()
        rank   = row.get("rank", 99)
        labels.append(label + (" ✗" if contra else (" ★" if rank == 1 else "")))
        probs.append(prob)
        colors_list.append("#e53e3e" if contra else ("#48bb78" if rank==1 else "#63b3ed"))
    fig = go.Figure(go.Bar(
        x=labels, y=probs, marker_color=colors_list,
        text=[f"{p:.0%}" for p in probs], textposition="outside",
        textfont=dict(size=12),
    ))
    fig.add_hline(y=0.60, line_dash="dash", line_color="#48bb78", line_width=2,
        annotation_text=_t("prot_threshold"), annotation_font_size=11,
        annotation_position="bottom right")
    fig.update_layout(
        title=_t("platform_compare"),
        yaxis=dict(range=[0,1.2], tickformat=".0%", title=_t("p_prot_label")),
        xaxis=dict(tickfont=dict(size=11)), showlegend=False,
    )
    _style_fig(fig, height=360)
    return fig

def plot_risk_distribution(reports):
    counts = {l: sum(1 for r in reports if r["overall_risk_level"]==l)
              for l in ["LOW","MODERATE","HIGH","CRITICAL"]}
    labels_loc = [_t("bajo"), _t("moderado"), _t("alto"), _t("critico")]
    colors     = ["#48bb78","#ed8936","#f56565","#e53e3e"]
    vals       = [counts["LOW"],counts["MODERATE"],counts["HIGH"],counts["CRITICAL"]]
    fig = go.Figure(go.Bar(
        x=labels_loc, y=vals, marker_color=colors,
        text=vals, textposition="auto", textfont=dict(size=12),
    ))
    fig.update_layout(title=_t("risk_strat"),
        xaxis_title=_t("level_label"), yaxis_title=_t("patients_label"))
    _style_fig(fig, height=300)
    return fig

def plot_protection_histogram(reports):
    probs = [r["irt"]["probability_protection"] for r in reports]
    fig = px.histogram(x=probs, nbins=30, title=_t("dist_prot"),
        labels={"x":_t("p_prot_label"),"count":_t("patients_label")},
        color_discrete_sequence=["#63b3ed"])
    fig.add_vline(x=0.60, line_dash="dash", line_color="#48bb78",
        annotation_text=_t("prot_threshold"), annotation_font_size=11)
    fig.update_layout(yaxis_title=_t("patients_label"))
    _style_fig(fig, height=300)
    return fig

def plot_module_scores(reports):
    scores = {"TLR":[],"HLA":[],"STAT":[],"APOE":[]}
    for r in reports:
        ms = r.get("module_scores",{})
        scores["TLR"].append(ms.get("tlr",{}).get("score",0))
        scores["HLA"].append(ms.get("hla",{}).get("score",0))
        scores["STAT"].append(ms.get("stat",{}).get("score",0))
        scores["APOE"].append(ms.get("apoe_peg3",{}).get("score",0))
    fig = go.Figure()
    palette = ["#63b3ed","#4fd1c5","#68d391","#f6e05e"]
    for i,(mod,vals) in enumerate(scores.items()):
        fig.add_trace(go.Box(y=vals, name=mod, boxpoints="outliers", marker_color=palette[i]))
    fig.update_layout(title=_t("module_scores"), yaxis_title=_t("score_label"))
    _style_fig(fig, height=320)
    return fig


# ─── Agent message renderer ─────────────────────────────────────────────────

def _render_agent_message(msg: dict):
    slug   = msg["agent"]
    color  = _COUNCIL_COLORS.get(slug, "#63b3ed")
    source = msg.get("source","llm")
    engine = msg.get("engine", "github_gpt4o_mini")

    if source != "llm":
        src_html = f'<span class="error-badge">{_t("conn_error")}</span>'
    elif engine == "foundry_o4mini":
        src_html = (
            f'<span class="live-badge">{_t("ai_live")}</span>'
            f'<span style="background:rgba(99,179,237,0.18);border:1px solid rgba(99,179,237,0.55);'
            f'border-radius:999px;padding:2px 9px;font-size:0.7rem;font-weight:700;'
            f'color:#63b3ed;margin-left:5px;white-space:nowrap;">⚡ Azure Foundry o4-mini</span>'
        )
    else:
        src_html = f'<span class="live-badge">{_t("ai_live")}</span>'

    extras = ""
    if msg.get("code_block"):
        code_escaped = _html.escape(msg["code_block"]).replace('#', '&#35;')
        output_block = ""
        if msg.get("code_output"):
            output_escaped = _html.escape(msg["code_output"])
            output_block = (
                f'<pre style="background:#0d1117;color:#79c0ff;padding:0.6rem 0.8rem;'
                f'border-radius:6px;font-size:0.78rem;overflow-x:auto;margin-top:0.4rem;">'
                f'{output_escaped}</pre>'
            )
        extras += (
            f'<details style="margin-top:0.6rem;">'
            f'<summary style="cursor:pointer;color:#63b3ed;font-size:0.85rem;'
            f'font-weight:600;list-style:none;padding:0.3rem 0;">🔢 Ver código IRT 4PL</summary>'
            f'<pre style="background:#0d1117;color:#e2e8f0;padding:0.8rem;border-radius:8px;'
            f'font-size:0.78rem;overflow-x:auto;margin-top:0.4rem;">{code_escaped}</pre>'
            f'{output_block}'
            f'</details>'
        )

    if msg.get("citations"):
        cit_items = ""
        for c in msg["citations"]:
            pmid  = _html.escape(str(c.get("pmid","")))
            auth  = _html.escape(str(c.get("authors","")))
            yr    = _html.escape(str(c.get("year","")))
            jour  = _html.escape(str(c.get("journal","")))
            relev = _html.escape(str(c.get("relevance","")))
            cit_items += (
                f'<div style="margin-bottom:0.6rem;">'
                f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank" '
                f'style="color:#63b3ed;font-weight:700;">PMID {pmid}</a>'
                f' — {auth} ({yr}, <em>{jour}</em>)'
                f'<div style="color:#718096;font-size:0.82rem;margin-top:0.15rem;">{relev}</div>'
                f'</div>'
            )
        n = len(msg["citations"])
        extras += (
            f'<details style="margin-top:0.5rem;">'
            f'<summary style="cursor:pointer;color:#63b3ed;font-size:0.85rem;'
            f'font-weight:600;list-style:none;padding:0.3rem 0;">📚 {n} referencias bibliográficas</summary>'
            f'<div style="margin-top:0.6rem;">{cit_items}</div>'
            f'</details>'
        )

    st.markdown(f"""
<div class="agent-bubble" style="border-left:4px solid {color};">
  <div class="agent-bubble-header">
    <div>
      <span style="font-size:1.2rem;">{msg['avatar']}</span>
      <span class="agent-name" style="color:{color}; margin-left:6px;">{msg['name']}</span>
      <span class="agent-role"> — {msg['role']}</span>
    </div>
    {src_html}
  </div>
</div>""", unsafe_allow_html=True)
    st.markdown(msg["content"])
    if extras:
        st.markdown(extras, unsafe_allow_html=True)


# ─── Patient Deep Dive (fragment) ────────────────────────────────────────────

@st.fragment
def _render_patient_deep_dive(platform: str):
    reports_dict = st.session_state.get("reports", {})
    if not reports_dict:
        return
    reports      = list(reports_dict.values())
    patient_ids  = [r["patient_id"] for r in reports]
    critical_ids = [r["patient_id"] for r in reports if r.get("overall_risk_level") == "CRITICAL"]
    default_idx  = patient_ids.index(critical_ids[0]) if critical_ids else 0
    cohort_dicts = st.session_state.cohort_dicts

    selected_id = st.selectbox(
        _t("select_patient"),
        patient_ids,
        index=default_idx,
        format_func=lambda pid: (
            f"{'🚨 ' if st.session_state.reports.get(pid,{}).get('overall_risk_level')=='CRITICAL' else ''}"
            f"{pid} — {st.session_state.reports.get(pid,{}).get('overall_risk_level','?')}"
            f" · P={st.session_state.reports.get(pid,{}).get('irt',{}).get('probability_protection',0):.0%}"
        ),
        key="patient_select_main",
    )

    patient_dict = next((p for p in cohort_dicts if p["patient_id"] == selected_id), None)
    report = st.session_state.reports.get(selected_id)
    if patient_dict and report:
        st.session_state.current_analysis_report = report
        _render_patient_analysis(patient_dict, report, platform)

        st.markdown("<br>", unsafe_allow_html=True)
        run_dash_council = st.button(
            _t("analyze_council", selected_id),
            type="primary", use_container_width=True, key="btn_dash_council",
        )

        if run_dash_council:
            st.session_state["dash_council_pid"]      = selected_id
            st.session_state["dash_council_messages"] = []
            st.session_state["dash_council_patient"]  = patient_dict
            st.session_state["dash_council_report"]   = report
            st.markdown(f"""<div style="display:flex; align-items:center; gap:1rem; margin:0.8rem 0;">
  <div style="font-size:1.1rem; font-weight:700; color:#e2e8f0;">{_t("council_session", selected_id)}</div>
  <span class="live-badge">{_t("ai_live")}</span>
</div>""", unsafe_allow_html=True)
            il6_d = report.get("module_scores", {}).get("stat", {}).get("il6_burden", 0.0) or 0.0
            cit_d = get_citations(
                apoe_genotype=patient_dict.get("apoe_genotype", ""),
                variants=patient_dict.get("variants", {}),
                hla_haplotype=patient_dict.get("hla_haplotype", []),
                condition=patient_dict.get("special_condition", "none"),
                il6_burden=il6_d,
            )
            _ao = ["dr_genomico","dra_evidencia","ing_riesgo","doc_clinico","critico","doc_clinico_final"]
            _sl = {s: st.empty() for s in _ao}
            for s in _ao:
                p2 = COUNCIL_PERSONAS[s]
                with _sl[s].container():
                    st.markdown(f'<div class="agent-bubble" style="border-left:4px solid {_COUNCIL_COLORS[s]}; opacity:0.4;"><span style="color:{_COUNCIL_COLORS[s]};">{p2.avatar} {p2.name}</span> <span style="color:#718096; font-size:0.8rem;">{_t("waiting")}</span></div>', unsafe_allow_html=True)
            _n2s = {p2.name: s for s, p2 in COUNCIL_PERSONAS.items()}
            def _op2(an):
                s = _n2s.get(an)
                if s and s in _sl:
                    p2 = COUNCIL_PERSONAS[s]
                    with _sl[s].container():
                        st.markdown(f'<div class="agent-bubble" style="border-left:4px solid {_COUNCIL_COLORS[s]};"><span class="live-badge" style="margin-right:8px;">{_t("agent_live")}</span><span style="color:{_COUNCIL_COLORS[s]};">{p2.avatar} {p2.name}</span></div>', unsafe_allow_html=True)
            def _om2(msg):
                with _sl[msg.agent].container():
                    _render_agent_message(msg.to_dict())
            msgs_d = AgentCouncil().stream_session(
                patient=patient_dict, report=report, platform=platform,
                citations=cit_d, progress_callback=_op2, on_message=_om2,
            )
            st.session_state["dash_council_messages"] = [m.to_dict() for m in msgs_d]

        elif (st.session_state.get("dash_council_messages") and
              st.session_state.get("dash_council_pid") == selected_id):
            st.markdown(f'<div style="font-size:1.05rem; font-weight:700; color:#e2e8f0; margin:0.8rem 0;">{_t("council_session", selected_id)}</div>', unsafe_allow_html=True)
            for msg in st.session_state["dash_council_messages"]:
                _render_agent_message(msg)


# ─── Council Tab ─────────────────────────────────────────────────────────────

def _render_council_tab(platform):
    st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; padding:0.5rem 0 1rem 0;">
  <div>
    <div style="font-size:1.6rem; font-weight:800; color:#e2e8f0;">{_t("council_header")}</div>
    <div style="color:#a0aec0; font-size:0.9rem;">{_t("council_subtitle")}</div>
  </div>
  <div>
    <div style="display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end;">
      <span class="live-badge">Agents 1–5 · GitHub Models gpt-4o-mini</span>
      <span style="background:rgba(99,179,237,0.15);border:1px solid rgba(99,179,237,0.5);
        border-radius:999px;padding:2px 10px;font-size:0.72rem;font-weight:700;
        color:#63b3ed;white-space:nowrap;">⚡ Agent 6 · Azure Foundry o4-mini</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
    _synth_mini()

    source = st.radio(_t("patient_source"), [_t("demo_cases"), _t("cohort_cases")],
                      horizontal=True, key="council_source")

    if _t("cohort_cases") in source:
        cohort = st.session_state.get("cohort_dicts", [])
        if not cohort:
            st.warning(_t("first_run_no_cohort"))
            return
        patient_ids = [p["patient_id"] for p in cohort]
        col_sel, col_run = st.columns([3,1])
        with col_sel:
            sel_idx = st.selectbox(_t("select_cohort_patient"),
                range(len(patient_ids)),
                format_func=lambda i: f"{patient_ids[i]}  —  {cohort[i].get('age','?')} · APOE {cohort[i].get('apoe_genotype','?')}",
                key="council_cohort_idx")
        with col_run:
            st.markdown("<br>", unsafe_allow_html=True)
            start = st.button(_t("start_council"), type="primary", use_container_width=True, key="btn_council_cohort")
        patient_dict = cohort[sel_idx]
        target_vaccine = platform
    else:
        labels = persona_short_labels()
        col_sel, col_run = st.columns([3,1])
        with col_sel:
            p_idx = st.selectbox(_t("select_demo"),
                range(len(DEMO_PERSONAS)),
                format_func=lambda i: labels[i],
                key="council_demo_idx")
        with col_run:
            st.markdown("<br>", unsafe_allow_html=True)
            start = st.button(_t("start_council"), type="primary", use_container_width=True, key="btn_council_demo")
        persona = DEMO_PERSONAS[p_idx]
        patient_dict = {k: persona[k] for k in
            ["patient_id","name","age","sex","ethnicity","variants","hla_haplotype","apoe_genotype","special_condition"]}
        target_vaccine = persona.get("target_vaccine", platform)
        st.markdown(f"""
<div class="vg-card" style="border-left:4px solid #63b3ed; margin-top:0.5rem;">
  <b style="color:#63b3ed;">{persona['name']}</b> &nbsp;·&nbsp;
  {persona['age']} · {persona['sex']}
  <br><span style="color:#a0aec0; font-size:0.88rem;">{persona['backstory']}</span>
  <br><em style="color:#718096; font-size:0.82rem;">💡 {persona['why_interesting']}</em>
</div>""", unsafe_allow_html=True)

    if start:
        st.session_state.council_messages = []
        st.session_state.council_chat_history = []
        pid = patient_dict.get("patient_id", "?")

        with st.spinner(_t("analyzing_genomics", pid)):
            try:
                cond_val = patient_dict.get("special_condition", SpecialCondition.NONE.value)
                try: cond = SpecialCondition(cond_val)
                except: cond = SpecialCondition.NONE
                rep_obj = analyze_patient(
                    patient_id=pid, age=patient_dict["age"], sex=patient_dict["sex"],
                    variants=patient_dict["variants"], hla_haplotype=patient_dict["hla_haplotype"],
                    apoe_genotype=patient_dict["apoe_genotype"], target_vaccine=target_vaccine,
                    special_condition=cond, run_cross_platform=True,
                )
                report = rep_obj.to_dict()
            except Exception as exc:
                st.error(_t("error_engine", exc))
                return

        il6 = report.get("module_scores",{}).get("stat",{}).get("il6_burden", 0.0) or 0.0
        citations = get_citations(
            apoe_genotype=patient_dict.get("apoe_genotype",""),
            variants=patient_dict.get("variants",{}),
            hla_haplotype=patient_dict.get("hla_haplotype",[]),
            condition=patient_dict.get("special_condition","none"),
            il6_burden=il6,
        )

        st.markdown("---")
        st.markdown(f"""
<div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
  <div style="font-size:1.1rem; font-weight:700; color:#e2e8f0;">{_t("council_session", pid)}</div>
  <span class="live-badge">{_t("ai_live")} · GPT-4o-mini</span>
</div>""", unsafe_allow_html=True)

        agent_order = ["dr_genomico","dra_evidencia","ing_riesgo","doc_clinico","critico","doc_clinico_final"]
        slots = {slug: st.empty() for slug in agent_order}

        for slug in agent_order:
            p = COUNCIL_PERSONAS[slug]
            with slots[slug].container():
                st.markdown(
                    f'<div class="agent-bubble" style="border-left:4px solid {_COUNCIL_COLORS[slug]}; opacity:0.4;">'
                    f'<span style="color:{_COUNCIL_COLORS[slug]};">{p.avatar} {p.name}</span>'
                    f' <span style="color:#718096; font-size:0.8rem;">{_t("waiting")}</span></div>',
                    unsafe_allow_html=True)

        _name_to_slug = {p.name: slug for slug, p in COUNCIL_PERSONAS.items()}

        def _on_progress(agent_name):
            slug = _name_to_slug.get(agent_name)
            if slug and slug in slots:
                p = COUNCIL_PERSONAS[slug]
                with slots[slug].container():
                    st.markdown(
                        f'<div class="agent-bubble" style="border-left:4px solid {_COUNCIL_COLORS[slug]};">'
                        f'<span class="live-badge" style="margin-right:8px;">{_t("agent_live")}</span>'
                        f'<span style="color:{_COUNCIL_COLORS[slug]};">{p.avatar} {p.name}</span>'
                        f' <span style="color:#a0aec0; font-size:0.8rem;">{_t("generating")}</span></div>',
                        unsafe_allow_html=True)

        def _on_message(msg):
            msg_dict = msg.to_dict()
            with slots[msg.agent].container():
                _render_agent_message(msg_dict)

        council = AgentCouncil()
        messages = council.stream_session(
            patient=patient_dict, report=report, platform=target_vaccine,
            citations=citations, progress_callback=_on_progress, on_message=_on_message,
        )

        st.session_state.council_messages  = [m.to_dict() for m in messages]
        st.session_state.council_report    = report
        st.session_state.council_patient   = patient_dict
        st.session_state.council_platform  = target_vaccine

    elif st.session_state.get("council_messages"):
        report       = st.session_state.get("council_report", {})
        patient_dict = st.session_state.get("council_patient", {})
        sel_platform = st.session_state.get("council_platform", "mRNA")

        st.markdown("---")
        n_live = sum(1 for m in st.session_state.council_messages if m.get("source") == "llm")
        st.markdown(f"""
<div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
  <div style="font-size:1.1rem; font-weight:700; color:#e2e8f0;">
    {_t("council_session", patient_dict.get('patient_id', patient_dict.get('name','?')))}
  </div>
  <span class="{'live-badge' if n_live == 6 else ('error-badge' if n_live == 0 else 'live-badge')}">
    {'✅ ' + str(n_live) + '/6' if n_live > 0 else '❌ Error — GITHUB_TOKEN'}
  </span>
</div>""", unsafe_allow_html=True)

        for msg in st.session_state.council_messages:
            _render_agent_message(msg)

        final_msgs = [m for m in st.session_state.council_messages if m["agent"] == "doc_clinico_final"]
        if final_msgs:
            st.markdown("---")
            prob  = report.get("irt",{}).get("probability_protection", 0)
            risk  = report.get("overall_risk_level","?")
            rc    = risk_color(risk)
            st.markdown(f"""
<div class="vg-card" style="border:2px solid {rc}; box-shadow:0 0 20px {rc}18;">
  <div style="display:flex; justify-content:space-between; margin-bottom:0.8rem; padding-bottom:0.6rem;
              border-bottom:1px solid rgba(255,255,255,0.07);">
    <strong style="font-size:1.1rem; color:{rc};">{_t("official_verdict")}</strong>
    {risk_badge(risk)}
  </div>
  <div style="color:#e2e8f0; line-height:1.8; white-space:pre-line;">{report.get("final_recommendation","")}</div>
  <div style="margin-top:0.8rem; padding-top:0.6rem; border-top:1px solid rgba(255,255,255,0.07);
              font-size:0.85rem; color:#a0aec0;">
    {_t("platform_compare").split("—")[0].strip()}: <strong style="color:#63b3ed;">{sel_platform}</strong>
    &nbsp;|&nbsp; {_t("p_protection")}: <strong style="color:{rc}; font-size:1rem;">{prob:.0%}</strong>
    &nbsp;|&nbsp; <span class="live-badge">{n_live}/6 {_t("ai_live")}</span>
    &nbsp;|&nbsp; <span style="color:#63b3ed;font-size:0.8rem;">⚡ Agent 6: Azure Foundry o4-mini</span>
  </div>
</div>""", unsafe_allow_html=True)
            # 🧠 Reasoning trace — always visible after verdict
            _trace_label = "🧠 Árbol de Razonamiento — Trazabilidad de Agentes" if st.session_state.get("lang","es") == "es" else "🧠 Reasoning Tree — Agent Traceability"
            with st.expander(_trace_label, expanded=False):
                render_reasoning_trace({
                    "steps": st.session_state.council_messages,
                    "patient": patient_dict.get("patient_id", patient_dict.get("name","?")),
                    "platform": sel_platform,
                })

    else:
        st.markdown(f'<div style="text-align:center; padding:1.5rem 0 1rem; color:#718096;">{_t("select_demo").replace(":", "")} → <b>{_t("start_council")}</b></div>', unsafe_allow_html=True)
        cols = st.columns(6)
        for col, slug in zip(cols, ["dr_genomico","dra_evidencia","ing_riesgo","doc_clinico","critico","doc_clinico_final"]):
            p = COUNCIL_PERSONAS[slug]
            col.markdown(f"""
<div class="vg-card" style="text-align:center; min-height:110px;">
  <div style="font-size:1.8rem;">{p.avatar}</div>
  <div style="font-weight:700; color:{p.color}; font-size:0.82rem; margin-top:4px;">{p.name}</div>
  <div style="color:#718096; font-size:0.72rem;">{p.role}</div>
</div>""", unsafe_allow_html=True)

    if st.session_state.get("council_messages"):
        st.markdown("---")
        st.markdown(_t("followup_chat"))
        if "council_chat_history" not in st.session_state:
            st.session_state.council_chat_history = []
        _AV2 = {"user": "🙋", "assistant": "🎭"}
        for cm in st.session_state.council_chat_history:
            with st.chat_message(cm["role"], avatar=_AV2.get(cm["role"],"💬")):
                st.markdown(cm["content"])
        fu = st.chat_input(_t("followup_placeholder"), key="council_followup")
        if fu:
            _p = st.session_state.get("council_patient",{})
            _r = st.session_state.get("council_report",{})
            ctx = (f"Patient: {_p.get('patient_id',_p.get('name','?'))}, "
                   f"age {_p.get('age')}, APOE: {_p.get('apoe_genotype')}, "
                   f"P(prot)={_r.get('irt',{}).get('probability_protection',0):.1%}, "
                   f"Risk={_r.get('overall_risk_level','?')}")
            prev = " | ".join(m["content"][:100] for m in st.session_state.council_messages[-2:])
            prompt = f"Context: {ctx}\nSummary: {prev}\n\nQuestion: {fu}"
            with st.chat_message("user", avatar="🙋"):
                st.markdown(fu)
            with st.chat_message("assistant", avatar="🎭"):
                with st.spinner(_t("council_responding")):
                    try:
                        _c = AgentCouncil()
                        resp = _c._llm_call(
                            COUNCIL_PERSONAS["doc_clinico"].system_prompt,
                            prompt, max_tokens=500, slug="doc_clinico")
                        if not resp:
                            resp = _t("no_llm")
                    except Exception as exc:
                        resp = f"Error: {exc}"
                st.markdown(resp)
            st.session_state.council_chat_history.append({"role":"user","content":fu})
            st.session_state.council_chat_history.append({"role":"assistant","content":resp})


# ─── Patient deep-dive ───────────────────────────────────────────────────────

def _render_patient_analysis(patient_dict, report, platform):
    risk  = report.get("overall_risk_level","LOW")
    rc    = risk_color(risk)
    irt   = report.get("irt",{})
    prob  = irt.get("probability_protection",0)
    theta = irt.get("theta",0)
    ci    = irt.get("confidence_interval",[0,0])
    pc    = "#48bb78" if prob>=0.75 else ("#ed8936" if prob>=0.55 else "#f56565")
    pl    = _t("solid_prot") if prob>=0.75 else (_t("mod_prot") if prob>=0.55 else _t("low_prot"))
    pe    = "✅" if prob>=0.75 else ("⚠️" if prob>=0.55 else "❌")
    sex_raw = report.get("sex","")
    sex_es  = _t("sex_m") if sex_raw == "Male" else (_t("sex_f") if sex_raw == "Female" else sex_raw)
    cond     = report.get("special_condition","none")
    cond_lbl = _cond_label(cond)
    theta_gen = irt.get("theta_genetic", theta)
    theta_pen = irt.get("theta_penalty", 0)
    theta_line = (f"θ_gen={theta_gen:+.3f} + pen={theta_pen:+.2f} → θ={theta:+.3f}"
                  if theta_pen != 0 else f"θ = {theta:+.3f}")

    st.markdown(f"""
<div class="vg-card" style="border-left:5px solid {rc};">
  <div style="display:flex; align-items:center; gap:2rem; flex-wrap:wrap;">
    <div style="flex:1; min-width:220px;">
      <div style="font-size:1.25rem; font-weight:800; color:#fff;">🧬 {report.get('patient_id','?')}</div>
      <div style="color:#a0aec0; margin-top:4px;">{report.get('age','?')} · {sex_es} · APOE: {report.get('apoe_genotype','?')}
        {f'&nbsp;·&nbsp;<span class="badge badge-moderate">{cond_lbl}</span>' if cond!="none" else ""}
      </div>
      <div style="color:#718096; font-size:0.8rem; font-family:monospace; margin-top:5px;">{theta_line} · IC: {ci[0]:.0%}–{ci[1]:.0%}</div>
    </div>
    <div style="text-align:center; background:rgba(0,0,0,0.2); border-radius:10px; padding:0.7rem 1.3rem; border:1px solid {pc}40;">
      <div style="font-size:2.4rem; font-weight:800; color:{pc};">{prob:.0%}</div>
      <div style="font-size:0.72rem; color:#a0aec0;">{_t("p_protection")}</div>
      <div style="color:{pc}; font-weight:600; font-size:0.85rem;">{pe} {pl}</div>
    </div>
    <div style="text-align:center;">
      {risk_badge(risk)}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    tab_imm, tab_plat, tab_rec = st.tabs([_t("tab_immunogen"), _t("tab_platforms"), _t("tab_rec")])

    with tab_imm:
        ms = report.get("module_scores",{})
        MODS = [
            ("tlr",      _t("mod_tlr"),  "35%","TLR4/TLR7/TLR9"),
            ("hla",      _t("mod_hla"),  "40%","HLA alleles"),
            ("stat",     _t("mod_stat"), "20%","IL-6/STAT3"),
            ("apoe_peg3",_t("mod_apoe"), "5%", "APOE/LNP"),
        ]
        m_cols = st.columns(4)
        for col,(key,lbl,wt,genes) in zip(m_cols, MODS):
            score = ms.get(key,{}).get("score",0)
            delta = score - 0.65
            bc    = "#48bb78" if score>=0.70 else ("#ed8936" if score>=0.50 else "#f56565")
            col.markdown(f"""
<div class="vg-card" style="min-height:155px;">
  <div style="font-weight:700; color:#a0aec0; font-size:0.85rem;">{lbl}</div>
  <div style="font-size:0.7rem; color:#718096;">{wt} · {genes}</div>
  <div style="font-size:1.7rem; font-weight:800; color:#fff; margin:0.4rem 0;">{score:.3f}</div>
  <div class="score-bar-bg"><div class="score-bar-fill" style="background:{bc}; width:{score*100}%;"></div></div>
  <div style="font-size:0.72rem; color:{'#48bb78' if delta>=0 else '#f56565'}; margin-top:4px;">{'+' if delta>=0 else ''}{delta:+.3f} vs avg</div>
</div>""", unsafe_allow_html=True)

        if report.get("all_risk_flags"):
            st.markdown(_t("risk_alerts"))
            _CRIT_KW = ["CONTRAINDICACION","CONTRAINDICADO","CRITICAL","CYTOKINE STORM","CONTRAINDICATED"]
            for flag in report["all_risk_flags"]:
                is_c = any(kw in flag.upper() for kw in _CRIT_KW)
                (st.error if is_c else st.warning)(f"{'🚨' if is_c else '⚠️'} {flag}")

        immunocomp = report.get("immunocompromised")
        if immunocomp and immunocomp.get("condition","none") != "none":
            cn = _cond_label(immunocomp["condition"])
            interp = _html.escape(immunocomp.get("interpretation",""))
            dm = immunocomp.get("dose_multiplier", 1.0)
            dose_html = (f'<div style="background:rgba(99,179,237,0.1);border-radius:6px;'
                         f'padding:0.4rem 0.7rem;margin:0.4rem 0;color:#63b3ed;">'
                         f'💉 Dose: {dm}× standard</div>') if dm != 1.0 else ""
            mon_items = "".join(
                f'<div style="color:#a0aec0;font-size:0.85rem;">• {_html.escape(m)}</div>'
                for m in immunocomp.get("monitoring", [])
            )
            int_items = "".join(
                f'<div style="background:rgba(245,101,101,0.1);border-left:3px solid #f56565;'
                f'padding:0.3rem 0.6rem;margin:0.3rem 0;color:#feb2b2;font-size:0.85rem;">'
                f'{_html.escape(i)}</div>'
                for i in immunocomp.get("interactions", [])
            )
            st.markdown(f"""<details style="margin-top:0.5rem;">
<summary style="cursor:pointer;color:#63b3ed;font-size:0.88rem;font-weight:600;
list-style:none;padding:0.3rem 0;">🏥 {cn}</summary>
<div style="margin-top:0.5rem;padding:0.5rem 0;">
  <div style="font-weight:600;color:#e2e8f0;margin-bottom:0.4rem;">{interp}</div>
  {dose_html}{mon_items}{int_items}
</div></details>""", unsafe_allow_html=True)

    with tab_plat:
        cp = report.get("cross_platform")
        if cp:
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(plot_irt_curve(platform, theta_highlight=theta), use_container_width=True)
            with c2: st.plotly_chart(plot_cross_platform(cp), use_container_width=True)
            rows = [{"#": "⛔" if r.get("contraindicated") else f"#{r.get('rank','?')}",
                     "Platform": r.get("label",r.get("platform","")).split("(")[0].strip(),
                     _t("p_protection"): f"{r.get('probability_protection',0):.0%}",
                     "Status": (_t("avoid") if r.get("contraindicated") else
                                (_t("recommended") if r.get("rank")==1 else _t("alternative")))}
                    for r in sorted(cp, key=lambda x: x.get("rank",99))]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.plotly_chart(plot_irt_curve(platform, theta_highlight=theta), use_container_width=True)

    with tab_rec:
        narratives_es = {
            "CRITICAL": "Contraindicación detectada. Se requiere plataforma alternativa urgente.",
            "HIGH":     "Múltiples factores de riesgo. Considerar refuerzo de dosis o plataforma alternativa.",
            "MODERATE": "Perfil moderado. Protección parcial esperada. Monitorizar respuesta.",
            "LOW":      "Perfil favorable. Vacunación estándar con protección sólida esperada.",
        }
        narratives_en = {
            "CRITICAL": "Contraindication detected. Alternative platform required urgently.",
            "HIGH":     "Multiple risk factors. Consider dose booster or alternative platform.",
            "MODERATE": "Moderate profile. Partial protection expected. Monitor response.",
            "LOW":      "Favorable profile. Standard vaccination with solid protection expected.",
        }
        lang = st.session_state.get("lang","es")
        narr = (narratives_en if lang == "en" else narratives_es).get(risk,"")
        st.markdown(f'<div class="vg-card" style="border-left:4px solid {pc};"><em>🤖 {narr}</em></div>', unsafe_allow_html=True)
        st.success(f"**{report.get('final_recommendation','—')}**")
        st.caption("VaccineGenics — simulation only. Not for clinical use. / Solo simulación. No para uso clínico.")


# ─── Geneticist chat ─────────────────────────────────────────────────────────

def _render_geneticist_chat():
    st.markdown(f"""
<div style="padding:0.5rem 0 1rem 0;">
  <div style="font-size:1.3rem; font-weight:800; color:#e2e8f0;">{_t("gen_chat_header")}</div>
  <div style="color:#a0aec0; font-size:0.88rem;">{_t("gen_chat_subtitle")}</div>
</div>""", unsafe_allow_html=True)
    _synth_mini()

    if "geneticist_chat" not in st.session_state:
        st.session_state.geneticist_chat = []

    report = st.session_state.get("current_analysis_report")
    if report:
        pid  = report.get("patient_id","?")
        irt  = report.get("irt",{})
        prob = irt.get("probability_protection",0)
        risk = report.get("overall_risk_level","?")
        st.markdown(f"""
<div class="vg-card" style="margin-bottom:0.5rem; padding:0.7rem 1rem;">
  <span style="color:#63b3ed; font-weight:700;">{pid}</span>
  &nbsp;·&nbsp; {_t("p_protection")}: <strong>{prob:.0%}</strong>
  &nbsp;·&nbsp; {risk_badge(risk)}
  &nbsp;·&nbsp; <span class="live-badge">Context active</span>
</div>""", unsafe_allow_html=True)
    else:
        st.info(_t("gen_chat_no_patient"))

    _AV = {"user": "🙋", "assistant": "🧬"}
    for msg in st.session_state.geneticist_chat:
        with st.chat_message(msg["role"], avatar=_AV.get(msg["role"],"💬")):
            st.markdown(msg["content"])

    ui = st.chat_input(_t("gen_chat_placeholder"), key="geneticist_input")
    if ui:
        ctx = ""
        if report:
            irt = report.get("irt",{})
            ctx = (f"Patient {report.get('patient_id')}, {report.get('age')} yo, "
                   f"APOE={report.get('apoe_genotype')}, P(prot)={irt.get('probability_protection',0):.1%}, "
                   f"Risk={report.get('overall_risk_level')}, "
                   f"theta={irt.get('theta',0):+.3f}\n\n")
        with st.chat_message("user", avatar="🙋"):
            st.markdown(ui)
        with st.chat_message("assistant", avatar="🧬"):
            with st.spinner(_t("genetics_responding")):
                try:
                    _c = AgentCouncil()
                    resp = _c._llm_call(
                        _t("geneticist_system"),
                        f"{ctx}Question: {ui}", max_tokens=500, slug="geneticist")
                    if not resp:
                        resp = _t("no_llm")
                except Exception as exc:
                    resp = f"Error: {exc}"
            st.markdown(resp)
        st.session_state.geneticist_chat.append({"role":"user","content":ui})
        st.session_state.geneticist_chat.append({"role":"assistant","content":resp})


# ─── Custom profile tab ───────────────────────────────────────────────────────

def _render_create_profile_tab(platform):
    st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; padding:0.5rem 0 0.8rem 0;">
  <div>
    <div style="font-size:1.6rem; font-weight:800; color:#e2e8f0;">{_t("custom_header")}</div>
    <div style="color:#a0aec0; font-size:0.9rem;">{_t("custom_subtitle")}</div>
  </div>
  <span class="live-badge">IRT 4PL · 6 AI Agents</span>
</div>""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="synth-warning">
  <strong style="color:#f6e05e; font-size:0.95rem;">{_t("synth_warn_title")}</strong><br>
  <span style="color:#d69e2e; font-size:0.85rem;">{_t("synth_warn_body")}</span>
</div>""", unsafe_allow_html=True)

    if st.toggle(_t("methodology_toggle"), key="toggle_methodology"):
        st.markdown(f"""
**{_t("methodology_title")}**

| Variant/Locus | Frequency source | Sampling method |
|---|---|---|
| TLR4 rs4986790/rs4986791 | gnomAD v4 · dbSNP | Hardy-Weinberg equilibrium |
| TLR7 rs179008 (X-linked) | gnomAD v4 | Sex-adjusted |
| HLA class I (A, B, C) | HapMap CEU/AFR/EAS · IMGT/HLA 3.51 | Ancestry-weighted pool |
| HLA class II (DRB1, DQB1) | HapMap + 1000 Genomes | Ancestry-weighted pool |
| IL-6 rs1800795/96/97 | gnomAD v4 · Fishman et al. 1998 | LD haplotypes (r²≈0.4–0.6) |
| APOE rs429358/rs7412 | gnomAD v4 · AlzForum | ε2/ε3/ε4 allele combinations |
| TMPRSS2 rs2070788 | gnomAD v4 | Hardy-Weinberg equilibrium |
| STAT3 rs1137578 | gnomAD v4 | Independent |

**IRT 4PL engine:**
1. **TLR (35%)** — TLR4/TLR7/TLR9 variants affect adjuvant recognition
2. **HLA (40%)** — Class I/II alleles determine antigen presentation
3. **STAT/IL-6 (20%)** — Pro-inflammatory burden (cytokine storm risk)
4. **APOE (5%)** — LNP clearance rate (critical for mRNA vaccines)

θ_genetic → IRT 4PL → P(protection) per platform
""")

    st.markdown("---")
    _APOE_V  = _apoe_variants()
    _TLR4_V  = _tlr4_variants()
    _IL6_V   = _il6_variants()
    _TMPR_V  = _tmprss2_variants()
    _HLA_P   = _hla_presets()

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(_t("demo_data_label"))
        cp_name = st.text_input(_t("name_label"), value="My Patient" if st.session_state.get("lang","es")=="en" else "Mi Paciente", key="cp_name")
        cp_age  = st.slider(_t("age_label"), 1, 95, 35, key="cp_age")
        cp_sex  = st.selectbox(_t("sex_label"), ["Female","Male"],
                                format_func=lambda x: _t("sex_female") if x=="Female" else _t("sex_male"),
                                key="cp_sex")
        cp_eth  = st.selectbox(_t("ancestry_label"),
                                ["Latino","European","African","Asian","Other"],
                                format_func=lambda x: {
                                    "Latino":_t("anc_latino"),"European":_t("anc_european"),
                                    "African":_t("anc_african"),"Asian":_t("anc_asian"),"Other":_t("anc_other")
                                }[x], key="cp_eth")
        cp_cond = st.selectbox(_t("special_cond_label"), _COND_VALUES,
                                format_func=lambda v: _cond_label(v), key="cp_cond")
        cp_vax  = st.selectbox(_t("target_platform_label"),
                                ["mRNA","adenoviral_vector","protein_subunit"],
                                format_func=lambda x: {"mRNA":_t("mrna"),"adenoviral_vector":_t("adenoviral"),"protein_subunit":_t("protein_subunit")}[x],
                                key="cp_vax")

    with col_right:
        st.markdown(_t("genetic_profile_label"))
        cp_apoe  = st.selectbox("APOE", list(_APOE_V.keys()), index=2, key="cp_apoe",
                                 help="ε4/ε4: highest LNP risk (mRNA). ε3/ε3: typical European. ε2/ε2: lowest risk.")
        cp_hla   = st.selectbox("HLA", list(_HLA_P.keys()), key="cp_hla",
                                 help="HLA class II (DRB1) is the most relevant genetic factor in vaccine response.")
        cp_tlr4  = st.selectbox("TLR4 (Asp299Gly / Thr399Ile)", list(_TLR4_V.keys()), key="cp_tlr4",
                                 help="TLR4 variants reduce innate signaling. Homozygous = attenuated inflammatory response.")
        cp_il6   = st.selectbox("IL-6 Promoter (rs1800795 −174G>C)", list(_IL6_V.keys()), key="cp_il6",
                                 help="C/C: high IL-6 production → increased post-vaccine hyperinflammation risk.")
        cp_tmpr  = st.selectbox("TMPRSS2 (rs2070788 A>G)", list(_TMPR_V.keys()), key="cp_tmpr",
                                 help="G>G: higher TMPRSS2 expression, relevant for anti-coronavirus vaccines.")

    st.markdown("<br>", unsafe_allow_html=True)
    run_custom = st.button(_t("analyze_btn"), type="primary", use_container_width=True, key="btn_custom_profile")

    if run_custom:
        variants = {}
        variants.update(_APOE_V[cp_apoe])
        variants.update(_TLR4_V[cp_tlr4])
        variants.update(_IL6_V[cp_il6])
        variants.update(_TMPR_V[cp_tmpr])
        variants.update({
            "rs179008":  {"genotype":"G/G","risk_allele":"A","gene":"TLR7"},
            "rs5743836": {"genotype":"A/A","risk_allele":"A","gene":"TLR9"},
            "rs352140":  {"genotype":"A/A","risk_allele":"G","gene":"TLR9"},
            "rs1137578": {"genotype":"A/A","risk_allele":"G","gene":"STAT3"},
            "rs8099917": {"genotype":"T/T","risk_allele":"G","gene":"IFNL3"},
        })
        safe_name = re.sub(r'[^A-Z0-9]', '-', cp_name.upper())[:20].strip('-')
        pid = f"CUSTOM-{safe_name or 'PATIENT'}"
        patient_dict = {
            "patient_id": pid, "name": _html.escape(cp_name)[:50], "age": cp_age,
            "sex": cp_sex, "ethnicity": cp_eth,
            "variants": variants, "hla_haplotype": _HLA_P[cp_hla],
            "apoe_genotype": cp_apoe, "special_condition": cp_cond,
        }
        with st.spinner(_t("analyzing_custom")):
            try:
                cond_obj = SpecialCondition(cp_cond)
                rep_obj  = analyze_patient(
                    patient_id=pid, age=cp_age, sex=cp_sex,
                    variants=variants, hla_haplotype=_HLA_P[cp_hla],
                    apoe_genotype=cp_apoe, target_vaccine=cp_vax,
                    special_condition=cond_obj, run_cross_platform=True,
                )
                report = rep_obj.to_dict()
                st.session_state["custom_profile_patient"] = patient_dict
                st.session_state["custom_profile_report"]  = report
                st.session_state["custom_profile_vax"]     = cp_vax
                st.session_state["custom_council_messages"] = []
                st.session_state.current_analysis_report   = report
            except Exception as exc:
                st.error(_t("error_analysis", exc))
                return

    if st.session_state.get("custom_profile_report"):
        cp_report  = st.session_state["custom_profile_report"]
        cp_patient = st.session_state["custom_profile_patient"]
        cp_sel_vax = st.session_state.get("custom_profile_vax", platform)

        st.markdown("---")
        st.markdown(_t("results_label"))
        _render_patient_analysis(cp_patient, cp_report, cp_sel_vax)

        st.markdown("<br>", unsafe_allow_html=True)
        run_council_custom = st.button(
            _t("send_council_btn"), type="primary",
            use_container_width=True, key="btn_council_custom")

        if run_council_custom:
            st.session_state["custom_council_messages"] = []
            st.markdown("---")
            pid = cp_patient.get("patient_id","?")
            st.markdown(f"""
<div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
  <div style="font-size:1.1rem; font-weight:700; color:#e2e8f0;">{_t("council_session", pid)}</div>
  <span class="live-badge">{_t("ai_live")} · GPT-4o-mini</span>
</div>""", unsafe_allow_html=True)

            il6 = cp_report.get("module_scores",{}).get("stat",{}).get("il6_burden",0.0) or 0.0
            citations = get_citations(
                apoe_genotype=cp_patient.get("apoe_genotype",""),
                variants=cp_patient.get("variants",{}),
                hla_haplotype=cp_patient.get("hla_haplotype",[]),
                condition=cp_patient.get("special_condition","none"),
                il6_burden=il6,
            )
            agent_order = ["dr_genomico","dra_evidencia","ing_riesgo","doc_clinico","critico","doc_clinico_final"]
            slots = {slug: st.empty() for slug in agent_order}
            for slug in agent_order:
                p = COUNCIL_PERSONAS[slug]
                with slots[slug].container():
                    st.markdown(
                        f'<div class="agent-bubble" style="border-left:4px solid {_COUNCIL_COLORS[slug]}; opacity:0.4;">'
                        f'<span style="color:{_COUNCIL_COLORS[slug]};">{p.avatar} {p.name}</span>'
                        f' <span style="color:#718096; font-size:0.8rem;">{_t("waiting")}</span></div>',
                        unsafe_allow_html=True)

            _name_to_slug_c = {p.name: slug for slug, p in COUNCIL_PERSONAS.items()}

            def _on_prog_c(agent_name):
                slug = _name_to_slug_c.get(agent_name)
                if slug and slug in slots:
                    p = COUNCIL_PERSONAS[slug]
                    with slots[slug].container():
                        st.markdown(
                            f'<div class="agent-bubble" style="border-left:4px solid {_COUNCIL_COLORS[slug]};">'
                            f'<span class="live-badge" style="margin-right:8px;">{_t("agent_live")}</span>'
                            f'<span style="color:{_COUNCIL_COLORS[slug]};">{p.avatar} {p.name}</span>'
                            f' <span style="color:#a0aec0; font-size:0.8rem;">{_t("generating")}</span></div>',
                            unsafe_allow_html=True)

            def _on_msg_c(msg):
                with slots[msg.agent].container():
                    _render_agent_message(msg.to_dict())

            council = AgentCouncil()
            messages = council.stream_session(
                patient=cp_patient, report=cp_report, platform=cp_sel_vax,
                citations=citations, progress_callback=_on_prog_c, on_message=_on_msg_c,
            )
            st.session_state["custom_council_messages"] = [m.to_dict() for m in messages]

        elif st.session_state.get("custom_council_messages"):
            st.markdown("---")
            for msg in st.session_state["custom_council_messages"]:
                _render_agent_message(msg)


# ─── Landing page ─────────────────────────────────────────────────────────────

def _render_landing_page():
    st.markdown(f"""
<div style="text-align:center; padding:2rem 0 1rem 0;">
  <div class="main-title">🧬 VaccineGenics</div>
  <div style="font-size:1.15rem; color:#a0aec0; margin-top:0.5rem;">
    {_t("landing_title")}
  </div>
  <div style="color:#718096; max-width:650px; margin:0.8rem auto 1.2rem; line-height:1.7; font-size:0.92rem;">
    {_t("landing_subtitle")}
  </div>
</div>
<div style="max-width:720px; margin:0 auto 1.8rem auto;
     background:rgba(236,201,75,0.07); border:2px solid rgba(236,201,75,0.45);
     border-radius:12px; padding:1rem 1.4rem; text-align:center;">
  <div style="font-size:1.1rem; font-weight:800; color:#ecc94b; letter-spacing:0.04em;">
    {_t("synth_warn_title")}
  </div>
  <div style="color:#d69e2e; font-size:0.88rem; margin-top:0.4rem; line-height:1.6;">
    {_t("synth_warn_body")}
  </div>
</div>""", unsafe_allow_html=True)
    cols = st.columns(4)
    steps = [
        ("🧬", _t("step1_title"), _t("step1_desc")),
        ("📚", _t("step2_title"), _t("step2_desc")),
        ("📈", _t("step3_title"), _t("step3_desc")),
        ("🎭", _t("step4_title"), _t("step4_desc")),
    ]
    for col,(e,t,d) in zip(cols, steps):
        col.markdown(f"""
<div class="vg-card" style="text-align:center; min-height:130px;">
  <div style="font-size:2rem;">{e}</div>
  <div style="font-weight:700; color:#63b3ed; margin-top:6px;">{t}</div>
  <div style="color:#a0aec0; font-size:0.82rem; margin-top:4px;">{d}</div>
</div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _, dc, _ = st.columns([1,2,1])
    with dc:
        if st.button(_t("demo_btn"), type="primary", use_container_width=True):
            st.session_state["demo_trigger"] = True
            st.rerun()
    st.markdown(f'<div style="text-align:center; color:#4a5568; font-size:0.8rem; padding:1.5rem 0;">{_t("copyright")}</div>', unsafe_allow_html=True)


def _run_demo_cohort():
    cohort_list, reports_dict = [], {}
    for persona in DEMO_PERSONAS:
        cohort_list.append(dict(persona))
        try: cond = SpecialCondition(persona["special_condition"])
        except: cond = SpecialCondition.NONE
        rep = analyze_patient(
            patient_id=persona["patient_id"], age=persona["age"], sex=persona["sex"],
            variants=persona["variants"], hla_haplotype=persona["hla_haplotype"],
            apoe_genotype=persona["apoe_genotype"],
            target_vaccine=persona.get("target_vaccine","mRNA"),
            special_condition=cond, run_cross_platform=True,
        )
        reports_dict[persona["patient_id"]] = rep.to_dict()
    st.session_state.cohort_dicts = cohort_list
    st.session_state.reports      = reports_dict
    st.success(_t("demo_loaded", len(reports_dict)))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.markdown(_CSS, unsafe_allow_html=True)

    # Session state init
    defaults = {"reports":{},"cohort_dicts":[],"council_messages":[],
                "council_chat_history":[],"current_analysis_report":None,
                "custom_profile_patient":None,"custom_profile_report":None,
                "custom_profile_vax":"mRNA","custom_council_messages":[],
                "dash_council_pid":None,"dash_council_messages":[],
                "dash_council_report":None,"dash_council_patient":None,
                "lang":"es"}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Banner
    st.markdown(f'<div class="vg-banner">{_t("synth_banner")}</div>', unsafe_allow_html=True)

    # ── Control bar ──
    st.markdown('<div style="background:#151c2c; border:1px solid rgba(99,179,237,0.12); border-radius:10px; padding:0.8rem 1.5rem; margin-bottom:1.2rem;">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 1])
    with c1:
        n_patients = st.slider(_t("cohort_size"), 20, 2000, 100, 10)
    with c2:
        platform = st.selectbox(_t("vaccine_platform"),
            ["mRNA","adenoviral_vector","protein_subunit"],
            format_func=lambda x: {"mRNA":_t("mrna"),"adenoviral_vector":_t("adenoviral"),"protein_subunit":_t("protein_subunit")}[x])
    with c3:
        run_button = st.button(_t("run_analysis"), type="primary", use_container_width=True)
    with c4:
        if st.button(_t("clear"), use_container_width=True):
            _clear_session()
            st.rerun()
    with c5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(_t("lang_btn"), use_container_width=True, key="lang_toggle"):
            st.session_state["lang"] = "en" if st.session_state["lang"] == "es" else "es"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Run analysis ──
    if run_button:
        cohort_dicts = _load_cohort(n_patients)
        st.session_state.cohort_dicts = cohort_dicts
        progress = st.progress(0, text=_t("analyzing_cohort"))
        reports = []
        for i, p in enumerate(cohort_dicts[:n_patients]):
            try: cond = SpecialCondition(p.get("special_condition", SpecialCondition.NONE.value))
            except: cond = SpecialCondition.NONE
            try:
                rep = analyze_patient(
                    patient_id=p["patient_id"], age=p["age"], sex=p["sex"],
                    variants=p["variants"], hla_haplotype=p["hla_haplotype"],
                    apoe_genotype=p["apoe_genotype"], target_vaccine=platform,
                    special_condition=cond, run_cross_platform=True,
                )
                reports.append(rep.to_dict())
            except Exception as exc:
                st.warning(f"⚠️ {p.get('patient_id')}: {exc}")
            progress.progress((i+1)/n_patients, text=f"{_t('analyzing_cohort')} {i+1}/{n_patients}")
        progress.empty()
        st.session_state.reports = {r["patient_id"]: r for r in reports}
        st.success(_t("patients_analyzed", len(reports)))

    if st.session_state.pop("demo_trigger", False):
        with st.spinner(_t("loading_demo")):
            _run_demo_cohort()
        # Pre-select Fátima (HIV severo + VITT + TLR7 LOF — most complex case) in Council
        st.session_state["council_demo_idx"] = 6
        st.session_state["_demo_just_loaded"] = True

    # ── Tabs ──
    tab_dashboard, tab_council, tab_custom, tab_consult, tab_proteo = st.tabs([
        _t("tab_dashboard"),
        _t("tab_council"),
        _t("tab_custom"),
        _t("tab_consult"),
        _t("tab_proteo"),
    ])

    # Render non-dashboard tabs first so st.stop() in dashboard doesn't affect them
    with tab_council:
        _render_council_tab(platform)

    with tab_custom:
        _render_create_profile_tab(platform)

    with tab_consult:
        _render_geneticist_chat()

    with tab_proteo:
        render_proteomics_tab(platform, lang=st.session_state.get("lang","es"))

    # ── Dashboard (last so st.stop() doesn't block other tabs) ──
    with tab_dashboard:
        if not st.session_state.reports:
            st.info(_t("config_info"))
            _render_landing_page()
            st.stop()

        reports = list(st.session_state.reports.values())
        probs = [r["irt"]["probability_protection"] for r in reports]
        risk_counts = {l: sum(1 for r in reports if r["overall_risk_level"]==l)
                       for l in ["LOW","MODERATE","HIGH","CRITICAL"]}
        immunocomp_count = sum(1 for r in reports if r.get("special_condition","none") != "none")
        sero_count = sum(1 for r in reports if r["irt"].get("seroconversion_likely", False))
        avg_prob   = float(np.mean(probs)) if probs else 0.0

        if st.session_state.pop("_demo_just_loaded", False):
            _cta_msg = ("🎭 **Demo cargado.** Ve a la pestaña **Consejo de Agentes IA** — "
                        "Fátima (HIV severo + VITT risk) está preseleccionada como el caso más dramático."
                        if st.session_state.get("lang","es") == "es" else
                        "🎭 **Demo loaded.** Open the **AI Agent Council** tab — "
                        "Fátima (severe HIV + VITT risk) is pre-selected as the most complex case.")
            st.success(_cta_msg)

        _synth_mini()
        st.markdown(f'<div class="section-header">{_t("cohort_summary")}</div><div class="section-line"></div>', unsafe_allow_html=True)
        k1,k2,k3,k4,k5,k6 = st.columns(6)
        pc = "#48bb78" if avg_prob>=0.70 else ("#ed8936" if avg_prob>=0.50 else "#f56565")
        for col, val, lbl, color, top_color in [
            (k1, str(len(reports)),        _t("patients_kpi"),   "#fff",    "#63b3ed"),
            (k2, f"{avg_prob:.0%}",        _t("avg_prob_kpi"),   pc,        "#63b3ed"),
            (k3, str(sero_count),          _t("seroconv_kpi"),   "#48bb78", "#48bb78"),
            (k4, str(immunocomp_count),    _t("immunocomp_kpi"), "#63b3ed", "#63b3ed"),
            (k5, str(risk_counts["LOW"]),  _t("low_risk_kpi"),   "#48bb78", "#48bb78"),
            (k6, str(risk_counts["HIGH"]+risk_counts["CRITICAL"]), _t("high_crit_kpi"),"#f56565","#f56565"),
        ]:
            col.markdown(f'<div class="kpi-item" style="border-top-color:{top_color};"><div class="kpi-value" style="color:{color};">{val}</div><div class="kpi-label">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1: st.plotly_chart(plot_risk_distribution(reports), use_container_width=True)
        with c2: st.plotly_chart(plot_protection_histogram(reports), use_container_width=True)
        c3,c4 = st.columns(2)
        with c3: st.plotly_chart(plot_module_scores(reports), use_container_width=True)
        with c4: st.plotly_chart(plot_irt_curve(platform, height=300), use_container_width=True)

        st.divider()
        st.markdown(f'<div class="section-header">{_t("patient_deepdive")}</div><div class="section-line"></div>', unsafe_allow_html=True)
        _render_patient_deep_dive(platform)

        st.divider()
        st.markdown(f'<div class="section-header">{_t("cohort_table")}</div>', unsafe_allow_html=True)
        lang = st.session_state.get("lang","es")
        risk_map = ({"LOW":"Low","MODERATE":"Mod","HIGH":"High","CRITICAL":"CRITICAL"}
                    if lang=="en" else
                    {"LOW":"Bajo","MODERATE":"Mod","HIGH":"Alto","CRITICAL":"CRÍTICO"})
        rows = [{
            "ID": r["patient_id"],
            "Age" if lang=="en" else "Edad": r["age"],
            "Sex" if lang=="en" else "Sexo": {"Male":"M","Female":"F"}.get(r["sex"],"?"),
            "APOE": r["apoe_genotype"],
            "θ": round(r["irt"]["theta"],3),
            _t("p_protection"): f"{r['irt']['probability_protection']:.0%}",
            "Risk" if lang=="en" else "Riesgo": risk_map.get(r["overall_risk_level"],"?"),
        } for r in reports]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     height=min(420, len(rows)*35+40))


if __name__ == "__main__":
    main()
