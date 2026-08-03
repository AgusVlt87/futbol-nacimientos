# ¿De dónde salen los futbolistas argentinos?

**Geografía del talento en el fútbol argentino: un test del *birthplace effect*.**

¿Los futbolistas argentinos nacen desproporcionadamente en el interior y en
ciudades chicas y medianas, respecto de lo que correspondería por la población de
esos lugares? Este repo contiene el pipeline reproducible que responde esa
pregunta con datos, no con folklore.

La especificación completa del estudio está en [CLAUDE.md](CLAUDE.md); las
decisiones de diseño, en [config.yaml](config.yaml); **los resultados, en
[reports/paper.md](reports/paper.md)**.

---

## Qué encontramos

Sobre 5.511 futbolistas argentinos nacidos entre 1975 y 2008, con los **nacidos
vivos** de cada cohorte como denominador. La tasa se lee directo: de cada 100.000
bebés nacidos en un lugar, cuántos llegaron a futbolistas profesionales.

**Al pibe del interior le cuesta mucho más entrar, pero el que entra rinde más.**
Entre los futbolistas que ya llegaron a un juvenil de la selección, los nacidos
fuera de un gran aglomerado llegan a la Mayor en el 41,9% de los casos contra el
28,1% de los nacidos en una ciudad grande (OR 1,85; IC 95% 1,14–2,98; p = 0,013;
igual al controlar por cohorte). **Es el resultado más sólido del trabajo porque
no usa denominador poblacional**: no lo afectan ni el reparto estimado de
nacimientos, ni el hecho de que el parto se registre en la ciudad cabecera, ni la
cobertura de Wikidata.

**El *birthplace effect* clásico no aparece: aparece invertido.** La tasa va de
12,9 por 100.000 nacidos en localidades de menos de 10.000 habitantes a 30,5 en
aglomerados de más de 500.000 (RR 0,42; IC 95% 0,38–0,47). No hay pico en las
ciudades medianas. Pero **es un escalón, no un gradiente**: los nueve deciles de
tamaño por debajo de ~10.000 habitantes no tienen tendencia, y el tamaño de la
ciudad explica el 1% de la variación entre ciudades (pseudo-R² = 0,011).

**La producción se concentra en el AMBA y el corredor pampeano.** CABA produce
2,6 veces lo que le tocaría por sus nacimientos y Santa Fe 2,3; Salta 0,23. Las
cunas son Rafaela (98 cada 100.000 nacidos), Gran Santa Fe (73) y Gran Rosario
(58).

**La formación está mucho más concentrada que el nacimiento.** El 47,1% se forma
fuera de su provincia de nacimiento contra el 13,8% de la población general
(OR 5,58; IC 95% 5,10–6,10). Quien nace en un gran aglomerado se forma a 7 km de
mediana; quien nace en cualquier otro lado cambia de departamento en el 86–98% de
los casos. El NEA retiene al 8,3% de los suyos; el AMBA, al 91,6%. **Diez clubes
concentran el 48% de toda la formación del país.**

**Hay dos modelos de club formador.** Rosario Central forma 94 jugadores a 0 km
de mediana de su lugar de nacimiento y con el 18% venido de otra provincia;
Boca forma 143 a 277 km y con el 77% de afuera.

**No lo fabrica la cobertura de Wikidata.** El patrón se sostiene en los cuatro
niveles competitivos, incluida la selección mayor, donde la cobertura del corpus
es prácticamente censal. Eso acota la amenaza de cobertura; **no** acota la otra
—que el parto se registre en la ciudad cabecera—, que sigue abierta y es la
limitación central del trabajo.

**El paper completo es [paper/paper.pdf](paper/paper.pdf)** — 18 páginas, con las
16 figuras que sostienen el argumento intercaladas en el texto. Se compila con
`paper/compilar.ps1` desde la fuente [paper/paper.tex](paper/paper.tex).

También está la versión en markdown ([reports/paper.md](reports/paper.md)), las 26
figuras sueltas en [outputs/figures/](outputs/figures/) y la revisión crítica del
propio diseño en [docs/roast.md](docs/roast.md).

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
# Fase 1 — jugadores, lugares y carreras (Wikidata)
python -m src.ingest.wikidata_players
python -m src.ingest.wikidata_places
python -m src.ingest.wikidata_careers
python -m src.ingest.wikidata_clubs

