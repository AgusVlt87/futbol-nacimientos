# ¿De dónde salen los futbolistas argentinos?

### Geografía del nacimiento y de la formación en el fútbol argentino, cohortes 1975–2008

*Análisis reproducible sobre Wikidata, la serie histórica de nacidos vivos del
DEIS y el Censo Nacional 2022 del INDEC. Snapshot de Wikidata: 30 de julio de 2026.*

---

## Resumen

Se analiza el lugar de nacimiento de 5.511 futbolistas profesionales argentinos
nacidos entre 1975 y 2008, contra el número de **nacidos vivos** de cada cohorte
en cada lugar. La tasa se lee directo: de cada 100.000 bebés nacidos en un lugar,
cuántos llegaron a futbolistas profesionales.

**Primero: el *birthplace effect* clásico no aparece en Argentina, y lo que
aparece es su inverso.** La producción es de 12,7 futbolistas cada 100.000
nacidos en localidades de menos de 10.000 habitantes contra 28,4 en aglomerados
de más de 500.000 (RR 0,45; IC 95% 0,41–0,50). El término cuadrático de un modelo
binomial negativo no aporta ajuste: no hay pico en las ciudades medianas. Pero el
efecto **no es un gradiente sino un escalón**: por decil de tamaño, los nueve
deciles por debajo de ~10.000 habitantes no muestran tendencia alguna, y el
tamaño de la ciudad explica apenas el 1% de la variación entre ciudades
(pseudo-R² = 0,011).

**Segundo, y es lo que vuelve interpretable a todo lo demás: el artefacto de las
maternidades no está operando.** La objeción de fondo contra cualquier estudio de
lugar de nacimiento es que el parto ocurre donde hay maternidad, de modo que los
pueblos se vacían y las cabeceras se llenan. Se probó, y las dos puntas del
cociente registran **residencia**, no parto: la serie del DEIS titulada
«nacimientos ocurridos» es idéntica a la tabulación por residencia de la madre en
las 432 celdas provincia×año en que se solapan (diferencia máxima: cero), y hay 76
futbolistas cuyo `P19` apunta a localidades de menos de 2.000 habitantes, en 63
localidades distintas, donde ninguna maternidad puede existir (**Figura 27**).

**Tercero, y es el resultado más robusto del trabajo: entre los que ya llegaron a
un juvenil de la selección, los nacidos fuera de un gran aglomerado llegan a la
Mayor con más frecuencia** —41,9% contra 28,1%; OR 1,85 (IC 95% 1,14–2,98),
p = 0,013, y 1,85 ajustando por cohorte de nacimiento. Este análisis **no usa
denominador poblacional**, de modo que no lo afectan ni el sesgo de imputación de
nacimientos ni la cobertura de Wikidata. Dicho en criollo: al pibe del interior le
cuesta mucho más entrar, pero el que entra rinde más.

**Cuarto: la producción se concentra en el corredor pampeano y en el AMBA, en ese
orden.** La región pampeana produce 34,5 futbolistas cada 100.000 nacidos y el
AMBA 28,3, contra 8,2 del NOA y 9,6 del NEA. Por provincia, CABA produce 2,6 veces
lo que le correspondería por sus nacimientos y Santa Fe 2,3; Salta, Catamarca y
San Juan producen menos de un cuarto.

**Quinto: la formación está mucho más concentrada que el nacimiento.** El 47,1%
de los futbolistas se forma en una provincia distinta de aquella en la que nació,
contra el 13,8% de la población general que reside fuera de su provincia de
nacimiento (OR 5,58; IC 95% 5,10–6,10). El NEA retiene al 8,6% de los futbolistas
que nacen en su territorio; el AMBA, al 90,8%. Diez clubes concentran el 48% de
toda la formación del país.

El patrón se sostiene entre los jugadores de la selección mayor, donde la
cobertura de Wikidata es prácticamente censal: no lo fabrica el corpus.

---

## 1. Introducción

### 1.1 El *birthplace effect*

El *birthplace effect* —también llamado *place of early development effect*— es
uno de los hallazgos más replicados en la investigación sobre desarrollo
deportivo. Côté y colegas (2006) documentaron que las ciudades chicas y medianas
producen desproporcionadamente más atletas de elite que las grandes urbes y que
las zonas rurales, con un óptimo típicamente situado entre los 50.000 y los
100.000 habitantes. La explicación habitual combina espacio físico para el juego
libre, densidad social suficiente para sostener competencia organizada sin
generar barreras de acceso, y relaciones entrenador-jugador más estables.

### 1.2 El caso argentino

Argentina exporta futbolistas en volumen y tiene un relato nacional muy
establecido sobre su origen. El «crack del interior», el potrero, el pueblo chico
que da campeones del mundo —Gualeguay, 44.000 habitantes, dos— describe con
precisión el patrón que el *birthplace effect* predice.

Ese relato nunca fue puesto a prueba. Lo que existe es periodismo descriptivo:
listas de jugadores por provincia, sin denominador y por lo tanto sin capacidad
de distinguir «produce muchos» de «nace mucha gente». Este trabajo es, hasta
donde alcanza nuestra búsqueda, el primer análisis estadístico del *birthplace
effect* en el fútbol argentino.

### 1.3 Hipótesis

- **H1.** Los futbolistas están sobrerrepresentados entre los nacidos en ciudades
  chicas y medianas.
- **H2.** El interior produce más futbolistas per cápita que el AMBA.
- **H3.** Existe migración sistemática entre el lugar de nacimiento y el club
  formador.
