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

**El básquet argentino tiene el efecto que el fútbol no tiene.** Corrido el mismo
pipeline sobre otros deportes —misma ventana, mismo denominador, misma cadena de
geocoding, lo único que cambia es el deporte—, en el contraste que define el
*birthplace effect* (ciudades de 50–100k contra grandes aglomerados) el **básquet
da RR 1,95 (IC 95% 1,38–2,76)** y el **fútbol 0,72 (0,64–0,82)**, con intervalos
que no se tocan. El básquet dibuja la U invertida de manual, con el pico
exactamente donde Côté et al. (2006) lo sitúan; el rugby está aún más concentrado
que el fútbol (RR 0,08). Ningún artefacto de medición compartido —el registro de
nacimientos, la imputación del denominador, la cobertura de Wikipedia, el nivel
socioeconómico— puede producir mapas opuestos para deportes distintos medidos con
el mismo instrumento.

**El *birthplace effect* clásico no aparece en el fútbol: aparece invertido.** La
tasa va de 12,7 por 100.000 nacidos en localidades de menos de 10.000 habitantes
a 28,4 en aglomerados de más de 500.000 (RR 0,45; IC 95% 0,41–0,50). No hay pico
en las ciudades medianas. Pero **es un escalón, no un gradiente**: los nueve
deciles de tamaño por debajo de ~10.000 habitantes no tienen tendencia, y el
tamaño de la ciudad explica el 1% de la variación entre ciudades
(pseudo-R² = 0,011).

**La versión fuerte del artefacto de las maternidades queda refutada; la débil, acotada.** Era la objeción de fondo
contra cualquier estudio de lugar de nacimiento —el parto ocurre donde hay
maternidad, así que los pueblos se vacían y las cabeceras se llenan— y era la
limitación central declarada del trabajo. Se probó: la serie del DEIS titulada
«nacimientos **ocurridos**» es idéntica a la tabulación por **residencia de la
madre** en las 432 celdas provincia×año en que se solapan (diferencia máxima:
cero), y hay 76 futbolistas cuyo `P19` apunta a localidades de menos de 2.000
habitantes, en 63 localidades distintas, donde ninguna maternidad puede existir.
Emiliano Sala figura nacido en Cululú, Santa Fe: 106 habitantes.
Eso descarta que el `P19` sea *sistemáticamente* el lugar del parto, pero no que
lo sea en una fracción de los casos: la cota superior de mala atribución es del
44,5% del déficit del interior.

**Al pibe del interior le cuesta mucho más entrar, pero el que entra rinde más.**
Entre los futbolistas que ya llegaron a un juvenil de la selección, los nacidos
fuera de un gran aglomerado llegan a la Mayor en el 41,1% de los casos contra el
28,1% de los nacidos en una ciudad grande (OR 1,78; IC 95% 1,09–2,93; p = 0,027;
igual al controlar por cohorte). **No usa denominador poblacional**, así que no lo
afectan ni el reparto estimado de nacimientos ni la cobertura de Wikidata. **Pero
todo el contraste lo aporta un solo estrato**: sin el tramo de 10.000 a 50.000
habitantes —25 casos— el OR cae a 1,42 y el intervalo cruza el 1. Y condiciona en
un *collider*, así que es consistente con la historia del filtro de acceso pero
también con cualquier otra selección diferencial.

**Lo que mejor predice dónde nace un futbolista no es el tamaño de la ciudad ni
la cercanía a un club: es la pobreza.** Agregados al modelo el NBI departamental
del censo y la distancia al club formador más cercano, el **NBI explica siete
veces más variación que el tamaño** (pseudo-R² 0,071 contra 0,010) y cada punto
porcentual de NBI baja la producción un 15%. La distancia al club —fuerte por sí
sola, RR 0,854— **se apaga por completo al entrar la pobreza** (RR 0,987;
p = 0,75): era un proxy. El mapa de producción de futbolistas se parece más al
mapa de la pobreza estructural argentina que al de la infraestructura formativa.

**Y el mapa departamental resume mal el fenómeno.** Solo el 17% de la variación
residual separa a un departamento de otro; el 83% restante ocurre entre ciudades
del mismo departamento. La unidad a la que el fenómeno pasa es más chica que la
que el trabajo dibuja.