# Fase 2 — población, nacimientos y geografía
python -m src.ingest.indec_census
python -m src.ingest.nacimientos
python -m src.ingest.georef
python -m src.ingest.ign_boundaries

# Fase 3 — limpieza, denominadores y geocoding (este orden importa:
# el crosswalk necesita las localidades del censo ya construidas)
python -m src.clean.build_players
python -m src.clean.build_population
python -m src.clean.crosswalk_localidades
python -m src.clean.geocode_places
python -m src.clean.build_denominators
python -m src.clean.build_analysis_dataset
python -m src.clean.build_careers
python -m src.clean.geocode_clubs

# Fases 5 a 9 — análisis y figuras
python -m src.analysis.run_all
python -m src.analysis.run_levels_and_flow
python -m src.analysis.run_futbol
python -m src.analysis.run_seleccion      # selección: Mayor, juveniles y conversión
python -m src.analysis.run_criterio_denominador   # qué criterio usan las dos puntas del cociente
python -m src.ingest.wikidata_placebo     # deportistas de otros deportes
python -m src.analysis.run_placebo        # test placebo: ¿la geografía es del fútbol?
python -m src.viz.make_figures            # figuras 1 a 13
python -m src.viz.make_figures_extra      # figuras 14 a 28
```

Cada script es idempotente: si el crudo ya está descargado no lo vuelve a pedir
(salvo `--force`).

---

## Fuentes de datos

| Qué | Fuente | Licencia / acceso |
|---|---|---|
| Jugadores, lugar de nacimiento, posición, clubes | [Wikidata](https://query.wikidata.org/) vía SPARQL | CC0 |
| **Nacidos vivos por jurisdicción y año, 1914–2024** (el denominador) | [DEIS](https://datos.gob.ar/dataset/serie-historica-de-nacimientos-ocurridos-en-argentina-por-jurisdiccion) | Datos abiertos |
| Nacimientos por departamento 2012–2022 (validación del denominador) | [RENAPER](https://datos.gob.ar/dataset/nacimientos-en-argentina) | Datos abiertos |
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
- **Cohortes.** Nacidos **1975–2008**. El límite de atrás lo puso un hueco de la
  fuente: el DEIS no publica 1971–1974, y arrancar en 1970 dejaba a esa cohorte
  con el denominador de un solo año. El de adelante es la carrera: quien nació en
  2008 tenía 14 años en 2022. La censura se cuantifica cohorte por cohorte.
- **Unidades.** Provincia, **departamento** (nivel principal, 529 unidades) y
  localidad censal (define el tamaño de ciudad).
- **Tamaño de ciudad.** Dos esquemas de corte: el del diseño
  (<10k / 10–50k / 50–100k / 100–500k / >500k) y el de Côté et al. (2006) para
  comparar con la literatura. Se reportan los dos: si el efecto aparece con uno
  solo, es un artefacto de la partición.
- **Denominador: nacidos vivos, no población censada.** Por provincia es dato
  real (DEIS, por año). Por departamento y ciudad se reparte el total provincial
  real según la población del censo más cercano al año de nacimiento; ese reparto
  es el único supuesto de la cadena y se valida contra los nacimientos
  departamentales reales del RENAPER (r = 0,993, error mediano 9%). Se reportan
  además cinco denominadores alternativos y el orden no cambia.
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
3. **El reparto intraprovincial es un supuesto.** A nivel provincia el
   denominador es dato real; a nivel departamento y ciudad es una estimación,
   validada (r = 0,993, error mediano 9%) pero estimación al fin.
4. **Baseline temporal del tamaño de ciudad.** El tamaño de la localidad se mide
   en el Censo 2022, no en la infancia del jugador. **No se interpola población.**
5. **Censura a derecha.** Las cohortes 2003–2008 están incompletas por
   construcción: quien nació en 2008 tenía 14 años en 2022. Se incluyen, se
   marcan en `diagnostico_censura_cohortes.csv` y el análisis se repite sin ellas.
6. **Unidad geográfica en metrópolis fragmentadas.** Las tasas por departamento
   se inflan en el núcleo de los aglomerados que cruzan límites administrativos.
   Por eso el análisis de tamaño de ciudad usa aglomerados y no departamentos.

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
