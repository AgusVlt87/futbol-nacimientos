# Proyecto: ¿De dónde salen los futbolistas argentinos?

### Geografía del talento en el fútbol argentino

> Documento de arranque para Claude Code. Se puede usar como prompt inicial o guardar como `CLAUDE.md` en la raíz del repo. Reemplaza cualquier versión anterior del proyecto.

---

## Estado operativo

> Sección de trabajo. La especificación son las secciones 0–12; esto es el registro
> de lo verificado y lo hecho. Actualizar al cerrar cada fase.

**Fuentes verificadas** (probadas contra el endpoint real, 2026-07-30):

| Fuente | Estado | Detalle |
|---|---|---|
| Wikidata SPARQL | ✅ | 9.491 futbolistas con ciudadanía AR; **8.782 con `P19` + `P569`**. Usar `wdt:P106/wdt:P279*` para capturar subclases de `Q937857`. |
| INDEC Censo 2022 — microdatos REDATAM | ✅ | `datos.gob.ar`, dataset `censo-nacional-de-poblacion-hogares-y-viviendas-2022`, 24 zips CSV (~200 MB). Trae `DPTO`, `CODLOC`, `EDAD`, `P02` (sexo), **`P14` (provincia de nacimiento)**, `URP` (urbano/rural) → permite denominadores por **cohorte de edad**, no solo población total. |
| Georef API (`apis.datos.gob.ar/georef`) | ✅ | Geocoding oficial argentino. 24 provincias, 529 departamentos, 4.037 localidades. `/ubicacion?lat=&lon=` resuelve coordenada → depto + provincia. **Es la herramienta de normalización principal** (por coordenada, no por string). |
| Códigos geográficos INDEC 2022 | ✅ | xlsx de departamentos, gobiernos locales y localidades censales. |
| IGN — capas SIG | pendiente | Fase 2. |

**Hallazgo metodológico:** el censo 2022 pregunta **provincia de nacimiento** (`P14`).
Cruzado con `EDAD`, da un denominador *cohorte-matched por provincia de nacimiento* —
mucho mejor que "población residente en el censo X" y, además, provee el baseline
migratorio de la población general para contrastar contra el flujo de H3.

**Fases:** 0 ✅ · 1 ⏳ · 2–8 pendientes.

---

## 0. Rol y objetivo

Vas a construir **desde cero**, en fases, un pipeline de análisis reproducible que responda una pregunta: **¿los futbolistas argentinos nacen desproporcionadamente en ciertos lugares —el interior, las ciudades chicas y medianas— respecto de lo que correspondería por la población de esos lugares?**

Entregables:
1. Un **análisis estadístico riguroso**, siempre corregido por población.
2. **Visualizaciones de altísima calidad**, con foco en cartografía (mapas de Argentina).
3. Un **documento estilo paper** (IMRyD) con hallazgos claros.

Todo para **Argentina**, con **jugadores argentinos**. Trabajás en **Windows**, stack principal Python.

---

## 1. Contexto del fenómeno

El fenómeno se llama **birthplace effect** (efecto del lugar de nacimiento), también *place of early development effect*. La literatura internacional es amplia: existe una revisión sistemática solo de fútbol, y el hallazgo clásico (Côté et al., 2006) es que las ciudades **chicas y medianas** (aproximadamente 50.000–100.000 habitantes) producen desproporcionadamente más atletas de elite que las grandes urbes o las zonas rurales.

**El gap que llena este trabajo:** el fenómeno está muy estudiado en Norteamérica, Europa y Brasil, pero **no hay estudio académico serio para Argentina**. Todo lo argentino sobre "de dónde salen los jugadores" es periodismo descriptivo, sin baseline poblacional ni método estadístico. Este sería el primer análisis riguroso del birthplace effect en el fútbol argentino.

**El folklore argentino es la hipótesis, formalizada.** El relato del "crack del interior", del pueblo, del potrero —Rosario como cuna, Gualeguay (60.000 hab) con dos campeones del mundo, Zapala (32.000 hab), Santa Rosa (105.000 hab)— describe exactamente el patrón que el birthplace effect predice. La gracia del proyecto es probarlo con datos, no darlo por sentado.

---

## 2. Preguntas de investigación e hipótesis

