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
aparece es su inverso.** La producción es de 12,9 futbolistas cada 100.000
nacidos en localidades de menos de 10.000 habitantes contra 30,5 en aglomerados
de más de 500.000 (RR 0,42; IC 95% 0,38–0,47). El término cuadrático de un modelo
binomial negativo no aporta ajuste: no hay pico en las ciudades medianas. Pero el
efecto **no es un gradiente sino un escalón**: por decil de tamaño, los nueve
deciles por debajo de ~10.000 habitantes no muestran tendencia alguna, y el
tamaño de la ciudad explica apenas el 1% de la variación entre ciudades
(pseudo-R² = 0,011).

**Segundo, y es el resultado más robusto del trabajo: entre los que ya llegaron a
un juvenil de la selección, los nacidos fuera de un gran aglomerado llegan a la
Mayor con más frecuencia** —41,9% contra 28,1%; OR 1,85 (IC 95% 1,14–2,98),
p = 0,013, y 1,85 ajustando por cohorte de nacimiento. Este análisis **no usa
denominador poblacional**, de modo que no lo afectan ni el sesgo de imputación de
nacimientos ni el registro del parto en la ciudad cabecera ni la cobertura de
Wikidata. Dicho en criollo: al pibe del interior le cuesta mucho más entrar, pero
el que entra rinde más.

**Tercero: la producción se concentra en el AMBA y en un corredor pampeano.**
CABA produce 2,6 veces lo que le correspondería por sus nacimientos y Santa Fe
2,3; Salta, Catamarca y San Juan producen menos de un cuarto. El AMBA (35,0 cada
100.000) y la Pampa (30,2) cuadruplican al NOA (8,7).

**Cuarto: la formación está mucho más concentrada que el nacimiento.** El 47,1%
de los futbolistas se forma en una provincia distinta de aquella en la que nació,
contra el 13,8% de la población general que reside fuera de su provincia de
nacimiento (OR 5,58; IC 95% 5,10–6,10). El NEA retiene al 8,3% de los futbolistas
que nacen en su territorio; el AMBA, al 91,6%. Diez clubes concentran el 48% de
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

El reparto intraprovincial es el único supuesto de la cadena, y se valida: el
RENAPER publica nacimientos por departamento para 2012–2022, cohortes demasiado
recientes para tener futbolistas pero suficientes para medir el error del
supuesto. El error relativo mediano es del **9,1%** y el 83,8% de los
departamentos cae dentro del 20% (tabla `qa_validacion_denominador.csv`).

**Ese error tiene signo y tiene pendiente, y hay que decirlo (Figura 19).** No se
distribuye parejo: al decil de departamentos más chicos el estimador le asigna un
**17% más** de nacimientos de los reales, mientras que en el decil más grande no
se equivoca (Spearman entre tamaño y ratio estimado/real = −0,355; p < 10⁻¹⁵). Un
denominador inflado deprime la tasa, de modo que **el sesgo empuja en la misma
dirección que el hallazgo principal**: corregirlo llevaría el RR de las
localidades chicas de 0,42 a aproximadamente 0,49 —el efecto sobreviviría, pero
es un 17% más chico de lo que la tabla sugiere. La correlación global de 0,993
que se reportaba antes no mide exactitud: entre unidades que van de 435 a 60.160
nacimientos, cualquier reparto proporcional al tamaño la alcanza.

Una advertencia adicional sobre la validación: la serie del RENAPER parece estar
construida por residencia o registro y no por lugar de ocurrencia —su tasa bruta
de natalidad departamental tiene media 15,5 por mil y el 97% de los casos entre 8
y 30, valores incompatibles con un conteo por lugar del parto—. Validar un
reparto por población residente contra una fuente por residencia es en parte
circular. A nivel provincial las dos series coinciden dentro del 1,3% (CABA: DEIS
397.191, RENAPER 402.492), de modo que **con los datos disponibles no se puede
verificar la afirmación de que ambas puntas del cociente usan la misma
definición**; se declara como supuesto, no como hecho establecido.

**Y hay un límite de fondo que no se resuelve con más datos.** El portal del DEIS
publica la serie como nacimientos **ocurridos**, por lugar del parto, que sería la
misma definición que usa el `P19` de Wikidata: quien nació en una maternidad de la
Capital figuraría en la Capital en las dos puntas del cociente, y el cociente
sería válido. Pero esa simetría, aun si se cumpliera, **solo vale a nivel
provincial**, que es donde el DEIS es dato real. Por debajo de la provincia el
denominador ya no es por ocurrencia: es población residente repartida. Y es
justamente ahí —departamento, ciudad, tamaño de localidad— donde viven H1, el
ranking de cunas y las Figuras 1, 4, 7 y 11.