**La producción se concentra en el corredor pampeano y en el AMBA, en ese orden.**
La región pampeana produce 34,5 futbolistas cada 100.000 nacidos y el AMBA 28,3,
contra 8,2 del NOA. Por provincia, CABA produce 2,6 veces lo que le tocaría por
sus nacimientos y Santa Fe 2,3; Salta 0,23. Las cunas son Rafaela (98 cada 100.000
nacidos), Gran Santa Fe (73) y Gran Rosario (58).

**Entre los que llegaron lejos, la formación está mucho más concentrada que el
nacimiento** — con la advertencia de que esa submuestra está seleccionada por el
desenlace y describe a la elite, no a la población de futbolistas. El 47,1% se
forma fuera de su provincia de nacimiento; el NEA retiene al 8,6% de los suyos y
el AMBA al 90,8%. Hay dos modelos de club formador: Rosario Central forma 94
jugadores a 0 km de mediana y con el 18% venido de otra provincia; Boca forma 143
a 277 km y con el 77% de afuera.

**El paper completo es [paper/paper.pdf](paper/paper.pdf)** — 28 páginas, con las
figuras que sostienen el argumento intercaladas en el texto. Se compila con
`paper/compilar.ps1` desde [paper/paper.tex](paper/paper.tex). La misma cosa en
markdown está en [reports/paper.md](reports/paper.md), y las 33 figuras sueltas en
[outputs/figures/](outputs/figures/).

Las tablas de las dos versiones **se generan desde `outputs/tables/`**, no se
escriben a mano: `python -m src.report.sync_tablas_paper` las reescribe y
`--check` falla si quedaron desfasadas del pipeline. Hay un test que lo verifica.

---

## Qué NO sostiene este trabajo

Vale la pena leerlo antes que los resultados.

- **Nacer no es criarse.** El lugar de nacimiento no es el de crianza, y la
  literatura reciente señala a la transición entre los dos como lo que más pesa.
  El pipeline no tiene lugar de crianza en ninguna parte.
- **Los controles son parciales.** Hay dos covariables —NBI departamental y
  distancia al club formador más cercano— y faltan las demás: densidad de ligas
  locales, existencia de pensión, y la red formativa vigente en la época de cada
  cohorte. Las asociaciones son observacionales.
- **La tasa de error del `P19` está medida** —133 casos verificados a mano contra
  BDFA, una fuente independiente de Wikipedia— y da **5,9 % de error, no
  diferencial**: 6,1 % entre los ubicados en metrópolis y 5,7 % entre los del
  resto (OR 1,09; p = 1,00). Un error uniforme atenúa el efecto en vez de
  fabricarlo: el RR corregido pasa de 0,599 a **0,547** (IC 0,397–0,682). Falta
  completar la muestra hasta los 300 previstos para cerrar los intervalos. Lo que
  sí quedó mal parado es el club formador de H3: Wikidata **no tiene ninguno
  cargado en el 52 %** de los casos, y entre los que sí, difiere del real en el
  11,8 %.
- **H3 (formación) está seleccionada por el desenlace.** La cobertura del club
  formador va del 99,2% entre jugadores de selección al 12,7% en el resto. Sus
  números son órdenes de magnitud, no estimaciones poblacionales, y ninguna otra
  conclusión se apoya en ellos.
- **Solo fútbol masculino** en el análisis principal. El femenino entra como
  contraste (n = 213) y resulta indistinguible del masculino.

La lista completa, con las doce limitaciones y su alcance, está en el §4.3 del
paper.

---

## Cómo se revisó

El repo lo construyó un modelo y después se revisó tres veces, cada una con su
documento:

| Documento | Qué es |
|---|---|
| [docs/roast.md](docs/roast.md) | Segunda pasada: revisión hostil del diseño |
| [docs/re-analisis.md](docs/re-analisis.md) | Tercera pasada: diagnóstico independiente y plan de expansión |
| [docs/impacto-lote-1.md](docs/impacto-lote-1.md) | Reparación de la geografía departamental |
| [docs/impacto-lote-2.md](docs/impacto-lote-2.md) | Qué criterio usan las dos puntas del cociente |
| [docs/impacto-lote-3.md](docs/impacto-lote-3.md) | Test placebo y robustez |
| [docs/hallazgos-pendientes.md](docs/hallazgos-pendientes.md) | Lo que quedó abierto |