- **H1 (tamaño de ciudad):** los futbolistas argentinos están sobrerrepresentados entre los nacidos en ciudades chicas y medianas, respecto de lo esperado por la distribución poblacional (el patrón clásico del birthplace effect).
- **H2 (mapa federal):** el interior produce más futbolistas de lo esperado por su población, en comparación con AMBA / Gran Buenos Aires. Cuantificar la producción **per cápita** por provincia y departamento.
- **H3 (flujo del talento — DIFERENCIAL DEL TRABAJO):** existe una migración sistemática entre el lugar de nacimiento y el club formador: nacen en el interior y se forman/debutan en clubes grandes del centro. Este es el ángulo propio y más valioso; ver sección 5.
- **H4 (nivel competitivo, opcional):** el efecto se intensifica con el nivel alcanzado (los que llegan a la elite o a la selección vienen aún más de ciudades chicas). Requiere una variable de "nivel".
- **Exploratorio, con reservas:** asociación entre posición y región de nacimiento (el mito de "las delanteras del norte"). Tratar como **estrictamente exploratorio**, con corrección por comparaciones múltiples; alto riesgo de encontrar patrones espurios. No presentar como hallazgo confirmatorio.

---

## 3. Decisiones a fijar antes de la ingesta masiva

> Fijar en `config.yaml` y respetar en todo el pipeline.

1. **Muestra de jugadores.** Default recomendado: **base amplia de futbolistas profesionales argentinos** como esqueleto (para tener n y baseline sólido), con **capas por nivel** (ej. debutaron en primera / jugaron en Europa top / fueron a la selección) para el análisis fino de H4, y la **selección histórica y los campeones del mundo** como caso ilustrativo con gancho narrativo.
2. **Período / cohortes.** Define qué baseline poblacional hace falta. Default: acotar a cohortes donde la población por localidad sea reconstruible con censos. Documentar el rango.
3. **Unidad geográfica.** Analizar en dos niveles: **provincia** (robusto, buena cobertura) y **departamento/localidad** (más granular, más ruido y más normalización). Reportar ambos.
4. **Métrica de "tamaño de ciudad".** Definir los cortes de población para clasificar localidades (ej. <10k, 10–50k, 50–100k, 100–500k, >500k), alineados con la literatura para poder comparar.

---

## 4. Datos

### 4.1 Jugadores

Fuente primaria: **Wikidata** vía SPARQL (gratis, estructurado, sin problema de términos de uso).

- Propiedades: `P106` (ocupación) = `Q937857` (futbolista), `P27` (nacionalidad) = `Q414` (Argentina), `P569` (fecha de nacimiento), **`P19` (lugar de nacimiento)**, `P413` (posición), `P54` (equipos), `P625` (coordenadas, sobre la entidad del lugar), `P1082` (población, sobre la entidad del lugar).
- Endpoint: `https://query.wikidata.org` (o `SPARQLWrapper` desde Python). Paginar por año de nacimiento para evitar timeouts; unir y deduplicar por `?player`.

Query de arranque (ajustar e iterar el año):

```sparql
SELECT ?player ?playerLabel ?dob ?birthplace ?birthplaceLabel ?positionLabel WHERE {
  ?player wdt:P106 wd:Q937857 ;   # ocupación: futbolista
          wdt:P27  wd:Q414 ;      # nacionalidad: Argentina
          wdt:P569 ?dob .         # fecha de nacimiento
  OPTIONAL { ?player wdt:P19  ?birthplace . }   # lugar de nacimiento
  OPTIONAL { ?player wdt:P413 ?position . }     # posición
  FILTER( YEAR(?dob) = 1990 )     # iterar por año
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
```

En un segundo paso, enriquecer cada localidad de nacimiento con sus coordenadas (`P625`) y población (`P1082`) para poder mapear y clasificar por tamaño.

Otras fuentes (evaluar disponibilidad y términos, no asumir):
- **Wikipedia – categorías de futbolistas por provincia** (útil para chequear cobertura y completar).
- **Transfermarkt**: la más completa y, clave para H3, suele traer club formador / inferiores. **Pero sus términos prohíben el scraping automatizado.** Usar solo datasets ya publicados con licencia o acceso permitido.
- Datasets de **Kaggle**, FBref/StatsBomb open data.

### 4.2 Baseline poblacional y geografía

Es el corazón metodológico: **nadie está "sobrerrepresentado" sin comparar contra cuánta gente vive en cada lugar.**

- **INDEC – Censos** (población por provincia, departamento y localidad): para el denominador. Idealmente la población de cada localidad en el **año de nacimiento** de cada cohorte, no la actual → usar censos históricos.
- **RENAPER – nacimientos a nivel departamental (2012–2024)**: `https://estadisticas.renaper.gob.ar/app_myn/` (útil para cohortes recientes).
- **IGN (Instituto Geográfico Nacional)** – capas SIG oficiales con límites provinciales y departamentales, para los mapas.

### 4.3 Advertencias de datos (críticas)