Dicho de otro modo: la defensa metodológica más fuerte del estudio no aplica en el
nivel donde se mide el efecto principal. Se declara como la limitación central
del trabajo (§4.3) y es la primera cosa que habría que resolver.

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

| Paso | n |
|---|---:|
| Futbolistas argentinos en Wikidata | 9.115 |
| Con precisión de fecha ≥ año | 8.976 |
| Muestra masculina | 8.649 |
| Con lugar de nacimiento (`P19`) | 8.290 |
| Con lugar resuelto dentro de Argentina | 7.711 |
| **Cohortes 1975–2008** | **5.511** |

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

| Tamaño de la ciudad | Futbolistas | Nacidos | Tasa /100.000 | IC 95% | RR vs >500k |
|---|---:|---:|---:|---|---|
| <10k | 431 | 3.339.078 | 12,9 | 11,7–14,2 | 0,42 (0,38–0,47) |
| 10–50k | 568 | 3.418.174 | 16,6 | 15,3–18,0 | 0,55 (0,50–0,60) |
| 50–100k | 275 | 1.280.832 | 21,5 | 19,0–24,2 | 0,70 (0,62–0,80) |
| 100–500k | 631 | 2.934.614 | 21,5 | 19,9–23,3 | 0,71 (0,65–0,77) |
| **>500k** | **3.343** | **10.975.566** | **30,5** | **29,4–31,5** | 1,00 |

χ²(4) = 452,2; p < 10⁻⁹⁵; *w* = 0,29; n = 5.248.

El tramo de 50.000 a 100.000 habitantes —el óptimo que predice la literatura— no
muestra ningún pico. Con los cortes de Côté et al. (2006) el resultado es el
mismo: de 8,4 por 100.000 en localidades de menos de 1.000 habitantes a 30,5 en
las de más de 500.000.

**No es un gradiente: es un escalón (Figura 20).** La tabla de cinco tramos
sugiere una progresión ordenada, pero esa forma la produce el ancho de las
categorías. Por decil de tamaño de ciudad las tasas son 22,6 · 4,6 · 14,0 · 4,9 ·
8,5 · 8,8 · 13,3 · 11,3 · 16,0 · 25,9: **tres de los nueve pasos bajan**, y los
nueve deciles por debajo de ~10.000 habitantes —463 futbolistas, el 9% de la
muestra— no muestran ninguna tendencia. Todo el efecto es el salto del decil
superior. Conviene registrarlo porque **un escalón único es también la forma que
produciría el registro del parto en la ciudad cabecera** (§4.3), mientras que un
gradiente continuo no lo sería.

**Regresión.** Modelo binomial negativo sobre 3.459 ciudades: cada *e-fold* de
tamaño multiplica la tasa por 1,181 (IC 95% 1,120–1,246; p < 0,0001). Con el
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

| Variante | RR <10k vs >500k | IC 95% |
|---|---|---|
| Principal (aglomerado urbano) | 0,42 | 0,38–0,47 |
| Unidad = localidad censal aislada | 0,39 | 0,35–0,43 |
| Solo cohortes ≤ 2002 | 0,41 | 0,37–0,46 |

Con el denominador anterior —población censada en 2022— este mismo RR daba 0,57.
El denominador correcto **fortalece** el hallazgo, no lo debilita: la migración
del interior a las ciudades estaba inflando artificialmente la tasa de los
pueblos.

### 3.2 H2 — AMBA y corredor pampeano

**Figuras 1, 3, 5 y 6.** Por región (χ²(5) = 1.050,7; *w* = 0,44):

| Región | Futbolistas | Tasa /100.000 | IC 95% | RR vs AMBA |
|---|---:|---:|---|---|
| AMBA | 1.859 | 35,0 | 33,5–36,7 | 1,00 |
| Pampeana | 2.659 | 30,2 | 29,1–31,4 | 0,86 |
| Cuyo | 280 | 16,1 | 14,3–18,1 | 0,46 |
| Patagonia | 159 | 13,2 | 11,2–15,4 | 0,38 |
| NEA | 269 | 10,1 | 8,9–11,4 | 0,29 |
| NOA | 285 | 8,7 | 7,7–9,8 | 0,25 |

**H2 no se sostiene.** El interior no produce más que el AMBA: produce menos, y
en el norte produce cuatro veces menos. Por provincia:

| | Provincia | Futbolistas | Tasa /100.000 | Obs./Esp. |
|---|---|---:|---:|---:|
| 1 | CABA | 962 | 63,0 | 2,63 |
| 2 | Santa Fe | 950 | 54,2 | 2,26 |
| 3 | Córdoba | 577 | 31,6 | 1,32 |
| 4 | La Pampa | 49 | 27,1 | 1,13 |
| 5 | Entre Ríos | 181 | 23,8 | 0,99 |
| … | | | | |
| 22 | La Rioja | 14 | 7,1 | 0,29 |
| 23 | San Juan | 28 | 6,2 | 0,26 |
| 24 | Salta | 46 | 5,5 | 0,23 |

El orden no depende del baseline: se probaron seis denominadores distintos y CABA
y Santa Fe encabezan en todos.

A nivel de ciudad (**Figura 11**), las cunas son **Rafaela** (98,0 cada 100.000
nacidos), **Gran Santa Fe** (72,8), **Gran Rosario** (58,3) y **Tandil** (53,6).
Rafaela, 102.000 habitantes, produce tres veces más que el Gran Buenos Aires por
cada nacido. Es el único punto del mapa donde el folklore del pueblo chico
acierta, y no alcanza para sostener el patrón general.

### 3.3 H3 — La formación está mucho más concentrada que el nacimiento

**Figuras 8, 9 y 10.** Es el resultado con más consecuencias.

**Comparado con la población general, el futbolista migra cinco veces más.**

| Grupo | n | Fuera de su provincia |
|---|---:|---:|
| Futbolistas (nacimiento → club formador) | 1.923 | **47,1%** |
| Población general (nacimiento → residencia, Censo 2022) | 42.640.509 | 13,8% |

OR 5,58 (IC 95% 5,10–6,10). El punto de comparación es lo que vuelve
interpretable el número.

**El corte por origen es un escalón, no un gradiente:**

| Ciudad de nacimiento | n | Cambia de departamento | Cambia de provincia | Distancia mediana |
|---|---:|---:|---:|---:|
| <10k | 150 | 94,0% | 61,3% | 307 km |
| 10–50k | 209 | 97,6% | 64,1% | 312 km |
| 50–100k | 107 | 86,0% | 65,4% | 256 km |
| 100–500k | 225 | 86,7% | 67,6% | 470 km |
| >500k | 1.197 | 52,0% | 36,7% | **7 km** |

Entre los cuatro tramos menores no hay gradiente: todos migran masivamente. El
escalón está entre los aglomerados de más de 500.000 habitantes y todo lo demás.
Nacer en una ciudad grande significa formarse a siete kilómetros de casa.

**Por región de origen la asimetría es estructural:**

| Región | Nacidos | Formados allí | Saldo neto | Retención |
|---|---:|---:|---:|---:|
| AMBA | 676 | 1.273 | **+597** | 91,6% |
| Pampeana | 963 | 563 | −400 | 49,4% |
| Cuyo | 79 | 50 | −29 | 48,1% |
| Patagonia | 66 | 24 | −42 | 28,8% |
| NOA | 79 | 29 | −50 | 29,1% |
| NEA | 84 | 8 | −76 | **8,3%** |

El NEA retiene a uno de cada doce futbolistas que nacen en su territorio.

**Los clubes** (**Figura 10**) muestran el mecanismo con nombre y apellido:

| Club | Formados | Distancia mediana | De otra provincia |
|---|---:|---:|---:|
| Boca Juniors | 143 | 277 km | 77% |
| River Plate | 122 | 265 km | 76% |
| Vélez Sarsfield | 98 | 18 km | 56% |
| Newell's Old Boys | 98 | 37 km | 34% |
| Rosario Central | 94 | **0 km** | 18% |
| Estudiantes | 85 | 233 km | 41% |

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
selección (χ²(4) = 26,5; p < 0,0001; *w* = 0,32; n = 255): 15,3 seleccionados por
millón de nacidos en aglomerados de más de 500.000 contra 7,5 en localidades de
menos de 10.000. Por región, 17 por millón en el AMBA contra 2 en el NOA.

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

| Ciudad de nacimiento | Juveniles | Llegan a la Mayor | % | IC 95% |
|---|---:|---:|---:|---|
| <10k | 19 | 7 | 36,8 | 16,3–61,6 |
| 10–50k | 25 | 14 | 56,0 | 34,9–75,6 |
| 50–100k | 20 | 6 | 30,0 | 11,9–54,3 |
| 100–500k | 31 | 12 | 38,7 | 21,8–57,8 |
| **>500k** | **242** | **68** | **28,1** | 22,5–34,2 |

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
Rosario o La Plata. La interpretación natural es que el lugar de nacimiento no
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
  entre pueblo y gran aglomerado es 0,34 · 0,43 · 0,41 · 0,55 en las cohortes de
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