- **H4.** El efecto se intensifica con el nivel competitivo alcanzado.
- **Exploratorio.** Asociación entre posición y región de nacimiento.

---

## 2. Métodos

### 2.1 El denominador: nacidos vivos, no población censada

Es la decisión metodológica central y conviene explicar por qué.

**Lo que no sirve.** Contar futbolistas nacidos en 1975 contra la población
censada en 2022 no mide nacimientos: mide quiénes seguían vivos y residiendo en
el mismo lugar casi cincuenta años después. Ese denominador está contaminado por
mortalidad y, sobre todo, por migración interna —que en Argentina va justamente
del interior hacia el centro, en la misma dirección que el fenómeno bajo estudio.

**Lo que se usa.** El denominador es el número de **nacidos vivos** de cada
cohorte en cada lugar:

| Nivel | Fuente | Naturaleza |
|---|---|---|
| Provincia | DEIS, serie histórica de nacidos vivos por jurisdicción, 1914–2024 | **Dato real**, por año |
| Departamento / ciudad | el total provincial real, repartido según la participación de cada departamento en la población de su provincia en el censo más cercano al año de nacimiento (1991, 2001, 2010, 2022) | **Estimado** |

El reparto intraprovincial es el principal supuesto de la cadena —el otro es el
reparto de los partidos divididos, §4.3— y se valida: el
RENAPER publica nacimientos por departamento para 2012–2022, cohortes demasiado
recientes para tener futbolistas pero suficientes para medir el error del
supuesto. El error relativo mediano es del **9,1%** y el 84,1% de los
departamentos cae dentro del 20% (tabla `qa_validacion_denominador.csv`).

**Ese error tiene signo y tiene pendiente, y hay que decirlo (Figura 19).** No se
distribuye parejo: al decil de departamentos más chicos el estimador le asigna un
**17% más** de nacimientos de los reales, mientras que en el decil más grande no
se equivoca (Spearman entre tamaño y ratio estimado/real = −0,355; p < 10⁻¹⁵). Un
denominador inflado deprime la tasa, de modo que **el sesgo empuja en la misma
dirección que el hallazgo principal**: corregirlo llevaría el RR de las
localidades chicas de 0,45 a aproximadamente 0,52 —el efecto sobreviviría, pero
es un 17% más chico de lo que la tabla sugiere. La correlación global de 0,993
que se reportaba antes no mide exactitud: entre unidades que van de 435 a 60.160
nacimientos, cualquier reparto proporcional al tamaño la alcanza.

Una advertencia sobre la validación: la serie del RENAPER está construida por
residencia o registro y no por lugar de ocurrencia —su tasa bruta de natalidad
departamental tiene media 15,5 por mil y el 97% de los casos entre 8 y 30,
valores incompatibles con un conteo por lugar del parto—. Eso hacía sospechar
que validar un reparto por población residente contra una fuente por residencia
era circular. Resulta que no lo es, pero por una razón que obligó a rehacer el
argumento entero de esta sección.

#### 2.1.1 Qué criterio usan realmente las dos puntas del cociente

Es la pregunta de la que depende todo el trabajo, y hasta ahora estaba sin
contestar. Se contesta con dos pruebas (**Figura 27**, tablas
`criterio_denominador_*` y `criterio_p19_*`).

**El denominador no cuenta partos: cuenta residencias.** El DEIS publica dos
series de nacidos vivos por jurisdicción. La histórica 1914–2024 —la que usa este
trabajo— se titula «nacimientos **ocurridos**». La otra, 2005–2022, es
explícitamente por **residencia de la madre**. En las **432 celdas
provincia×año** en que se solapan, las dos series son **idénticas**: cero celdas
con diferencia, diferencia absoluta máxima cero. CABA, cuyas maternidades atienden
partos de todo el conurbano y que por ocurrencia debería mostrar un exceso
grande, coincide año por año al dígito.

Cualquiera sea su título, el dato es la tabulación por residencia. La afirmación
que este paper hacía —que la serie cuenta partos y que por eso comparte
definición con el `P19` de Wikidata— **era falsa**, y se sostenía sobre el título
del recurso en el portal, no sobre el dato.

**El numerador tampoco: registra el pueblo.** Si el `P19` de Wikidata anotara el
lugar del parto, las localidades sin maternidad tendrían cero futbolistas —nadie
nace materialmente en un paraje de cien habitantes— y la tasa por tamaño de
localidad mostraría un **escalón** en el umbral en que una localidad puede
sostener una maternidad. No es lo que se observa: hay **76 futbolistas cuyo `P19`
apunta a localidades de menos de 2.000 habitantes, repartidos en 63 localidades
distintas**. Emiliano Sala figura nacido en Cululú, Santa Fe, 106 habitantes;
José Basanta en Tres Sargentos, Buenos Aires, 456. Y la tasa no tiene forma de
escalón sino que sube irregularmente desde el tramo más chico (10,8 · 6,3 · 9,6 ·
12,7 · 15,0 por 100.000), sin ningún umbral.

**Consecuencia.** Las dos puntas del cociente registran, predominantemente, el
lugar de **residencia**, no el del parto. El artefacto de las maternidades —la
amenaza que este paper declaraba como su limitación central, y que dos revisiones
independientes señalaron como el punto de falla del trabajo— **no está operando en
la dirección que se temía**. Y el cociente es definicionalmente coherente en todos
sus niveles, no solo en el provincial: residencia arriba y residencia abajo.