Tres errores que encontró ese proceso y que vale la pena conocer si se reusa el
código:

1. **Los códigos de departamento del INDEC no son estables entre censos.** 44 de
   532 cambiaron entre 1991 y 2022. Un `merge(how="left")` descartaba en silencio
   los partidos disueltos en 1994: 1.049.301 nacimientos, el 70% del Gran Buenos
   Aires. Los totales provinciales cuadraban, por eso era invisible.
2. **La lista de los 24 partidos del GBA estaba corrida un lugar.** Doce de
   veinticuatro códigos apuntaban a otro partido. Ahora se declaran por nombre y
   se resuelven contra el padrón oficial del INDEC.
3. **El título de un recurso oficial no es su metodología.** La serie del DEIS
   dice «ocurridos» y es por residencia.

Los tres compartían causa: nada verificaba los datos contra el padrón, y nada
verificaba que las transformaciones conservaran la masa. Ahora
`padron_departamentos.verificar_conservacion` corta el pipeline si una
transformación pierde nacimientos, y compara **grupo por grupo**, no totales
—los tres errores conservaban el total nacional—.

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
python -m src.ingest.wikipedia_fichas    # equipo_debut de las fichas (H3)
python -m src.clean.build_club_debut
python -m src.ingest.wikidata_clubs_wiki # sede de los clubes que solo salen de fichas
python -m src.clean.build_careers
python -m src.clean.geocode_clubs