### 4.2 Qué cambió al corregir el denominador

Vale registrarlo porque es el tipo de cosa que decide un resultado en silencio.
Con la población censada en 2022 como denominador, el RR de las localidades de
menos de 10.000 habitantes contra los grandes aglomerados daba 0,57; con los
nacimientos reales da 0,42. La diferencia es la migración: los pueblos son
exportadores netos de población, así que contar a sus residentes de 2022
subestimaba cuánta gente había nacido ahí e inflaba su tasa.

En la misma corrección, el AMBA pasó de estar por debajo de la región pampeana a
estar por encima. Las áreas metropolitanas tienen menos hijos por habitante, de
modo que un denominador de población las hacía parecer menos productivas de lo
que son por nacido.

### 4.3 Limitaciones

1. **Nacer no es criarse, y en Argentina el parto ocurre donde hay maternidad.**
   Es la limitación más seria y no está acotada. Un chico de un pueblo de 3.000
   habitantes nace en la cabecera departamental y queda registrado ahí, en el
   DEIS y en Wikidata. Eso vacía sistemáticamente a las localidades chicas y llena
   a las cabeceras. Dos señales de que el problema es real: el tramo `<10k` se
   construye sobre un padrón que incluye 264 «localidades» de menos de 100
   habitantes —entre ellas `ZONA RURAL` y parajes de seis personas, donde
   materialmente no nace nadie—, y la forma del efecto es un escalón único
   (§3.1), que es exactamente lo que este artefacto produciría. **El análisis de
   §3.5 se diseñó para esquivar el problema; los de §3.1 a §3.4 lo padecen.**
2. **El reparto intraprovincial es un supuesto con sesgo direccional.** No solo
   es estimado: su error es del +17% en el decil de departamentos más chicos y
   nulo en el más grande (§2.1, Figura 19), y empuja en la misma dirección que el
   hallazgo. Corregirlo llevaría el RR de 0,42 a ~0,49.
3. **Cobertura de Wikidata.** Es un corpus de notabilidad, no un registro, y
   nunca se contrastó contra un padrón independiente de futbolistas
   profesionales: **la tasa de error del `P19` no está medida**. La cobertura
   además varía al doble entre cohortes (la de 1975–1979 rinde el 47,5% del pico
   de 1985–1989). El análisis por nivel competitivo acota el problema pero no lo
   elimina.
4. **H3 se mide sobre una muestra seleccionada por el desenlace.** La cobertura
   del club formador va del 99,2% en jugadores de selección al 12,7% en el resto,
   de modo que la submuestra de H3 está enriquecida al doble en jugadores de
   elite y vaciada cinco veces del resto. El 47,1% de migración y el «diez clubes
   concentran el 48%» describen a los que llegaron lejos, no a la población de
   futbolistas. Deben leerse como orden de magnitud y no como estimación.
5. **La comparación de H3 con la población general no es estrictamente
   comparable**: 47,1% (futbolistas, nacimiento → primer club, alrededor de los
   18 años) contra 13,8% (toda la población, todas las edades, nacimiento →
   residencia 2022). La variable `P14` del censo no está cruzada con edad, así
   que la comparación no se puede acotar a las mismas cohortes.
6. **Sin controles.** No hay ninguna covariable más allá del tamaño de la ciudad:
   ni distancia a un club con inferiores, ni nivel socioeconómico, ni densidad de
   ligas. El trabajo es descriptivo y las lecturas causales de §4.1 y §4.4 son
   interpretaciones, no estimaciones.
7. **Tamaño de efecto chico donde se lo mide de forma continua.** El tamaño de la
   ciudad explica el 1% de la variación entre ciudades (pseudo-R² = 0,011).
8. **Números chicos en el mapa departamental.** No se aplica *shrinkage* ni
   Bayes empírico: un departamento con dos jugadores encabeza el ranking per
   cápita por puro ruido de Poisson. La **Figura 21** separa qué departamentos se
   apartan de verdad de la media nacional y cuáles son varianza; el ranking crudo
   no debe leerse sin ella.
9. **Censura a derecha.** Las cohortes 2003–2008 están incompletas por
   construcción. Se incluyen, se marcan y el análisis se repite sin ellas.
10. **Unidad geográfica en metrópolis fragmentadas.** Las tasas por departamento
    se inflan en el núcleo de los aglomerados que cruzan límites administrativos
    (Capital de Mendoza recibe a los nacidos en todo el Gran Mendoza contra el
    denominador de un solo departamento). Por eso el análisis de tamaño usa
    aglomerados.
11. **Solo fútbol masculino.**

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