Queda una versión débil de la amenaza: que una fracción de los registros de
Wikidata sí anote la ciudad cabecera. La cota superior de esa fracción es
**44,5%**, y se calcula del peor modo posible —atribuyendo **todo** el déficit de
las localidades chicas a mala atribución y **nada** a un efecto real—. No es una
estimación: es un techo, y el hecho de que 63 localidades de menos de 2.000
habitantes aparezcan como lugar de nacimiento sugiere que el valor real está muy
por debajo. Medirlo requiere contrastar el `P19` contra un padrón independiente
(§4.3, limitación 3).

Como control, se reportan además cinco denominadores alternativos (población
total en los censos 1991, 2001, 2010 y 2022, y personas que en 2022 declararon
haber nacido en cada provincia). **El orden de las provincias no cambia con
ninguno de ellos** (Figura 24).

### 2.2 Ventana de cohortes

**1975–2008.** Los dos límites los impuso el dato, no la comodidad:

- *Hacia atrás*: la serie del DEIS **no publica 1971–1974**, único hueco en 110
  años. Empezar en 1970 dejaba a esa cohorte con el denominador de un solo año y
  su tasa salía cinco veces más alta sin que nada fallara. El pipeline ahora
  rechaza cualquier ventana con huecos (`build_denominators.verificar_cobertura`).
- *Hacia adelante*: la carrera. Quien nació en 2008 tenía 14 años en 2022 y no
  puede haber debutado.

La censura a derecha se cuantifica cohorte por cohorte (**Figura 12**, tabla
`diagnostico_censura_cohortes.csv`): la tasa sube de 17 por 100.000 en 1975–1979
a un pico de 37 en 1985–1989, y cae a 15 en 2000–2004 y 3 en 2005–2009. La caída
final es censura; la inicial es cobertura, porque Wikidata registra peor a los
jugadores más viejos. El análisis principal usa toda la ventana y se repite
restringido a cohortes ≤ 2002 como robustez.

### 2.3 Muestra

Wikidata vía SPARQL, paginado por año de nacimiento, snapshot fechado en
`data/raw/wikidata/_snapshot.json`.

<!-- TABLA:muestra INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Paso | n |
|---|---:|
| Jugadores en wikidata | 9.115 |
| Precisión de fecha ≥ año (timeprecision ≥ 9) | 8.976 |
| Género = male | 8.649 |
| Con lugar de nacimiento (p19) | 8.290 |
| Lugar resuelto dentro de argentina | 7.711 |
| **Cohorte 1975–2008** | **5.511** |
<!-- TABLA:muestra FIN -->

### 2.4 Resolución geográfica

Los nombres de lugares argentinos en Wikidata son inconsistentes: hay homónimos
entre provincias (cuatro localidades se llaman Santa Rosa) y entidades que son
provincias o partidos y no ciudades. **Se resuelve por coordenada** (`P625`)
contra la API Georef del Estado argentino; el nombre solo se usa como chequeo
cruzado.

La granularidad de cada entidad se clasifica antes de usarla: 20 lugares de
nacimiento son provincias, 83 departamentos o partidos, dos regiones y cuatro
países. El caso más consecuente es la entidad «Argentina», que 255 jugadores
tienen como lugar de nacimiento: su centroide cae en el departamento Presidente
Roque Sáenz Peña de Córdoba y, sin ese filtro, convertía a General Levalle
—5.674 habitantes— en la tercera cuna de futbolistas del país.

**El mismo problema aparece un nivel más arriba y también se corrige.** Cuando el
`P19` es una provincia entera, su centroide cae en un departamento cualquiera:
el de Buenos Aires en Azul, el de Córdoba en Tercero Arriba, el de San Juan en
Ullum. Los 110 jugadores en esa situación quedaban asignados a esos
departamentos, que así llegaban al top-12 nacional de tasa —Ullum y Tumbaya con
la totalidad de su cuenta fabricada, Azul inflado un 222%—. Ahora conservan la
provincia, que es dato válido, y quedan **excluidos del análisis departamental y
del de tamaño de ciudad**. El análisis provincial usa los 5.511; el departamental,
5.389; el de tamaño de ciudad, 5.248.

**«Tamaño de ciudad» = aglomerado urbano cuando existe.** Lanús no es una ciudad
de 200.000 habitantes: es una porción de un conurbano de 16,2 millones. Se usa la
definición de aglomerado del propio INDEC, y se reporta la variante con la
localidad aislada como control.

### 2.5 Estadística

Chi-cuadrado de bondad de ajuste contra la distribución real de nacimientos
—nunca uniforme—, con Cohen's *w* y Cramér's *V*. Tasas por 100.000 con intervalo
exacto de Poisson (Garwood), elegido porque muchos departamentos tienen cero, uno
o dos jugadores. Razones de tasas y *odds ratios* con IC 95%. Regresión binomial
negativa con *offset* logarítmico de los nacimientos. Corrección de
Benjamini-Hochberg en los cruces exploratorios.

### 2.6 La limitación central: nacer ≠ formarse

Wikidata da el lugar de **nacimiento**, no el de desarrollo. Para H3 se construyó
un proxy del club formador: el vínculo jugador-club (`P54`) con la fecha de
inicio (`P580`) más temprana, excluyendo selecciones. **Es un proxy.** Wikidata
suele omitir las inferiores, con lo cual el primer club listado es muchas veces
el de debut profesional; y su cobertura es muy desigual por nivel: 99,2% entre
los jugadores de selección mayor contra 12,7% en el resto. H3 se apoya en 1.923
jugadores con origen y club formador ubicados en Argentina.

---

## 3. Resultados

### 3.1 H1 — El efecto aparece invertido

**Figuras 4 y 7.**

