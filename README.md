# ¿De dónde salen los futbolistas argentinos?

**Geografía del talento en el fútbol argentino: un test del *birthplace effect*.**

¿Los futbolistas argentinos nacen desproporcionadamente en el interior y en
ciudades chicas y medianas, respecto de lo que correspondería por la población de
esos lugares? Este repo contiene el pipeline reproducible que responde esa
pregunta con datos, no con folklore.

La especificación completa del estudio está en [CLAUDE.md](CLAUDE.md); las
decisiones de diseño, en [config.yaml](config.yaml).

---

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Probado en Python 3.14.5 sobre Windows 11.

---

## Cómo se corre

```powershell
python -m src.ingest.wikidata_players      # Fase 1
python -m src.ingest.indec_census          # Fase 2
python -m src.ingest.ign_boundaries        # Fase 2
python -m src.clean.geocode_birthplaces    # Fase 3
python -m src.analysis.run_all             # Fase 5
python -m src.viz.make_figures             # Fase 6
```

Cada script es idempotente: si el crudo ya está descargado no lo vuelve a pedir
(salvo `--force`).

---

## Fuentes de datos

| Qué | Fuente | Licencia / acceso |
|---|---|---|
| Jugadores, lugar de nacimiento, posición, clubes | [Wikidata](https://query.wikidata.org/) vía SPARQL | CC0 |
| Población por departamento, localidad, edad, sexo y provincia de nacimiento | [INDEC — Censo 2022, microdatos REDATAM](https://datos.gob.ar/dataset/censo-nacional-de-poblacion-hogares-y-viviendas-2022) | Datos abiertos |
| Códigos geográficos oficiales | [INDEC — Códigos geográficos 2022](https://datos.gob.ar/dataset/codigos-geograficos-del-indec-2022) | Datos abiertos |
| Normalización de localidades → departamento/provincia | [API Georef](https://apis.datos.gob.ar/georef/api/) | Datos abiertos |
| Límites provinciales y departamentales (mapas) | [IGN](https://www.ign.gob.ar/) | Datos abiertos |

**Transfermarkt no se usa:** sus términos prohíben el scraping automatizado. Si en
la Fase 7 hiciera falta el club formador para H3, se obtiene de fuentes con
licencia o del texto de Wikipedia, nunca scrapeando Transfermarkt.

---

## Supuestos y decisiones (resumen)

Todos justificados en línea en [config.yaml](config.yaml).

- **Muestra.** Todo futbolista con ciudadanía argentina en Wikidata y lugar de
  nacimiento dentro de Argentina. Muestra principal masculina; la femenina se
  analiza aparte por cobertura y literatura distintas.
- **Cohortes.** Análisis principal: nacidos **1970–2000**. El límite lo pone el
  denominador, no Wikidata: el Censo 2022 solo cuenta a quien seguía vivo y en el
  país en 2022, así que hacia atrás el denominador se erosiona; hacia adelante la
  carrera está censurada a derecha.
- **Unidades.** Provincia, **departamento** (nivel principal, 529 unidades) y
  localidad censal (define el tamaño de ciudad).
- **Tamaño de ciudad.** Dos esquemas de corte: el del diseño
  (<10k / 10–50k / 50–100k / 100–500k / >500k) y el de Côté et al. (2006) para
  comparar con la literatura. Se reportan los dos: si el efecto aparece con uno
  solo, es un artefacto de la partición.
- **Denominador.** Tres baselines, se reportan todos:
  `census_total` (población total del lugar), `census_cohort` (población del lugar
  **restringida a la edad** de la cohorte — el principal) y `birth_province`
  (personas censadas en 2022 que declararon haber nacido en esa provincia, por
  cohorte de edad; solo a nivel provincial).
- **Normalización.** Por **coordenada** (`P625`) contra Georef, no por matching de
  strings. Lo que queda ambiguo se marca `unresolved`; **no se adivina.**

---

## Limitaciones declaradas

1. **Nacer ≠ formarse.** Wikidata da el lugar de nacimiento, no el de desarrollo.
   La literatura reciente sugiere que lo que más pesa es la *transición* entre
   ambos. El análisis base es válido y es la metodología clásica del campo, pero
   H3 (flujo nacimiento → club formador) requiere un dato que hay que conseguir
   aparte.
2. **Cobertura sesgada de Wikidata.** Los jugadores notables están
   sobrerrepresentados. Si la notoriedad correlaciona con la geografía, el efecto
   estimado se distorsiona. Se chequea con la variable de prominencia
   (`sitelinks`) y con los tiers de nivel competitivo.
3. **Baseline temporal.** El tamaño de la localidad se mide en el Censo 2022, no
   en la infancia del jugador. Se corre un análisis restringido a cohortes
   recientes como control. **No se interpola población.**
4. **Denominador por residencia, no por nacimiento.** A nivel departamento y
   localidad, el censo cuenta dónde vive la gente, no dónde nació. A nivel
   provincia sí existe el dato de nacimiento (variable `P14`) y por eso se reporta
   ese baseline aparte.

---

## Estructura

```
data/{raw,interim,processed}/   # raw es intocable; no se versiona (sí los manifiestos)
src/{ingest,clean,analysis,viz}/
notebooks/                      # EDA
outputs/{figures,tables}/
reports/                        # el paper
tests/
```

---

## Reproducibilidad

- `data/raw/` no se edita nunca; cada descarga deja un `_manifest.json` fechado
  con la URL, el tamaño y el SHA-256.
- El snapshot de Wikidata queda fechado en `data/raw/wikidata/_snapshot.json`.
  Wikidata cambia todos los días: sin esa fecha los números no se reproducen.
- Seeds fijadas en `config.yaml` (`stats.random_seed`).
- Los datos derivados no se versionan: se regeneran corriendo el pipeline.
