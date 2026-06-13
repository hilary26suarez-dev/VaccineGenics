# VaccineGenics — Roadmap y Proyección de Impacto

> Documento de visión estratégica · Actualizado junio 2026

---

## El problema de escala que VaccineGenics resuelve

Cada año se administran **~1.8 mil millones de dosis de vacunas** en el mundo.
Se estima que **25–30% de la población** tiene al menos una variante farmacogenómica
clínicamente significativa que afecta su respuesta vacunal — y no lo sabe.

En América Latina el problema es mayor: las bases de datos genómicas globales
(gnomAD, HapMap) subrepresenstan gravemente a poblaciones latinoamericanas,
lo que significa que los modelos actuales están calibrados para europeos.

VaccineGenics nació como herramienta educativa/investigadora. Su potencial final
es convertirse en infraestructura de salud pública para precisión vacunal.

---

## Timeline de desarrollo

```
2026                2027                2028                2029-2030           2031+
  │                   │                   │                   │                   │
  ▼                   ▼                   ▼                   ▼                   ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FASE 0              FASE 1              FASE 2              FASE 3              FASE 4
MVP Inicial         Herramienta         Plataforma          Investigación       Plataforma
                    de Investigación    Académica           Clínica             Pública/Social

100% sintético      Colabs académicos   CONICIT/NSF grant   IRB-approved        Convenios
6 agentes AI        Auth institucional  Datos reales opt.   Validación clínica  institucionales
3 plataformas       API pública         Pub. indexada       Multi-país          Salud pública
vacunales           Azure Container     Latinoamérica       COFEPRIS path       OPS/OMS/CCSS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Fase 0 — Hackathon MVP (junio 2026, actual)

**Estado:** Proyecto estudiantil — Azure free tier + GitHub Models free tier

**Lo que existe:**
- Motor farmacogenómico con 4 módulos genéticos y modelo IRT 4PL
- Consejo de 6 agentes AI (GitHub Models + Azure AI Foundry)
- Dashboard de cohorte con hasta 2,000 pacientes sintéticos
- Proteómica con estructuras 3D reales (PDB)
- 8 casos demo clínicos, 12 condiciones especiales
- Datos 100% sintéticos — sin riesgo de privacidad

**Limitaciones conocidas:**
- Rate limits del tier gratuito de GitHub Models
- Sin autenticación de usuarios
- Sin persistencia de resultados entre sesiones
- Sin datos genómicos reales

---

## Fase 1 — Herramienta de Investigación (Q3 2026 – Q2 2027)

**Fuentes de recursos:** Azure for Research / Microsoft for Startups (créditos académicos gratuitos), horas de desarrollo estudiantil, publicaciones gratuitas (arXiv / bioRxiv)

**Infraestructura:**
```
Streamlit Cloud   →   Azure Container Apps    (autoscaling)
GitHub Models     →   Azure OpenAI Service    (sin rate limit diario)
Sin caché         →   Azure Redis Cache       (resultados reutilizables)
Sin auth          →   Microsoft Entra ID      (correo institucional)
Sin BD            →   Azure Cosmos DB         (historial por investigador)
```

**Hitos:**
- [ ] API REST pública con documentación Swagger (investigadores sin UI)
- [ ] Login con correo institucional UCIMED / UCR / TEC
- [ ] Exportación de análisis a CSV / JSON citable
- [ ] Rate limiting por rol (estudiante / investigador / institución)
- [ ] Preprint en bioRxiv: _"VaccineGenics: A Multi-Agent AI Framework for Pharmacogenomic Vaccine Optimization"_

**Usuarios objetivo:** 100–500 investigadores en UCIMED y universidades colaboradoras en Costa Rica

---

## Fase 2 — Plataforma Académica Regional (Q3 2027 – Q2 2028)

**Fuentes de recursos:** Beca CONICIT (Costa Rica), NSF International, Microsoft Academic Alliance, convenios universitarios

**El cambio crítico de Fase 2: datos genómicos reales (opt-in)**

Con aprobación de comité de ética e IRB, se integran datos genómicos
anonimizados de participantes voluntarios en estudios de vacunación de UCIMED.
Esto permite calibrar el modelo para poblaciones latinoamericanas — el gap más
importante que existe en la literatura actual.

**Base de datos latinoamericana propia:**
```
gnomAD (actual) — cobertura latinoamericana: ~8% de variantes
VaccineGenics DB (meta) — cobertura latinoamericana: 60%+ de variantes

Poblaciones subrepresentadas a incluir:
  Mestizo costarricense · Chorotega · Cabécar · Ngäbe-Buglé
  Afrocostarricense · Poblaciones del Pacífico centroamericano
```

**Hitos:**
- [ ] Publicación peer-reviewed en revista indexada (Bioinformatics, JAMIA, o similar)
- [ ] Convenio con ≥3 universidades latinoamericanas (UCR, UNIBE Panamá, UES)
- [ ] Modo batch: análisis de cohortes completas subidas en CSV
- [ ] DOI por análisis: cada resultado es citable en papers
- [ ] API partner para laboratorios genómicos locales en LATAM

**Usuarios objetivo:** 2,000–5,000 investigadores en 5+ países latinoamericanos

---

## Fase 3 — Investigación Clínica (2028–2030)

**Fuentes de recursos:** Fondos de innovación en salud (CCSS, OPS/OMS, BID Salud), becas de investigación clínica, convenios con ministerios de salud

**El salto crítico: de herramienta de investigación a soporte clínico**

Este paso requiere:
1. Aprobación IRB para uso con datos de pacientes reales
2. Validación prospectiva en estudio clínico controlado
3. Inicio de proceso regulatorio (COFEPRIS México / INVIMA Colombia / ruta equivalente)
4. Auditoría de sesgo algorítmico por población

**Arquitectura de Fase 3:**
```
Capa Clínica (nueva):
├── Integración con HL7 FHIR (estándar de registros médicos)
├── Conector a laboratorios de secuenciación (Illumina, Ion Torrent)
├── Módulo de explicabilidad (SHAP values por variante)
├── Audit trail completo para regulación
└── Dashboard para farmacéutico / genetista clínico