<!-- TABLA:h1_tramos INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Tamaño de la ciudad | Futbolistas | Nacidos | Tasa /100.000 | IC 95% | RR vs >500k |
|---|---:|---:|---:|---|---|
| <10k | 431 | 3.385.077 | 12,7 | 11,6–14,0 | 0,45 (0,41–0,50) |
| 10–50k | 568 | 3.491.322 | 16,3 | 15,0–17,7 | 0,57 (0,52–0,63) |
| 50–100k | 275 | 1.338.281 | 20,5 | 18,2–23,1 | 0,72 (0,64–0,82) |
| 100–500k | 631 | 2.994.490 | 21,1 | 19,5–22,8 | 0,74 (0,68–0,81) |
| **>500k** | **3.343** | **11.788.344** | **28,4** | **27,4–29,3** | **1,00** |
<!-- TABLA:h1_tramos FIN -->

χ²(4) = 382,1; p < 10⁻⁸⁰; *w* = 0,27; n = 5.248.

El tramo de 50.000 a 100.000 habitantes —el óptimo que predice la literatura— no
muestra ningún pico. Con los cortes de Côté et al. (2006) el resultado es el
mismo: de 8,3 por 100.000 en localidades de menos de 1.000 habitantes a 28,4 en
las de más de 500.000.

**No es un gradiente: es un escalón (Figura 20).** La tabla de cinco tramos
sugiere una progresión ordenada, pero esa forma la produce el ancho de las
categorías. Por decil de tamaño de ciudad las tasas son 22,6 · 4,6 · 14,0 · 4,9 ·
8,5 · 8,8 · 13,3 · 11,3 · 16,0 · 25,9: **tres de los nueve pasos bajan**, y los
nueve deciles por debajo de ~10.000 habitantes —463 futbolistas, el 9% de la
muestra— no muestran ninguna tendencia. Todo el efecto es el salto del decil
superior. Esa forma —un escalón único— es también la que produciría el registro
del parto en la ciudad cabecera, y por eso se la sospechó como artefacto en las
dos primeras versiones de este trabajo. La §2.1.1 muestra que ese mecanismo no
está operando: la forma del efecto queda sin explicación por esa vía y pide otra.

**Regresión.** Modelo binomial negativo sobre 3.477 ciudades: cada *e-fold* de
tamaño multiplica la tasa por 1,175 (IC 95% 1,114–1,240; p < 0,0001). Con el
término cuadrático **ni el lineal ni el cuadrático resultan significativos**
(p = 0,11 y p = 0,44) y el AIC empeora (3.654,3 contra 3.652,8). No hay curva en
U invertida que ajustar.

**Y el tamaño del efecto es chico (Figura 7).** El pseudo-R² de McFadden de ese
modelo es **0,011** y la devianza explicada, 2,6%: el tamaño de la ciudad da
cuenta de alrededor del 1% de la variación entre ciudades. La pendiente es real y
está bien estimada; su capacidad para predecir cuántos futbolistas produce una
ciudad determinada es casi nula. A 100.000 habitantes las ciudades reales van de
3 a 100 por cada 100.000 nacidos.

**Robustez.** El patrón se sostiene en las dos variantes:

<!-- TABLA:h1_robustez INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Variante | RR <10k vs >500k | IC 95% |
|---|---:|---|
| Principal (aglomerado urbano) | 0,45 | 0,41–0,50 |
| Unidad = localidad censal aislada | 0,36 | 0,32–0,40 |
| Solo cohortes ≤ 2002 | 0,44 | 0,39–0,49 |
<!-- TABLA:h1_robustez FIN -->

Con el denominador anterior —población censada en 2022— este mismo RR daba 0,57.
El denominador correcto **fortalece** el hallazgo, no lo debilita: la migración
del interior a las ciudades estaba inflando artificialmente la tasa de los
pueblos.

### 3.2 H2 — AMBA y corredor pampeano

**Figuras 1, 3, 5 y 6.** Por región (χ²(5) = 1.050,7; *w* = 0,44):

<!-- TABLA:h2_regiones INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Región | Futbolistas | Tasa /100.000 | IC 95% | RR vs AMBA |
|---|---:|---:|---|---:|
| Pampeana | 2.587 | 34,5 | 33,2–35,9 | 1,22 |
| AMBA | 1.872 | 28,3 | 27,0–29,6 | 1,00 |
| Cuyo | 265 | 15,2 | 13,4–17,2 | 0,54 |
| Patagonia | 153 | 12,7 | 10,8–14,9 | 0,45 |
| NEA | 255 | 9,6 | 8,4–10,8 | 0,34 |
| NOA | 269 | 8,2 | 7,2–9,2 | 0,29 |
<!-- TABLA:h2_regiones FIN -->

**H2 no se sostiene, aunque no del modo en que se creyó al principio.** El
interior no produce más que el centro: el norte produce cuatro veces menos. Pero
el AMBA **no** encabeza: la región pampeana produce un 22% más por nacido (34,5
contra 28,3). La producción se concentra en un corredor pampeano —Santa Fe,
Córdoba, el centro bonaerense— y el AMBA viene después. Por provincia:

<!-- TABLA:h2_provincias INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
|  | Provincia | Futbolistas | Tasa /100.000 | Obs./Esp. |
|---:|---|---:|---:|---:|
| 1 | Ciudad Autónoma de Buenos Aires | 962 | 63,0 | 2,63 |
| 2 | Santa Fe | 950 | 54,2 | 2,26 |
| 3 | Córdoba | 577 | 31,6 | 1,32 |
| 4 | La Pampa | 49 | 27,1 | 1,13 |
| 5 | Entre Ríos | 181 | 23,7 | 0,99 |
| … |  |  |  |  |
| 22 | Catamarca | 15 | 6,5 | 0,27 |
| 23 | San Juan | 28 | 6,2 | 0,26 |
| 24 | Salta | 46 | 5,5 | 0,23 |
<!-- TABLA:h2_provincias FIN -->