# Fases 5 a 9 — análisis y figuras
python -m src.analysis.run_all
python -m src.analysis.run_levels_and_flow
python -m src.analysis.run_futbol
python -m src.analysis.run_seleccion      # selección: Mayor, juveniles y conversión
python -m src.analysis.run_edad_relativa  # control positivo
python -m src.analysis.run_sesgo_granularidad
python -m src.clean.build_covariables     # NBI y distancia al club
python -m src.analysis.run_modelo         # covariables y varianza
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
| **Club de debut** (`equipo_debut` de la ficha), el 41,8% de la cobertura de H3 | [API de acción de Wikimedia](https://www.mediawiki.org/wiki/API:Main_page) sobre es/en.wikipedia | CC BY-SA 4.0 |
| **Nacidos vivos por jurisdicción y año, 1914–2024** (el denominador) | [DEIS](https://datos.gob.ar/dataset/serie-historica-de-nacimientos-ocurridos-en-argentina-por-jurisdiccion) | Datos abiertos |
| Nacimientos por departamento 2012–2022 (validación del denominador) | [RENAPER](https://datos.gob.ar/dataset/nacimientos-en-argentina) | Datos abiertos |
| Población por departamento, localidad, edad, sexo y provincia de nacimiento | [INDEC — Censo 2022, microdatos REDATAM](https://datos.gob.ar/dataset/censo-nacional-de-poblacion-hogares-y-viviendas-2022) | Datos abiertos |
| Códigos geográficos oficiales | [INDEC — Códigos geográficos 2022](https://datos.gob.ar/dataset/codigos-geograficos-del-indec-2022) | Datos abiertos |
| Normalización de localidades → departamento/provincia | [API Georef](https://apis.datos.gob.ar/georef/api/) | Datos abiertos |
| Límites provinciales y departamentales (mapas) | [IGN](https://www.ign.gob.ar/) | Datos abiertos |

| **Nacidos vivos por residencia de la madre, 2005–2022** (la serie contrafáctica) | [DEIS](https://datos.gob.ar/dataset/nacidos-vivos-registrados-por-jurisdiccion-de-residencia-de-la-madre-republica-argentina) | CC-BY 4.0 |

**Fuentes que NO se usan, y dónde vive la restricción de cada una** —son dos
documentos distintos y no dicen lo mismo, conviene no confundirlos:

- **Transfermarkt**: su `robots.txt` **sí permite** las rutas de ficha de jugador
  (`Allow: /`; solo excluye `/ceapi`, `/quickselect`, `/jumplist` y
  `/navigation/getSubNavigation`). La prohibición está en los **términos de uso
  §11**: «el usuario no tiene permitido acceder o copiar el contenido digital
  utilizando bots, spiders, screen scraping u otros procesos automatizados».
- **BDFA** (`bdfa.com.ar`): acá sí es el `robots.txt`, y es explícito: bloquea
  `ClaudeBot`, `curl`, `wget` y `Python-requests` por nombre, más los endpoints
  `/lista_jugadores.asp?*` y `/api_jugadores_ajax.asp`. No se evadió cambiando el
  `User-Agent`.
- **AFA**: su `robots.txt` permite el rastreo (solo excluye `/cache/`), pero el
  sitio no publica fichas con lugar de nacimiento.

Por eso la validación del `P19` se hizo **a mano**, leyendo BDFA en un navegador:
133 casos, 94,1% de acuerdo, error no diferencial. Y por eso el club de debut se
completó desde **Wikipedia** y no desde Transfermarkt, que lo tiene mejor: la API
de Wikimedia está publicada para uso programático y su política de etiqueta pide
un `User-Agent` identificable con contacto, lotes en vez de pedidos sueltos y
pausa entre llamadas — que es lo que hace `src/ingest/wikipedia_fichas.py`. Los
5.511 jugadores salieron en **218 pedidos HTTP**.

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
- **Unidades.** Provincia, **departamento** (nivel principal, 515 unidades) y
  localidad censal (define el tamaño de ciudad).
- **Tamaño de ciudad.** Dos esquemas de corte: el del diseño
  (<10k / 10–50k / 50–100k / 100–500k / >500k) y el de Côté et al. (2006) para
  comparar con la literatura. Se reportan los dos: si el efecto aparece con uno
  solo, es un artefacto de la partición.
- **Denominador: nacidos vivos, no población censada.** Por provincia es dato
  real (DEIS, por año). Por departamento y ciudad se reparte el total provincial
  real según la población del censo más cercano al año de nacimiento. Ese reparto
  es el principal supuesto de la cadena —el otro es el reparto de los 44 partidos
  cuyos códigos cambiaron entre censos, en
  [data/reference/crosswalk_departamentos.csv](data/reference/crosswalk_departamentos.csv)—
  y se valida contra los nacimientos departamentales reales del RENAPER (error
  mediano 9%). Se reportan además cinco denominadores alternativos y el orden no
  cambia.
- **Códigos geográficos: nunca a mano.** Todo código de departamento se resuelve
  contra el padrón oficial del INDEC, y toda transformación verifica que conserve
  la masa, grupo por grupo. Los dos bugs más caros del proyecto salieron de no
  hacerlo.
- **Normalización.** Por **coordenada** (`P625`) contra Georef, no por matching de
  strings. Lo que queda ambiguo se marca `unresolved`; **no se adivina.**

---

## Limitaciones declaradas

La lista completa y su alcance están en el §4.3 del paper (doce puntos). El
resumen honesto está arriba, en **Qué NO sostiene este trabajo**. Las tres que más
condicionan la lectura:

1. **Nacer ≠ criarse.** Es la limitación conceptual de fondo y no se resuelve con
   estos datos. Lo que **sí** quedó acotado es su versión mecánica —el artefacto
   de las maternidades—: las dos puntas del cociente registran residencia, no
   parto (§2.1.1 del paper). Queda su versión débil, con techo de 44,5% calculado
   del peor modo posible.
2. **El reparto sub-provincial es un supuesto con sesgo direccional.** A nivel
   provincia el denominador es dato real; por debajo es estimación, con un error
   del +17% en el decil de departamentos más chicos que empuja en la misma
   dirección que el hallazgo. El placebo lo neutraliza como amenaza a la
   identificación —afecta igual a los cinco deportes— pero sigue midiendo mal la
   magnitud.
3. **Sin controles.** Ninguna covariable más allá del tamaño de la ciudad.

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
- Los datos derivados no se versionan: se regeneran corriendo el pipeline. Como
  `outputs/` está en `.gitignore`, **`git diff outputs/` siempre sale vacío y no
  sirve para verificar nada**: cada corrida deja un `outputs/tables/_run.json` con
  el commit, el hash del `config.yaml` y el recuento de filas de cada tabla.
- `outputs/_baseline_3f07dba/` conserva las tablas de antes de reparar la
  geografía, para que las cifras de `docs/impacto-lote-1.md` sean auditables sin
  volver a correr el pipeline viejo.