Capa AI actualizada:
├── Modelos fine-tuneados con datos latinoamericanos propios
├── RAG sobre literatura actualizada automáticamente (PubMed API live)
└── Agente de vigilancia de nuevas variantes (alertas de literatura)
```

**Hitos:**
- [ ] Estudio de validación clínica en ≥500 pacientes reales (con consentimiento)
- [ ] Publicación en NEJM / The Lancet Digital Health
- [ ] Acuerdo piloto con CCSS (Caja Costarricense de Seguro Social)
- [ ] Inicio de proceso regulatorio regional
- [ ] Primera integración con fabricante de vacunas (brazo de investigación)

**Usuarios objetivo:** 10,000+ investigadores + primeros usuarios clínicos piloto

---

## Fase 4 — Plataforma de Impacto Social (2030 en adelante)

**Modelo de impacto:**

```
Herramienta para investigación (más rápido de desplegar)
├── API para universidades y laboratorios genómicos
├── Plataforma SaaS para departamentos de farmacogenómica
└── Base de datos latinoamericana como recurso académico abierto

Alianzas con sector salud
├── Convenios con fabricantes de vacunas para análisis de subgrupos
│   (descubrir por qué cierto % de un ensayo clínico no responde)
└── Data partnership para vacunas de nueva generación más inclusivas

Salud pública (largo plazo)
├── Programas nacionales de vacunación de precisión en LATAM
└── Piloto OPS/OMS para países de ingresos medios
    (Costa Rica, Panamá, Colombia como casos piloto)
```

---

## Proyección de impacto en salud pública

### El número que importa

```
Población mundial con variante farmacogenómica significativa:  ~2,000 millones
Vacunas administradas por año:                                 ~1,800 millones dosis
Superposición (personas con variante + vacunadas):             ~500 millones/año

Si VaccineGenics mejora la selección de plataforma vacunal
y reduce respuestas subóptimas en un 20%:

→ 100 millones de mejores respuestas vacunales por año
```

### Impacto específico en América Latina

| País | Programa de vacunación | Gap genómico actual | Impacto potencial |
|---|---|---|---|
| Costa Rica | Universal CCSS | Alto (poca data local) | Modelo de validación |
| México | Bienestar + IMSS | Muy alto | Mayor escala LATAM |
| Colombia | PAI nacional | Alto | Hub de datos |
| Brasil | PNI (mayor de LATAM) | Moderado (más estudios) | Validación externa |

### Comparación con herramientas existentes

| Herramienta | Foco | AI multi-agente | Latinoamérica | Open source |
|---|---|---|---|---|
| PharmGKB | Base de datos | No | No | Sí (datos) |
| CPIC Guidelines | Guías clínicas | No | No | Sí |
| GenomeMed | Clínico (comercial) | No | No | No |
| **VaccineGenics** | **Vacunas + reasoning** | **Sí — 6 agentes** | **Sí — prioridad** | **Sí** |

---

## Equipo que requiere el proyecto

```
Fase 1 (investigación):
  Hilary Suárez — Lead developer + pharmacogenomics domain    [ya existe]
  Mentor clínico (UCIMED) — validación médica               [por conseguir]
  TOTAL: 1.5 personas

Fase 2 (plataforma académica):
  + 1 Bioinformático (análisis de variantes latinoamericanas)
  + 1 Frontend developer (mejorar UX para investigadores)
  TOTAL: 3–4 personas

Fase 3 (investigación clínica):
  + 1 Farmacogenomista clínico titulado
  + 1 Regulatory affairs specialist
  + 1 DevOps / cloud architect
  TOTAL: 6–7 personas

Fase 4 (impacto social):
  + Coordinadores de alianzas institucionales
  + Equipo científico expandido por región
  TOTAL: 15–20 personas
```

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Falta de datos genómicos latinoamericanos | Alto | Alto | Alianza con biobancos regionales desde Fase 2 |
| Regulación médica | Medio | Alto | Mantenerse como "soporte a investigación" hasta completar validación Fase 3 |
| Sesgo algorítmico en subpoblaciones | Medio | Alto | Audit de equidad desde Fase 1, publicar métricas de bias |
| Competidor institucional grande | Medio | Medio | Ventaja: foco en LATAM, datos propios, relaciones institucionales locales |
| Dependencia de Azure/GitHub Models | Bajo | Bajo | Arquitectura multi-proveedor desde Fase 2 |

---

## La visión en una línea

> VaccineGenics es el primer motor de precisión vacunal construido específicamente para
> poblaciones latinoamericanas, combinando farmacogenómica cuantitativa con razonamiento
> multi-agente — atacando el mayor gap de equidad en salud del mercado de medicina de
> precisión: las poblaciones que más lo necesitan son las menos representadas en los datos.

---

*VaccineGenics · Precision Vaccine Intelligence · Visión a 5 años*
*© 2026 Hilary Suárez · hilary26suarez@gmail.com*