El orden no depende del baseline: se probaron seis denominadores distintos y CABA
y Santa Fe encabezan en todos.

A nivel de ciudad (**Figura 11**), las cunas son **Rafaela** (98,0 cada 100.000
nacidos), **Gran Santa Fe** (72,8), **Gran Rosario** (58,3) y **Tandil** (53,6).
Rafaela, 102.000 habitantes, produce más del triple que el Gran Buenos Aires por
cada nacido. Es el único punto del mapa donde el folklore del pueblo chico
acierta, y no alcanza para sostener el patrón general.

### 3.3 H3 — La formación está mucho más concentrada que el nacimiento

**Figuras 8, 9 y 10.** Es el resultado con más consecuencias.

**Comparado con la población general, el futbolista migra cinco veces más.**

<!-- TABLA:h3_poblacion INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Grupo | n | Fuera de su provincia |
|---|---:|---:|
| Futbolistas (nacimiento → club formador) | 1.923 | **47,0%** |
| Población general (nacimiento → residencia, Censo 2022) | 42.640.509 | 13,8% |
<!-- TABLA:h3_poblacion FIN -->

OR 5,58 (IC 95% 5,10–6,10). El punto de comparación es lo que vuelve
interpretable el número.

**El corte por origen es un escalón, no un gradiente:**

<!-- TABLA:h3_tamano INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Ciudad de nacimiento | n | Cambia de departamento | Cambia de provincia | Distancia mediana |
|---|---:|---:|---:|---:|
| <10k | 150 | 94,0% | 61,3% | 307 km |
| 10–50k | 209 | 97,6% | 64,1% | 312 km |
| 50–100k | 107 | 86,0% | 65,4% | 256 km |
| 100–500k | 225 | 86,7% | 67,6% | 470 km |
| >500k | 1.197 | 52,0% | 36,7% | 7 km |
<!-- TABLA:h3_tamano FIN -->

Entre los cuatro tramos menores no hay gradiente: todos migran masivamente. El
escalón está entre los aglomerados de más de 500.000 habitantes y todo lo demás.
Nacer en una ciudad grande significa formarse a siete kilómetros de casa.

**Por región de origen la asimetría es estructural:**

<!-- TABLA:h3_regiones INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Región | Nacidos | Formados allí | Saldo neto | Retención |
|---|---:|---:|---:|---:|
| AMBA | 677 | 1.260 | +583 | 90,8% |
| Cuyo | 75 | 46 | -29 | 45,3% |
| Patagonia | 65 | 23 | -42 | 27,7% |
| NOA | 76 | 28 | -48 | 28,9% |
| NEA | 81 | 8 | -73 | 8,6% |
| Pampeana | 949 | 558 | -391 | 48,9% |
<!-- TABLA:h3_regiones FIN -->

El NEA retiene a uno de cada doce futbolistas que nacen en su territorio.

**Los clubes** (**Figura 10**) muestran el mecanismo con nombre y apellido:

<!-- TABLA:clubes INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Club | Formados | Distancia mediana | De otra provincia |
|---|---:|---:|---:|
| Boca Juniors | 143 | 277 km | 77% |
| Club Atlético River Plate | 122 | 265 km | 76% |
| Club Atlético Vélez Sarsfield | 98 | 18 km | 56% |
| Club Atlético Newell’s Old Boys | 98 | 37 km | 34% |
| Club Atlético Rosario Central | 94 | 0 km | 18% |
| Club Estudiantes de La Plata | 85 | 233 km | 41% |
<!-- TABLA:clubes FIN -->

Hay dos modelos distintos de club formador. Rosario Central y Newell's forman
jugadores que nacieron en Rosario o al lado: son una salida local para un talento
local. Boca y River funcionan como aspiradoras nacionales: la mitad de sus
formados nació a más de 270 km. **Diez clubes concentran el 48% de toda la
formación registrada del país; veinte concentran el 71%.**

### 3.4 H4 — No lo fabrica la cobertura de Wikidata

**Figuras 13 y 16.** La objeción más seria contra todo lo anterior es el sesgo de
cobertura. La prueba está en los jugadores de selección mayor, donde el registro
de Wikidata es prácticamente censal.

**El gradiente por tamaño se sostiene en los cuatro niveles**, incluida la
selección: 14,3 seleccionados por millón de nacidos en aglomerados de más de
500.000 contra 7,4 en localidades de menos de 10.000. Por región, 17,8 por millón
en la Pampeana y 14,2 en el AMBA, contra 2,1 en el NOA.

En cambio **H4 tal como estaba formulada no se sostiene**: no hay evidencia de
que la elite provenga más de ciudades chicas (OR 0,89; IC 95% 0,71–1,13).

Un matiz que la tabla de cinco tramos esconde y que conviene decir: dentro de la
selección, **los cuatro tramos no metropolitanos son indistinguibles entre sí**
(7,5 · 7,0 · 8,6 · 9,2 por millón, con intervalos que se solapan por completo).
Como en H1, lo que hay es un contraste binario contra los grandes aglomerados,
no una escalera.