- **Sesgo de cobertura de Wikidata:** los jugadores notables están sobrerrepresentados y los del interior o menos famosos pueden faltar. Esto puede inflar o atenuar el efecto; discutirlo como limitación central.
- **Normalización de localidades:** los nombres de lugares argentinos en Wikidata vienen inconsistentes (a veces provincia, a veces ciudad, homónimos). Hay un trabajo real de geocoding y desambiguación.
- **Baseline histórico:** la población de cada localidad cambia con el tiempo; usar el censo más cercano al año de nacimiento de la cohorte.
- **Múltiples nacionalidades / lugares:** definir y documentar la regla de desambiguación.

---

## 5. La limitación central: nacer ≠ formarse

Es lo más importante de tener claro, y hay que declararlo con honestidad en el paper. La literatura reciente muestra que el lugar de nacimiento **por sí solo** es un predictor flojo; lo que pesa es la **transición** entre dónde se nace y dónde se desarrolla el jugador. Un estudio halló que quienes migraron de su lugar de nacimiento a otro lugar de crecimiento deportivo tenían ~38% más de chances de debutar profesionalmente.

Wikidata te da el lugar de **nacimiento**, no el de **formación**. Dos caminos:

- **Versión base (factible ya):** análisis del lugar de nacimiento vs población. Es la metodología clásica del birthplace effect, totalmente válida y publicable. Es el piso del proyecto.
- **Versión fuerte (el diferencial, H3):** conseguir el **club formador / lugar de desarrollo** de cada jugador (de Transfermarkt con licencia, o parseando el texto de Wikipedia: "surgió de las inferiores de X", "debutó en Y") y analizar el **flujo nacimiento → club formador**. En Argentina esto es parte del fenómeno, no solo ruido: nacen en el interior y "se van con la valija" a los clubes grandes del centro. Si se consigue este dato, el trabajo pasa de replicación correcta a aporte propio.

Diseñar el pipeline para que la versión base funcione sola, y la capa de formación sea un módulo opcional que la potencia.

---

## 6. Metodología estadística

- **Test principal:** chi-cuadrado de bondad de ajuste, observado (nacimientos de jugadores por unidad geográfica / por tramo de tamaño de ciudad) vs esperado (distribución poblacional real). No usar distribución uniforme como único baseline.
- **Producción per cápita:** tasa de futbolistas por cada 100.000 habitantes, por provincia, departamento y tramo de tamaño de ciudad. Es la métrica que corrige el efecto de que "donde vive más gente hay más de todo".
- **Tamaño de efecto e intervalos:** siempre. Odds ratios / risk ratios por tramo de tamaño con IC 95%; Cramér's V para la asociación global.
- **Regresión:** relación entre tamaño (o densidad) de la localidad y tasa de producción de jugadores.
- **Subgrupos:** por nivel competitivo (H4), por década de nacimiento, por posición (exploratorio, con corrección por comparaciones múltiples).
- **Para H3:** matrices y análisis de flujo origen→destino.

Regla transversal: **ningún hallazgo se apoya solo en un p-valor.** Reportar estadístico, gl, p, tamaño de efecto e IC.

---

## 7. Estructura del repositorio y fases

```
futbol-geografia-arg/
├── data/
│   ├── raw/          # crudo, nunca se edita
│   ├── interim/
│   └── processed/
├── src/
│   ├── ingest/       # Wikidata, población (INDEC/RENAPER), geografía (IGN)
│   ├── clean/        # geocoding, normalización de localidades, dedup
│   ├── analysis/     # tests, tasas per cápita, flujos
│   └── viz/          # mapas y figuras
├── notebooks/
├── outputs/
│   ├── figures/
│   └── tables/
├── reports/          # el paper
├── tests/
├── config.yaml
├── requirements.txt
└── README.md
```

**Fases (commit al cerrar cada una):**

- **Fase 0 – Setup:** repo, entorno, `config.yaml` con las decisiones de la sección 3, `requirements.txt`.
- **Fase 1 – Ingesta jugadores:** SPARQL paginado por año → `data/raw/`. Guardar la **fecha del snapshot** de Wikidata.
- **Fase 2 – Ingesta población y geografía:** censos INDEC, RENAPER, shapefiles del IGN. Guardar crudo y documentar cobertura.
- **Fase 3 – Limpieza y geocoding:** normalizar localidades, asignar coordenadas y población, deduplicar, QA de faltantes, regla de desambiguación.
- **Fase 4 – EDA:** distribuciones, faltantes, chequeos de sanidad, primeros mapas exploratorios.
- **Fase 5 – Análisis:** todo lo de la sección 6, resultados exportados a `outputs/tables/`.
- **Fase 6 – Visualizaciones:** las de la sección 8 → `outputs/figures/`.
- **Fase 7 – (opcional) Módulo flujo/formación:** H3, si se consiguió el dato de club formador.
- **Fase 8 – Paper:** redacción según sección 9, consumiendo tablas y figuras.

