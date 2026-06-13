# 🧬 VaccineGenics — Precision Vaccine Intelligence with Multi-Agent AI

> _"Your DNA determines whether a vaccine will protect you. VaccineGenics calculates it."_

[![Azure AI](https://img.shields.io/badge/Azure%20AI-GitHub%20Models%20%7C%20Foundry-cyan)](https://models.inference.ai.azure.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-red)](https://vaccinegenics-dbzefqukskjcbuuwkptufn.streamlit.app/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)
[![Research](https://img.shields.io/badge/Research-Precision%20Vaccinology-blue)](#)

> ⚠️ **All patient data is 100% synthetic.** No real patient data is used, stored, or processed.
> This tool is for educational and research purposes only — not for clinical decisions.

---

## 🎬 Demo

> **[▶ Live App on Streamlit Cloud](https://vaccinegenics-dbzefqukskjcbuuwkptufn.streamlit.app/)**
>
> **▶ Watch the 5-minute demo on YouTube** — _link added before submission deadline_

---

## 🔬 What Problem Does VaccineGenics Solve?

Standard vaccine protocols treat every patient identically. But genomic variants in **TLR4, HLA-DRB1, STAT3, IL-6, and APOE** genes mean two people receiving the same vaccine can have radically different immune responses — one achieving 90% protection, the other barely 40%.

VaccineGenics uses **pharmacogenomics** and a **6-agent AI council** to answer:

> _"Given this patient's DNA, which vaccine platform gives the best protection — and what is the clinical evidence?"_

It is a reasoning-first clinical knowledge engine for **precision vaccinology**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VACCINEGENICS SYSTEM                             │
│                                                                         │
│   Patient Genomic Profile (100% synthetic)                              │
│   SNPs: TLR4 · HLA-DRB1 · STAT3 · IL-6 · APOE · TMPRSS2 + 7 more     │
│                              │                                          │
│                              ▼                                          │
│         ┌────────────────────────────────────────┐                      │
│         │      PHARMACOGENOMICS ENGINE           │                      │
│         │  • 4 genetic modules (TLR/HLA/STAT/APOE)                     │
│         │  • IRT 4PL immunogenicity model        │                      │
│         │  • Cross-platform comparison (3 vaccines)                     │
│         │  • 12 special conditions (HIV, transplant, cancer…)          │
│         └────────────────────┬───────────────────┘                      │
│                              │  θ_clinical · P(protection) · Risk flags │
│                              ▼                                          │
│  ┌────────────────── 6-AGENT AI COUNCIL ──────────────────────────┐    │
│  │                                                                  │    │
│  │  🧬 Dr. Genómico ──► 📚 Dra. Evidencia ──► ⚙️ Ing. Riesgo      │    │
│  │  Genomic analysis    PubMed PMIDs cited    IRT results + code   │    │
│  │  (GitHub Models)     (GitHub Models)       (GitHub Models)      │    │
│  │                           │                                      │    │
│  │                           ▼                                      │    │
│  │       🩺 Doc. Clínico ──► 🔎 Crítico ──► 🩺 Doc. Clínico Final  │    │
│  │       Clinical synthesis  Adversarial      FINAL verdict         │    │
│  │       (GitHub Models)     review           Azure Foundry o4-mini │    │
│  │                           (GitHub Models)                        │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│        ┌─────────────────────┼──────────────────────┐                  │
│        ▼                     ▼                      ▼                  │
│  📊 Cohort Dashboard   🔬 Genomics Chat      🧫 Proteomics              │
│  Risk stratification   Live Q&A with         3D protein structures      │
│  IRT curves · 2,000    clinical geneticist   Variant impact heatmaps    │
│  patients · rankings   AI (GitHub Models)    3Dmol.js + PDB real data  │
└─────────────────────────────────────────────────────────────────────────┘

Microsoft AI Infrastructure:
  ├── GitHub Models / Azure AI Inference  →  Agents 1–5  (gpt-4o-mini)
  └── Azure AI Foundry Responses API      →  Agent 6 — Doc. Clínico Final (o4-mini)
```

---

## ⚡ Key Features

| Feature | Description |
|---|---|
| **6-Agent Reasoning Council** | Sequential debate: each agent builds on the previous output. Agent 6 uses Azure AI Foundry o4-mini for the final clinical recommendation. |
| **IRT 4PL Model** | Item Response Theory 4-Parameter Logistic — adapted from educational measurement to model vaccine immunogenicity. θ (theta) = immune capacity score. |
| **Cross-Platform Comparison** | Same DNA, 3 vaccine platforms (mRNA, Adenoviral Vector, Protein Subunit) — ranked by P(protection). |
| **12 Special Conditions** | HIV (controlled/moderate/severe), organ transplant, bone marrow transplant, active cancer, biologics, steroids, radiation → theta penalty applied. |
| **Literature Grounding** | Dra. Evidencia cites PubMed PMIDs in every response. 20+ curated pharmacogenomics references. |
| **Live Genomics Chat** | Ask any follow-up question to an AI clinical geneticist after the council runs. |
| **Cohort Dashboard** | Simulate 20–2,000 synthetic patients. Risk distribution, IRT curves, module score analysis, patient deep-dive. |
| **Adversarial Review** | Crítico Interno challenges the weakest assumption — responsible AI by design. |
| **Custom Patient Profile** | Build your own synthetic patient: choose HLA alleles, APOE genotype, TLR4/IL-6/TMPRSS2 variants, special conditions — get a full AI council analysis. |
| **Proteomics** | 5-section protein visualization: variant→protein→vaccine network, real 3D structures (3Dmol.js, RCSB PDB), vaccine mechanism pathway, patient impact heatmap. |
| **8 Clinical Demo Cases** | Elena (HIV), Fatima (HIV severe + VITT risk), Carlos (standard), Sofia (cancer), Marco (pediatric), Roberto (biologics), Ana (transplant), Miguel (APOE ε4/ε4). |

---

## 🎯 Challenge Alignment

### Reasoning Agents Track

| Requirement | VaccineGenics Implementation |
|---|---|
| **Multi-step reasoning** | 6-agent sequential pipeline — each agent uses the previous agent's full output as context |
| **Complex problem** | Pharmacogenomics: which of 3 vaccine platforms best fits this patient's DNA and clinical condition? |
| **Knowledge grounding** | PubMed KB · Dra. Evidencia cites real PMIDs · 20+ curated pharmacogenomics references |
| **Quantitative assessment** | IRT 4PL computes θ_clinical and P(protection) with 95% CI for each platform |
| **Population-level insights** | Cohort dashboard: 2,000 patients, risk stratification, module score distribution, cross-platform ranking |
| **Adversarial validation** | Crítico Interno agent stress-tests the recommendation before it is finalized |
| **Follow-up reasoning** | Council follow-up chat + Genomics Chat for post-analysis Q&A |

### Foundry IQ Requirement ✅

VaccineGenics uses **Azure AI Foundry infrastructure** at two levels:

1. **GitHub Models / Azure AI Inference** (`models.inference.ai.azure.com`) — Agents 1–5 with `gpt-4o-mini`. Part of Azure AI Foundry's unified model catalog.
2. **Azure AI Foundry Responses API** — Agent 6 (Doc. Clínico Final) calls the pre-deployed `vaccinegenics` Foundry agent via `POST {endpoint}/openai/v1/responses?api-version=2025-01-01-preview` with `o4-mini`.

Every call to Agent 6 is traced in Azure Application Insights automatically.

### Hack for Good & Best Student Categories

- **Hack for Good**: Addresses real healthcare equity gap — patients with specific genetic profiles are under-served by one-size-fits-all vaccine programs. VaccineGenics enables precision vaccinology at zero marginal cost using AI reasoning.
- **Best Student**: Built solo by a medical student in Costa Rica, combining clinical pharmacogenomics expertise with full-stack AI engineering.

---

## 🛠️ Technology Stack

```
AI / Agents
├── Azure AI Foundry (Responses API)   →  Agent 6: final recommendation (o4-mini)
├── GitHub Models / Azure AI Inference →  Agents 1–5: council debate (gpt-4o-mini)
└── 6-agent sequential orchestrator    →  council.py (custom, no framework dependency)

Pharmacogenomics Engine (custom Python)
├── IRT 4PL model                      →  irt_model.py
├── 4 genetic modules                  →  TLR / HLA / STAT / APOE
├── Cross-platform comparator          →  cross_platform_analysis.py
└── 12 special condition handlers      →  immunocompromised_module.py

Frontend
├── Streamlit 1.45+                    →  Dashboard + 5 tabs + real-time streaming
├── Plotly                             →  IRT curves, network graphs, heatmaps
└── 3Dmol.js (CDN)                     →  Real PDB protein structures (no pip install)

Data
├── Synthetic patient generator        →  Hardy-Weinberg, gnomAD allele frequencies
├── 8 clinical demo personas           →  patient_personas.py
├── 20+ PubMed citations               →  literature_kb.py
└── RCSB PDB structures                →  TLR4/3FXI, HLA-DRB1/2SEB, APOE/3R4L, IL-6/1ALU
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- A [GitHub personal access token](https://github.com/settings/tokens) (free — no scopes needed for public model access)
- Optional: Azure AI Foundry project endpoint + API key (Agent 6 falls back gracefully without it)

### 1. Clone and install

```bash
git clone https://github.com/hilary26suarez-dev/VaccineGenics.git
cd VaccineGenics
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root (never commit this file):

```env
# Required — get at github.com/settings/tokens (free, no special scopes needed)
GITHUB_TOKEN=ghp_your_token_here

# Optional — Azure AI Foundry for Agent 6 (Doc. Clínico Final)
AZURE_AI_PROJECT_ENDPOINT=https://<hub>
AZURE_AI_PROJECT_KEY=your_key_here
AZURE_AI_AGENT_MODEL=o4-mini
```

### 3. Run

```bash
python -m streamlit run run_ui.py
```

Open `http://localhost:8501` in your browser.

**Or use the live Streamlit Cloud deployment** — no setup required:
`https://vaccinegenics-dbzefqukskjcbuuwkptufn.streamlit.app/`

---

## 📖 How It Works — Step by Step

### Step 1 — Choose or build a patient profile

- **8 pre-built clinical demo cases**: Elena (HIV controlled), Fátima (HIV severe + TLR7 LOF + VITT risk HLA), Marco (pediatric high-responder), Sofía (active cancer), Roberto (biologics), Ana (transplant), Carlos (standard), Miguel (APOE ε4/ε4)
- **Custom profile builder** (🧬 Mi Perfil tab): select HLA alleles, APOE genotype, TLR4/IL-6/TMPRSS2 variants, special conditions — full council analysis on your custom patient
- **Synthetic cohort** (📊 Dashboard): generate 20–2,000 random patients from population-level allele frequencies

### Step 2 — Pharmacogenomics Engine scores the profile

Four genetic modules with weighted contributions:

| Module | Weight | What it scores |
|---|---|---|
| TLR | 35% | Innate immunity signal — TLR4, TLR7, TLR9 variants |
| HLA | 40% | Adaptive immunity — HLA class I & II allele binding efficiency |
| STAT | 20% | Cytokine amplification — IL-6, STAT3 burden |
| APOE | 5% | LNP delivery — nanoparticle clearance rate (mRNA critical) |

Weighted scores → **θ_genetic** → IRT 4PL → **P(protection)** per vaccine platform.

### Step 3 — 6-Agent AI Council debates

| Agent | Role | LLM |
|---|---|---|
| 🧬 Dr. Genómico | Identify the most clinically significant variants | gpt-4o-mini |
| 📚 Dra. Evidencia | Cite PubMed literature for each variant finding | gpt-4o-mini |
| ⚙️ Ing. de Riesgo | Present IRT numbers, show the 4PL code, compare platforms | gpt-4o-mini |
| 🩺 Doc. Clínico | Synthesize findings into an initial recommendation | gpt-4o-mini |
| 🔎 Crítico Interno | Adversarially challenge the weakest assumption | gpt-4o-mini |
| 🩺 Doc. Clínico Final | Answer the critic → issue the final verdict with confidence | **o4-mini (Azure Foundry)** |

### Step 4 — Explore results

- Final recommendation with risk badge (LOW / MODERATE / HIGH / CRITICAL)
- IRT curve with patient's θ highlighted on the logistic
- Cross-platform ranking table (which vaccine is #1, #2, #3 — or ⛔ contraindicated)
- Proteomics: 3D protein structures, variant impact on TLR4/HLA/APOE/IL-6
- Follow-up chat with the full council or a clinical geneticist AI

---

## 🧫 Proteomics

The **🧫 Proteómica** tab visualizes the molecular mechanisms behind the pharmacogenomics engine:

1. **Variant → Protein → Vaccine Network** — Plotly graph showing how each patient variant connects to the key proteins and which vaccine platforms they affect
2. **3D Protein Structures** — Real PDB structures rendered live via 3Dmol.js (no backend required):
   - TLR4 (PDB: 3FXI) — mutation site Asp299Gly highlighted
   - HLA-DRB1 (PDB: 2SEB) — peptide-binding groove
   - APOE (PDB: 3R4L) — Cys112→Arg ε4 defining residue
   - IL-6 (PDB: 1ALU) — cytokine structure
   - TMPRSS2 (PDB: 7MEQ) — serine protease catalytic site
3. **Vaccine Mechanism Pathway** — Step-by-step diagram for the selected platform with patient variant effects overlaid
4. **Patient Impact Heatmap** — Protein × Platform matrix, colored by the patient's actual variant impact score

---

## 📂 Project Structure

```
VaccineGenics/
├── src/
│   ├── ui/
│   │   ├── app.py                    ← Streamlit dashboard (main entry, 5 tabs)
│   │   ├── proteomics_tab.py         ← Proteomics tab (3Dmol.js, network, heatmap)
│   │   └── reasoning_telemetry.py    ← Agent trace visualization
│   ├── agent/
│   │   ├── council.py                ← 6-agent orchestrator (all live LLM calls)
│   │   ├── foundry_agent.py          ← Azure AI Foundry Responses API integration
│   │   └── system_prompt.py          ← VaccineGenics clinical system prompt
│   ├── pharmacogenomics/
│   │   ├── risk_calculator.py        ← Main pharmacogenomics engine
│   │   ├── irt_model.py              ← IRT 4PL implementation
│   │   ├── cross_platform_analysis.py← 3-platform ranking
│   │   └── modules/
│   │       ├── tlr_module.py         ← TLR4/7/9 innate immunity
│   │       ├── hla_module.py         ← HLA class I & II adaptive immunity
│   │       ├── stat_module.py        ← IL-6/STAT3 cytokine pathway
│   │       ├── apoe_module.py        ← LNP delivery / APOE clearance
│   │       └── immunocompromised_module.py ← 12 special conditions
│   ├── synthetic/
│   │   ├── patient_generator.py      ← Cohort generator (Hardy-Weinberg, gnomAD)
│   │   └── patient_personas.py       ← 8 pre-built clinical demo cases
│   └── data/
│       └── literature_kb.py          ← 20+ PubMed pharmacogenomics citations
├── config.py                         ← IRT parameters, module weights
├── run_ui.py                         ← App entry point (Streamlit Cloud compatible)
├── requirements.txt
├── evals/                            ← 8-case validation set
│   └── eval_cases.json
└── .env.example                      ← Secrets template (never commit .env)
```

---

## 🧪 Validation

VaccineGenics includes an 8-case synthetic validation set (`evals/eval_cases.json`) covering:

| Case | Profile | Expected outcome |
|---|---|---|
| APOE ε4/ε4 | mRNA LNP | ⛔ Contraindicated — rapid LNP clearance |
| HLA-DRB1\*11:04 | Adenoviral vector | ⚠️ VITT risk — avoid |
| HIV severe | Any | HIGH risk — reduced immunogenicity |
| TLR4 Asp299Gly double mutant | Protein subunit | Moderate reduction |
| Pediatric (9 yr) high-responder HLA | mRNA | HIGH immunogenicity |
| Autoimmune + tocilizumab (anti-IL-6) | Protein subunit | Preferred — lower cytokine burden |
| Standard ε3/ε3 | mRNA | LOW risk — optimal response |
| HIV controlled | mRNA | MODERATE — manageable with monitoring |

Target: ≥80% accuracy on platform recommendation.

---

## 🔒 Privacy, Ethics & Security

| Principle | Implementation |
|---|---|
| **No real patient data** | All genomic profiles are synthetically generated using Hardy-Weinberg equilibrium and gnomAD population frequencies |
| **Transparent simulation** | Amber warning banner on every page: "DATOS 100% SINTÉTICOS — Solo investigación educativa" |
| **Credential security** | `.env` in `.gitignore` — never committed. Streamlit Cloud secrets via dashboard only. |
| **Input sanitization** | Free-text patient names sanitized with regex + `html.escape()` before HTML rendering |
| **Adversarial agent** | Crítico Interno is a built-in responsible-AI mechanism — it must challenge the recommendation before the final verdict |
| **No clinical claims** | Every output includes: "Not for clinical use. Consult a healthcare provider." |

---

## 👩‍💻 About the Developer

**Hilary Suárez** — Biotech Engineering student at **UCIMED** (Universidad de Ciencias Médicas), San José, Costa Rica 🇨🇷

Built solo, combining biomedical domain knowledge with full-stack AI engineering. VaccineGenics addresses a real gap observed during academic training: patients with identical vaccine schedules have radically different protection outcomes due to genetic variation — and current clinical tools don't account for it.

**Competing categories:**
- 🧠 **Reasoning Agents** — 6-agent sequential AI council with adversarial validation (Azure AI Foundry)
- 🌎 **Hack for Good** — AI for healthcare equity in underrepresented Latin American populations
- 🎓 **Best Student** — International student entry · Costa Rica · UCIMED

This project is supported for publication by UCIMED as part of its AI and precision medicine research program.

---

## 🗺️ Roadmap & Investment Projection

> **[→ Full 5-year development roadmap: ROADMAP.md](ROADMAP.md)**

VaccineGenics is designed as a living platform with four development phases:

```
PHASE 0          PHASE 1          PHASE 2          PHASE 3          PHASE 4
Initial MVP      Research Tool    Academic         Clinical         Public Impact
(now)            Q3 2026–Q2 2027  Platform         Research         Platform
─────────────────────────────────────────────────────────────────────────────
6-agent MVP  →   Container Apps   Latin America →  IRB-approved  →  Institutional
Synthetic data   Auth + API       genomic data     Validation        partnerships
3 platforms      Redis cache      Peer-reviewed    COFEPRIS path     OPS/WHO/CCSS
```

### The number that matters

> ~500 million people per year receive vaccines while carrying pharmacogenomic
> variants that affect their immune response — and they don't know it.
> VaccineGenics is built to close that gap, starting with Latin America,
> the most underrepresented population in current genomic databases.

| Phase | Timeline | Users | Key milestone |
|---|---|---|---|
| 0 — MVP inicial | Jun 2026 | Early adopters | 6-agent council, proteomics |
| 1 — Research tool | Q3 2026 | 100–500 researchers | Public API, institutional auth, preprint |
| 2 — Academic platform | Q3 2027 | 2,000–5,000 | Latin American genomic DB, indexed publication |
| 3 — Clinical research | 2028 | 10,000+ | IRB validation study, health system pilot |
| 4 — Public impact | 2030+ | Regional | OPS/OMS partnerships, ministerial agreements |

**Latin America is the most underserved region in global genomic databases — and the highest-need market for precision vaccinology.**

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

Copyright (c) 2026 Hilary Suárez

---

*VaccineGenics · Precision Vaccine Intelligence · © 2026 Hilary Suárez*