Vale una aclaración sobre el alcance de esta prueba. Acota **la amenaza de
cobertura** y no dice nada sobre la otra, el registro del parto en la ciudad
cabecera, que afecta a los seleccionados exactamente igual que al resto: un
jugador nacido en una maternidad del Gran Buenos Aires y criado en un pueblo
cuenta como `>500k` en las dos puntas del cociente, sea o no famoso.

### 3.5 De los juveniles a la Mayor: el resultado que no depende del denominador

**Figuras 14, 15 y 16.** Todo lo anterior son tasas por nacido, y por lo tanto
heredan los dos problemas del denominador. Este análisis no.

La pregunta es otra: **entre los futbolistas que ya llegaron a un juvenil de la
selección (sub-17 o sub-20), ¿qué proporción llega después a la Mayor, según
dónde nacieron?** El denominador acá no es una estimación de nacimientos: son los
347 juveniles observados.

<!-- TABLA:conversion INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Ciudad de nacimiento | Juveniles | Llegan a la Mayor | % | IC 95% |
|---|---:|---:|---:|---|
| <10k | 19 | 7 | 36,8 | 16,3–61,6 |
| 10–50k | 25 | 14 | 56,0 | 34,9–75,6 |
| 50–100k | 20 | 6 | 30,0 | 11,9–54,3 |
| 100–500k | 31 | 12 | 38,7 | 21,8–57,8 |
| **>500k** | **242** | **68** | **28,1** | **22,5–34,2** |
<!-- TABLA:conversion FIN -->

Agrupando en el contraste que tiene potencia —fuera de un gran aglomerado contra
adentro—: **41,9% (44 de 105) contra 28,1% (68 de 242)**. OR 1,85 (IC 95%
1,14–2,98); χ²(1) = 5,77; p = 0,016; Fisher exacto p = 0,013.

**No es un efecto generacional.** Una regresión logística que agrega el año de
nacimiento como control deja el OR en 1,85 (IC 95% 1,13–3,02; p = 0,014).

Por qué este resultado resiste lo que los otros no:

- **No usa denominador poblacional.** El sesgo de imputación del 17% no lo toca.
- **No depende de dónde ocurrió el parto** para construir una tasa: el registro
  del nacimiento en la cabecera clasificaría a un pibe de pueblo como `>500k`, y
  eso **atenúa** el contraste en vez de crearlo. El efecto medido es un piso.
- **La cobertura de Wikidata es del 97%** entre jugadores de selección, y es la
  misma para los dos grupos que se comparan.
- **Compara dentro de un grupo ya filtrado por talento reconocido**, de modo que
  no hay que suponer que el talento latente se distribuye parejo.

La lectura es que el filtro de acceso y el filtro de rendimiento van en
direcciones opuestas. Llegar desde el interior es mucho menos probable —de eso
tratan §3.1 a §3.4—, pero condicionado a haber llegado, el jugador del interior
convierte más. Es lo que se espera si el acceso está seleccionando por algo
distinto del talento: quien atraviesa un filtro más exigente llega, en promedio,
mejor.

### 3.6 Exploratorio: posición y región

**Estrictamente exploratorio.** De 24 contrastes, seis sobreviven a la corrección
de Benjamini-Hochberg, y todos involucran a las dos regiones con más casos: el
AMBA produce más defensores y menos mediocampistas de lo esperado, y la región
pampeana lo inverso. **El mito de «las delanteras del norte» no aparece**: ningún
contraste que involucre al NOA o al NEA sobrevive a la corrección.

---

## 4. Discusión

### 4.1 Por qué el efecto está invertido

El *birthplace effect* clásico se apoya en un supuesto implícito: que la
infraestructura de desarrollo deportivo está razonablemente distribuida, de modo
que lo que diferencia a los lugares es la calidad del entorno de juego informal.
Bajo ese supuesto la ciudad mediana gana: tiene espacio y tiene liga.

En Argentina ese supuesto no se cumple. La formación está concentrada: diez clubes
concentran la mitad de la formación registrada del país, y están todos en el AMBA,
el Gran Rosario o el Gran La Plata. La interpretación natural es que el lugar de nacimiento no
mide acá la calidad del entorno formativo sino **la distancia a la infraestructura
formativa**, y que esa distancia opera como filtro de acceso.

Es una interpretación, no un resultado, y conviene ser explícito sobre eso. El
estudio **no mide distancia a un club con inferiores**: ninguna regresión incluye
esa variable, ni nivel socioeconómico, ni densidad de ligas locales, ni existencia
de pensión. Todo el análisis es descriptivo y las asociaciones no están
controladas por nada.

**Dos pruebas que el propio mecanismo permite, y sus resultados:**

- *Si la causa fuera la centralización creciente de las inferiores, la brecha
  debería ensancharse por cohorte.* No lo hace (**Figura 22**): la razón de tasas
  entre pueblo y gran aglomerado es 0,36 · 0,45 · 0,43 · 0,58 en las cohortes de
  los 70, 80, 90 y 2000, plana y con intervalos solapados. El mecanismo no queda
  refutado —la centralización pudo ser estable en el período—, pero tampoco
  encuentra apoyo donde debería.
- *Si el acceso filtrara por algo distinto del talento, quien atraviesa el filtro
  más exigente debería rendir mejor.* Eso sí aparece, y es el resultado más
  robusto del trabajo (§3.5): entre los juveniles de la selección, los nacidos
  fuera de un gran aglomerado llegan a la Mayor un 42% de las veces contra un 28%.

Esa asimetría —menos acceso, mejor rendimiento condicional— es la evidencia más
directa de que el patrón geográfico principal refleja acceso y no distribución de
talento. Y, a diferencia de todo lo demás, no depende del denominador.