---

## 8. Visualizaciones (que sean excelentes)

La geografía se presta a mapas potentes; que sean el centro del apartado visual. Todas exportables en vectorial (SVG/PDF) para el paper, más versiones interactivas para explorar.

- **Mapa coroplético de Argentina** por provincia y por departamento: cantidad absoluta de futbolistas nacidos.
- **Mapa coroplético per cápita:** futbolistas por 100.000 habitantes. Este es el mapa clave, el que corrige por población y muestra el verdadero patrón.
- **Cartograma** (área proporcional a la producción de jugadores) para contrastar con el mapa geográfico real.
- **Scatter tamaño/densidad de ciudad vs tasa de producción**, con la curva del birthplace effect.
- **Mapa de flujos** nacimiento → club formador (para H3), tipo líneas origen-destino.
- Barras de tasa per cápita por tramo de tamaño de ciudad, con IC.

Pautas: una **paleta y una plantilla únicas** en todo; `geopandas` + `matplotlib` para figuras de paper; `plotly`/`folium` para lo interactivo. Escalas, unidades, n y fuente siempre rotulados. Cuidar proyección cartográfica y clasificación de rangos (quantiles vs cortes naturales). Sin *chartjunk*.

---

## 9. Documento final (estilo paper, con hallazgos)

Formato IMRyD:
1. **Introducción:** el birthplace effect, el estado del arte internacional, el gap argentino, las hipótesis.
2. **Métodos:** fuentes, muestra, unidades geográficas, definición del baseline poblacional, tests. Declarar la limitación nacer ≠ formarse.
3. **Resultados:** los mapas y tablas, hipótesis por hipótesis. Sección de **hallazgos** destacados y claros.
4. **Discusión:** interpretación, comparación con la literatura, **limitaciones** (cobertura de Wikidata, baseline histórico, lugar de formación), implicancias para la detección de talento.

Lecturas de fondo (verificar y citar en el paper, no copiar):
- Revisión sistemática del birthplace effect en fútbol: https://pmc.ncbi.nlm.nih.gov/articles/PMC11571467/
- "Place Matters" — nacimiento vs lugar de desarrollo: https://www.mdpi.com/2075-4663/12/4/99
- The geography of talent development: https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.1031227/full

---

## 10. Stack técnico

- **Python 3.11+** en Windows.
- Datos: `pandas`, `numpy`.
- Consulta: `SPARQLWrapper` o `requests`.
- Geo: `geopandas`, `shapely`; geocoding con un servicio a definir.
- Estadística: `scipy.stats`, `statsmodels`.
- Viz: `matplotlib` (+ `geopandas` plotting) para figuras de paper; `plotly` / `folium` para interactivo.
- `jupyter` para EDA.
- Reproducibilidad: versiones fijadas en `requirements.txt`, seeds donde aplique.

---

## 11. Reglas de trabajo (para Claude Code)

- **No inventar datos.** Si una fuente no está disponible o falta cobertura, documentarlo como gap; nunca rellenar con valores plausibles.
- **Reproducibilidad:** `data/raw/` intocable; toda transformación en código; snapshot de Wikidata fechado.
- **Documentar supuestos** (cohortes, cortes de tamaño de ciudad, censo usado como baseline, regla de desambiguación) en código y README.
- **Tests** para las funciones críticas (normalización de localidades, asignación de tramo de tamaño, cálculo de tasas per cápita).
- **No scrapear fuentes que lo prohíben** (Transfermarkt) sin autorización.
- **Estadística honesta:** siempre tamaño de efecto e IC; baseline poblacional real, no uniforme; corrección por comparaciones múltiples en los cruces exploratorios.
- **Commits incrementales** por fase.

---

## 12. Riesgos conocidos

- Cobertura incompleta y sesgada de Wikidata → sesgo de selección en la muestra (jugadores notables sobrerrepresentados).
- Lugar de formación no disponible en Wikidata → H3 depende de conseguir el dato por otra vía.
- Baseline poblacional histórico difícil de reconstruir hacia atrás por localidad.
- Normalización de nombres de localidades: trabajo considerable y fuente de error.
- Términos de uso de Transfermarkt.
- Cruces exploratorios (posición × región): riesgo alto de hallazgos espurios si no se corrige.