Frente a la literatura, el aporte hay que dimensionarlo con cuidado. La revisión
sistemática de Hernández-Simal y colegas (2024) ya documenta hallazgos que
favorecen a las áreas densas, ya reporta que en fútbol no hay ventaja consistente
de las ciudades chicas, y ya identifica la proximidad a centros de rendimiento
como uno de sus tres ejes explicativos. Este trabajo **no descubre un mecanismo
nuevo**: aporta la primera medición argentina —Argentina no aparece en esa
revisión—, con un denominador de nacidos vivos por cohorte que es mejor que el de
buena parte de la literatura, y un diseño condicional que no necesita denominador.

### 4.2 Qué cambió al corregir el denominador, y qué cambió al corregir la geografía

Vale registrar las dos cosas porque son del tipo que decide un resultado en
silencio.

**El denominador.** Con la población censada en 2022, el RR de las localidades de
menos de 10.000 habitantes contra los grandes aglomerados daba 0,57; con los
nacimientos reales da 0,45. La diferencia es la migración: los pueblos son
exportadores netos de población, así que contar a sus residentes de 2022
subestimaba cuánta gente había nacido ahí e inflaba su tasa.

**La geografía.** Dos errores de códigos de departamento, ninguno de los cuales
fallaba ruidosamente porque los dos conservaban los totales provinciales y
rompían el reparto interno:

- Los códigos del INDEC **no son estables entre censos**: 44 de 532 cambiaron
  entre 1991 y 2022, casi todos por las divisiones de partidos bonaerenses de
  1994. Como los nacimientos se reparten con el censo más cercano al año de
  nacimiento y los jugadores se geocodifican contra la geografía 2022, los
  nacimientos de un partido dividido quedaban partidos entre un código viejo y
  uno nuevo, y el viejo se perdía río abajo: **1.049.301 nacimientos, el 4,6% del
  total y el 70% de ellos del Gran Buenos Aires**, desaparecían del denominador
  por ciudad. Magdalena encabezaba el ranking departamental con 163 futbolistas
  por 100.000 y era enteramente un artefacto (su valor real es 65).
- La lista de los 24 partidos del Gran Buenos Aires estaba **corrida un lugar**:
  doce de los veinticuatro códigos apuntaban a otro partido que el que decía su
  comentario. El «AMBA» del estudio excluía Quilmes, Merlo, San Miguel, Tres de
  Febrero y Vicente López, e incluía La Plata, Marcos Paz, Pilar y Presidente
  Perón.

Corregidos los dos, **la región pampeana pasa a producir más que el AMBA** (34,5
contra 28,3) y la razón interior/AMBA pasa de 0,59 a 0,79. Las versiones
anteriores de este trabajo afirmaban lo contrario, y afirmaban además —como
lección metodológica— que el cambio de denominador había puesto al AMBA por
encima de la pampeana. Esa inversión era el error, no un hallazgo.

Ahora los códigos se resuelven contra el padrón oficial del INDEC en lugar de
escribirse a mano, hay un crosswalk histórico versionado con el criterio de cada
equivalencia, y una verificación de conservación de masa corta el pipeline si
alguna transformación pierde nacimientos.

### 4.3 Limitaciones

1. **Nacer no es criarse.** Sigue siendo la limitación conceptual de fondo: el
   lugar de nacimiento no es el de crianza, y la literatura reciente señala a la
   transición entre los dos como lo que más pesa. El pipeline no tiene lugar de
   crianza en ninguna parte.
   Lo que **sí** quedó acotado es la versión mecánica del problema —que el parto
   ocurre donde hay maternidad y eso vacía los pueblos—. Las dos puntas del
   cociente registran residencia y no parto (§2.1.1), de modo que el artefacto no
   opera como se temía. Queda su versión débil: que una fracción de los registros
   de Wikidata anote la cabecera. Su cota superior es 44,5%, calculada del peor
   modo posible, y hay 63 localidades de menos de 2.000 habitantes que aparecen
   como lugar de nacimiento, lo que sugiere un valor bastante menor.
   Una advertencia que sobrevive intacta: el tramo `<10k` se construye sobre un
   padrón que incluye 264 «localidades» de menos de 100 habitantes, entre ellas
   `ZONA RURAL`. Sean o no artefacto, no son la categoría «small city» de Côté et
   al. (2006), que arranca en 1.000 habitantes con localidades urbanas.
2. **El reparto intraprovincial es un supuesto con sesgo direccional.** No solo
   es estimado: su error es del +17% en el decil de departamentos más chicos y
   nulo en el más grande (§2.1, Figura 19), y empuja en la misma dirección que el
   hallazgo. Corregirlo llevaría el RR de 0,45 a ~0,52.
3. **El reparto de los partidos divididos es un segundo supuesto.** Para bajar de
   un partido que ya no existe —General Sarmiento, Morón antes de 1994— a los
   partidos actuales, se reparte su población según la proporción que tienen los
   sucesores en el primer censo en que aparecen separados, lo que supone que esa
   proporción describe la que tenían antes de dividirse. Afecta a 44
   departamentos; el criterio de cada equivalencia está en
   `data/reference/crosswalk_departamentos.csv`.
4. **Cobertura de Wikidata.** Es un corpus de notabilidad, no un registro, y
   nunca se contrastó contra un padrón independiente de futbolistas
   profesionales: **la tasa de error del `P19` no está medida**. Se intentó: la
   fuente candidata —la Base de Datos del Fútbol Argentino— prohíbe explícitamente
   en su `robots.txt` el acceso de agentes automáticos, de modo que la validación
   requiere consulta manual o autorización del sitio. La cobertura además varía al
   doble entre cohortes (la de 1975–1979 rinde el 47,5% del pico de 1985–1989). El
   análisis por nivel competitivo acota el problema pero no lo elimina.
5. **H3 se mide sobre una muestra seleccionada por el desenlace.** La cobertura
   del club formador va del 99,2% en jugadores de selección al 12,7% en el resto,
   de modo que la submuestra de H3 está enriquecida al doble en jugadores de
   elite y vaciada cinco veces del resto. El 47,1% de migración y el «diez clubes
   concentran el 48%» describen a los que llegaron lejos, no a la población de
   futbolistas. Deben leerse como orden de magnitud y no como estimación.
6. **La comparación de H3 con la población general no es estrictamente
   comparable**: 47,1% (futbolistas, nacimiento → primer club, alrededor de los
   18 años) contra 13,8% (toda la población, todas las edades, nacimiento →
   residencia 2022). La variable `P14` del censo no está cruzada con edad, así
   que la comparación no se puede acotar a las mismas cohortes.
7. **Sin controles.** No hay ninguna covariable más allá del tamaño de la ciudad:
   ni distancia a un club con inferiores, ni nivel socioeconómico, ni densidad de
   ligas. El trabajo es descriptivo y las lecturas causales de §4.1 y §4.4 son
   interpretaciones, no estimaciones.
8. **Tamaño de efecto chico donde se lo mide de forma continua.** El tamaño de la
   ciudad explica el 1% de la variación entre ciudades (pseudo-R² = 0,011).
9. **Números chicos en el mapa departamental.** No se aplica *shrinkage* ni
   Bayes empírico: un departamento con dos jugadores encabeza el ranking per
   cápita por puro ruido de Poisson. La **Figura 21** separa qué departamentos se
   apartan de verdad de la media nacional y cuáles son varianza; el ranking crudo
   no debe leerse sin ella.
10. **Censura a derecha.** Las cohortes 2003–2008 están incompletas por
   construcción. Se incluyen, se marcan y el análisis se repite sin ellas.
11. **Unidad geográfica en metrópolis fragmentadas.** Las tasas por departamento
    se inflan en el núcleo de los aglomerados que cruzan límites administrativos
    (Capital de Mendoza recibe a los nacidos en todo el Gran Mendoza contra el
    denominador de un solo departamento). Por eso el análisis de tamaño usa
    aglomerados.
12. **Solo fútbol masculino.**

### 4.4 Implicancias

Conviene separar lo que el dato sostiene de lo que sugiere.

**Lo que el dato sostiene.** Entre los futbolistas que ya llegaron a un juvenil de
la selección, los nacidos fuera de un gran aglomerado llegan a la Mayor con más
frecuencia (OR 1,85; p = 0,013; sin cambios al controlar por cohorte). Es un
contraste dentro de un grupo observado, sin denominador estimado. Si el acceso
midiera talento, la tasa de conversión debería ser igual en los dos grupos; no lo
es. **Eso es evidencia de que el filtro de acceso está dejando afuera jugadores
que habrían rendido.**

Para quien tiene que decidir dónde poner un centro de detección, la implicancia es
concreta y no depende de ninguna de las limitaciones de §4.3: **un juvenil del
interior es, en promedio, mejor apuesta que uno del AMBA con el mismo nivel
alcanzado.** Con 105 casos fuera del AMBA el intervalo es ancho (1,14–2,98) y
merece confirmarse con el padrón real de convocatorias de AFA, que existe y no es
público.

**Lo que el dato solo sugiere.** Que las regiones que producen un cuarto de lo
esperado sean «reservas desaprovechadas» requiere suponer que el talento latente
se distribuye parejo entre regiones —un supuesto razonable pero no testeado acá—.
Y la retención del 8,3% del NEA sale de la submuestra sesgada de H3. La dirección
del argumento es plausible; su magnitud, no está establecida.

Y una advertencia metodológica que sí se sostiene sola: **cualquier métrica de
producción basada en el lugar de nacimiento le atribuye al AMBA jugadores que el
AMBA absorbió, no formó** —y, en la medida en que el parto ocurre en la cabecera,
también le atribuye a las ciudades chicos que nacieron ahí de casualidad.

---

## 5. Reproducibilidad

Todo el pipeline es código; `data/raw/` no se edita y cada descarga deja un
manifiesto fechado con URL y SHA-256. Las decisiones de diseño están en
`config.yaml` con su justificación, y las funciones que comparten numerador y
denominador tienen tests. El orden de ejecución está en el README.

### Fuentes

- **Wikidata**, vía SPARQL. CC0. Snapshot 2026-07-30.
- **DEIS** (Dirección de Estadística e Información en Salud), serie histórica de
  nacidos vivos por jurisdicción, 1914–2024.
- **RENAPER**, nacimientos por departamento 2012–2022 (validación).
- **INDEC**, Censo 2022 (tabulados por radio censal) y radios censales
  1991–2022.
- **API Georef** y **IGN**.

Transfermarkt no se utilizó: sus términos prohíben el scraping automatizado.

### Lecturas de fondo

Punto de partida bibliográfico; las afirmaciones de §1.1 deben verificarse contra
estas fuentes antes de cualquier publicación formal.

- Revisión sistemática del *birthplace effect* en fútbol:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11571467/
- «Place Matters» — nacimiento contra lugar de desarrollo:
  https://www.mdpi.com/2075-4663/12/4/99
- The geography of talent development:
  https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.1031227/full
