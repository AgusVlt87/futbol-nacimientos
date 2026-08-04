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
(pseudo-R² = 0,010).

**Segundo, y es lo que vuelve interpretable a todo lo demás: el artefacto de las
maternidades no está operando.** La objeción de fondo contra cualquier estudio de
lugar de nacimiento es que el parto ocurre donde hay maternidad, de modo que los
pueblos se vacían y las cabeceras se llenan. Se probó, y las dos puntas del
cociente registran **residencia**, no parto: la serie del DEIS titulada
«nacimientos ocurridos» es idéntica a la tabulación por residencia de la madre en
las 432 celdas provincia×año en que se solapan (diferencia máxima: cero), y hay 76
futbolistas cuyo `P19` apunta a localidades de menos de 2.000 habitantes, en 63
localidades distintas, donde ninguna maternidad puede existir (**Figura 27**).

**Tercero: el patrón es del fútbol, no del país.** Corrido el mismo análisis
sobre otros deportes —misma ventana, mismo denominador, misma cadena de
geocoding—, la geografía cambia por completo. En el contraste que define el
*birthplace effect*, las ciudades de 50.000 a 100.000 habitantes contra los
grandes aglomerados: **el básquet da RR 1,95 (IC 95% 1,38–2,76) y el fútbol 0,72
(0,64–0,82)**, con intervalos que no se tocan. El básquet argentino tiene el
efecto clásico, con su pico exactamente donde la literatura lo predice; el rugby
está aún más concentrado que el fútbol (RR 0,08). Si lo que se midiera fuera
infraestructura general, nivel socioeconómico o cobertura de Wikipedia, los tres
deportes darían el mismo mapa (**Figura 28**). El **fútbol femenino**, en cambio,
es indistinguible del masculino (RR 0,73; p = 0,76 en el test de homogeneidad por
tramo) pese a tener una infraestructura completamente distinta y haberse
profesionalizado recién en 2019: lo que separa los mapas es el deporte, no la
estructura profesional que lo sostiene.

**Cuarto, y es el resultado más robusto del trabajo: entre los que ya llegaron a
un juvenil de la selección, los nacidos fuera de un gran aglomerado llegan a la
Mayor con más frecuencia** —41,1% contra 28,1%; OR 1,78 (IC 95% 1,09–2,93),
p = 0,027, y 1,78 ajustando por cohorte de nacimiento. **Todo el contraste lo
aporta un solo estrato**: sin el tramo de 10.000 a 50.000 habitantes, 25 casos,
el OR cae a 1,42 y el intervalo cruza el 1. Este análisis **no usa
denominador poblacional**, de modo que no lo afectan ni el sesgo de imputación de
nacimientos ni la cobertura de Wikidata. Dicho en criollo: al pibe del interior le
cuesta mucho más entrar, pero el que entra rinde más.

**Quinto: la producción se concentra en el corredor pampeano y en el AMBA, en ese
orden.** La región pampeana produce 34,5 futbolistas cada 100.000 nacidos y el
AMBA 28,3, contra 8,2 del NOA y 9,6 del NEA. Por provincia, CABA produce 2,6 veces
lo que le correspondería por sus nacimientos y Santa Fe 2,3; Salta, Catamarca y
San Juan producen menos de un cuarto.

**Sexto: la formación está mucho más concentrada que el nacimiento, y el número
bajó cuando se arregló la muestra.** El 44,5% se forma en una provincia distinta
de aquella en la que nació y el NEA retiene al 11,2% de los suyos. Mientras el
club formador salía solo de Wikidata, la cobertura iba del 99,2% entre jugadores
de selección al 12,7% en el resto y la submuestra estaba **seleccionada por el
desenlace**: describía a los que llegaron a la elite, que son los que se mudaron.
Sumando el campo `equipo_debut` de las fichas de Wikipedia la cobertura del
estrato «resto» sube a 72,1% y la migración cae de 47,1% a 44,5% (OR 5,58 →
5,03). **El sesgo existía y estaba inflando el número**; el hallazgo sobrevive
(§3.3, §4.3 limitación 5).

**Séptimo: hay un segundo sesgo, del lado del numerador, que empuja igual y es de
magnitud comparable.** La *granularidad* con que Wikidata registra el lugar de
nacimiento no es independiente de la región: entre los jugadores cuyo `P19` es
una provincia entera —y que por eso quedan fuera del análisis de tamaño de
ciudad— el NOA, Cuyo y el NEA están sobrerrepresentados entre 2,7 y 2,9 veces
(χ²(5) = 72,9; p < 10⁻¹³). Atribuir los 486 casos excluidos al tramo menor —una
cota deliberadamente inverosímil— llevaría su RR de 0,45 a 0,96 (§3.6). En
cambio, **la tasa de error del lugar de nacimiento ya no es una incógnita**:
sobre 133 casos verificados a mano contra una fuente independiente el acuerdo es
del 94,1% y el error **no es diferencial** (6,1% contra 5,7%), muy por debajo del
25% que haría falta para tumbar el resultado (§3.7, §3.9).

**Octavo: con covariables, lo que domina es la pobreza y no la geografía de los
clubes.** Agregados al modelo el NBI departamental y la distancia al club
formador más cercano, el NBI explica siete veces más variación que el tamaño de
la ciudad (pseudo-R² 0,071 contra 0,010) y la distancia —fuerte por sí sola, IRR
0,825— se apaga por completo (IRR 0,981; p = 0,63): era un proxy de pobreza. El
tamaño sobrevive atenuado (1,175 → 1,105). Y solo el 17% de la variación residual
separa a un departamento de otro: el resto ocurre entre ciudades vecinas, de modo
que el mapa departamental resume mal el fenómeno (§3.11, §3.12).

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
**19% más** de nacimientos de los reales, mientras que en el decil más grande no
se equivoca (Spearman entre tamaño y ratio estimado/real = −0,362; p < 10⁻¹⁶). Un
denominador inflado deprime la tasa, de modo que **el sesgo empuja en la misma
dirección que el hallazgo principal**: corregirlo llevaría el RR de las
localidades chicas de 0,45 a aproximadamente 0,53 —el efecto sobreviviría, pero
es un 19% más chico de lo que la tabla sugiere. La correlación global de 0,993
que se reportaba antes no mide exactitud: entre unidades que van de 38 a 266.434
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
a un pico de 37 en 1985–1989, y cae a 15 en 2000–2004 y 3 en 2005–2008. La caída
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
nacimiento son provincias, 83 departamentos o partidos, tres regiones y cuatro
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
5.401; el de tamaño de ciudad, 5.248.

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
un proxy del club formador con **dos fuentes**, en este orden.

**Primera: Wikidata.** El vínculo jugador-club (`P54`) con la fecha de inicio
(`P580`) más temprana, excluyendo selecciones. Cubre el 40,9% de la muestra, y de
forma muy desigual por nivel: 99,2% entre los jugadores de selección mayor contra
12,7% en el resto.

**Segunda: las fichas de Wikipedia.** El campo `equipo_debut` de la plantilla
`{{Ficha de deportista}}`, que ningún bot volcó nunca al grafo. Se bajó por la
API de acción de Wikimedia —publicada para uso programático, contenido CC BY-SA,
218 pedidos en total— y el club se resolvió a QID por el **destino del enlace**,
nunca por el nombre. Cubre un 41,8% adicional. **No se usó Transfermarkt**, que
tiene el dato con mejor cobertura, porque sus términos de uso prohíben la
extracción automatizada.

**Por qué se pueden mezclar.** Contra los 106 clubes verificados a mano en BDFA,
y en los 45 casos donde ambas fuentes tienen dato, aciertan igual: 88,9% cada una
(McNemar exacto p = 1,00). Y el error de la ficha **no es diferencial por estrato
de nacimiento** (83,7% contra 80,5%, Fisher p = 0,78). Wikidata va primero donde
está solo porque trae la fecha del vínculo mejor definida; la columna
`primer_club_fuente` registra la procedencia de cada caso.

**Sigue siendo un proxy**: las dos fuentes suelen omitir las inferiores, con lo
cual el primer club listado es muchas veces el de debut profesional. H3 se apoya
en 3.879 jugadores con origen y club formador ubicados en Argentina.

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
categorías. Por decil de tamaño de ciudad las tasas son 22,7 · 4,6 · 13,7 · 4,9 ·
7,2 · 9,4 · 13,1 · 11,2 · 15,7 · 24,6: **tres de los nueve pasos bajan**, y los
nueve deciles por debajo de ~10.000 habitantes —463 futbolistas, el 9% de la
muestra— no muestran ninguna tendencia. Todo el efecto es el salto del decil
superior. Esa forma —un escalón único— es también la que produciría el registro
del parto en la ciudad cabecera, y por eso se la sospechó como artefacto en las
dos primeras versiones de este trabajo. La §2.1.1 muestra que ese mecanismo no
está operando: la forma del efecto queda sin explicación por esa vía y pide otra.

**Regresión.** Modelo binomial negativo sobre 3.477 ciudades: cada *e-fold* de
tamaño multiplica la tasa por 1,175 (IC 95% 1,114–1,240; p < 0,0001). Con el
término cuadrático **ni el lineal ni el cuadrático resultan significativos**
(p = 0,12 y p = 0,45) y el AIC empeora (3.654,6 contra 3.653,1). No hay curva en
U invertida que ajustar.

**Y el tamaño del efecto es chico (Figura 7).** El pseudo-R² de McFadden de ese
modelo es **0,010** y la devianza explicada, 2,5%: el tamaño de la ciudad da
cuenta de alrededor del 1% de la variación entre ciudades. La pendiente es real y
está bien estimada; su capacidad para predecir cuántos futbolistas produce una
ciudad determinada es casi nula. Entre las trece ciudades de 90.000 a 110.000
habitantes la producción va de 0 a 98 por cada 100.000 nacidos.

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

**Figuras 1, 3, 5 y 6.** Por región (χ²(5) = 1.110,8; *w* = 0,45):

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

**Figuras 8, 9 y 10.**

> **Advertencia que condiciona toda la sección.** La submuestra de H3 son 3.879
> jugadores con club formador identificable, el 70,4% de la muestra. Estuvo
> **seleccionada por el desenlace** mientras el club salía solo de Wikidata
> (99,2% de cobertura en selección contra 12,7% en el resto); sumando las fichas
> de Wikipedia el piso sube a 72,1% y la cobertura por estrato de **nacimiento**
> queda plana (81 a 88% en los cinco tramos). Queda un 17,3% sin club, todavía
> concentrado en los jugadores menos notables, así que la migración medida sigue
> siendo probablemente una **cota superior**. Los números de esta sección no se
> usan para sostener H1, H2 ni el resultado de §3.5.

**Comparado con la población general, el futbolista migra cinco veces más.**

<!-- TABLA:h3_poblacion INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Grupo | n | Fuera de su provincia |
|---|---:|---:|
| Futbolistas (nacimiento → club formador) | 3.879 | **44,5%** |
| Población general (nacimiento → residencia, Censo 2022) | 42.640.509 | 13,8% |
<!-- TABLA:h3_poblacion FIN -->

OR 5,03 (IC 95% 4,72–5,36). El punto de comparación es lo que vuelve
interpretable el número.

**El corte por origen es un escalón, no un gradiente:**

<!-- TABLA:h3_tamano INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Ciudad de nacimiento | n | Cambia de departamento | Cambia de provincia | Distancia mediana |
|---|---:|---:|---:|---:|
| <10k | 326 | 92,6% | 57,7% | 290 km |
| 10–50k | 426 | 96,2% | 57,5% | 280 km |
| 50–100k | 199 | 85,4% | 64,8% | 277 km |
| 100–500k | 444 | 76,8% | 60,6% | 358 km |
| >500k | 2.383 | 52,0% | 35,7% | 7 km |
<!-- TABLA:h3_tamano FIN -->

Entre los cuatro tramos menores no hay gradiente: todos migran masivamente. El
escalón está entre los aglomerados de más de 500.000 habitantes y todo lo demás.
Nacer en una ciudad grande significa formarse a siete kilómetros de casa.

**Por región de origen la asimetría es estructural:**

<!-- TABLA:h3_regiones INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Región | Nacidos | Formados allí | Saldo neto | Retención |
|---|---:|---:|---:|---:|
| AMBA | 1.348 | 2.147 | +799 | 92,2% |
| Cuyo | 171 | 138 | -33 | 59,6% |
| Patagonia | 113 | 65 | -48 | 34,5% |
| NOA | 176 | 100 | -76 | 42,6% |
| NEA | 169 | 26 | -143 | 11,2% |
| Pampeana | 1.902 | 1.403 | -499 | 63,6% |
<!-- TABLA:h3_regiones FIN -->

El NEA retiene a uno de cada nueve futbolistas que nacen en su territorio.

**Los clubes** (**Figura 10**) muestran el mecanismo con nombre y apellido:

<!-- TABLA:clubes INICIO -->
<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->
| Club | Formados | Distancia mediana | De otra provincia |
|---|---:|---:|---:|
| Boca Juniors | 216 | 277 km | 81% |
| Club Atlético River Plate | 177 | 236 km | 77% |
| Club Atlético Newell’s Old Boys | 159 | 38 km | 32% |
| Club Atlético Vélez Sarsfield | 157 | 19 km | 58% |
| Club Atlético Rosario Central | 155 | 0 km | 20% |
| Club Estudiantes de La Plata | 130 | 144 km | 36% |
<!-- TABLA:clubes FIN -->

Hay dos modelos distintos de club formador. Rosario Central y Newell's forman
jugadores que nacieron en Rosario o al lado —mediana de 0 y 38 km, con el 20% y
el 32% venidos de otra provincia—: son una salida local para un talento local.
Boca y River funcionan como aspiradoras nacionales: la mitad de sus formados
nació a más de 277 y 236 km, y cuatro de cada cinco vienen de otra provincia.
**Diez clubes concentran el 37,6% de toda la formación registrada del país;
veinte concentran el 59,7%.**

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
(7,4 · 6,9 · 8,2 · 9,0 por millón, con intervalos que se solapan por completo).
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
337 juveniles observados.

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
adentro—: **41,1% (39 de 95) contra 28,1% (68 de 242)**. OR 1,78 (IC 95%
1,09–2,93); Fisher exacto p = 0,027.

**No es un efecto generacional.** Una regresión logística que agrega el año de
nacimiento como control deja el OR en 1,78 (IC 95% 1,08–2,96; p = 0,025).

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

### 3.6 El sesgo del numerador: la granularidad del `P19`

**Figura 32.** El estudio le dedicó tres revisiones al denominador y ninguna al
numerador más allá del geocoding. Pero el numerador tiene un sesgo propio y
empuja en la misma dirección que el hallazgo principal.

La **precisión** con que Wikidata registra el lugar de nacimiento depende de cuán
documentado esté el jugador. A un futbolista nacido en la Capital le ponen la
ciudad; a uno nacido en un pueblo de Santiago del Estero es más probable que le
pongan la provincia, o directamente «Argentina». Esos casos se excluyen del
análisis de tamaño de ciudad —correctamente, porque el centroide de una provincia
no ubica a nadie (§2.4)— pero si vienen desproporcionadamente del interior, la
exclusión le saca futbolistas justo a los tramos chicos.

**Viene del interior, y se puede probar.** De los jugadores con `P19` a nivel
provincia se conoce la provincia: es lo único que Wikidata dice de ellos.
Comparada contra la de los jugadores con `P19` a nivel localidad:

| Región | % con `P19` = provincia | % con `P19` = localidad | Sobrerrepresentación |
|---|---:|---:|---:|
| NOA | 14,5 | 5,1 | **2,88** |
| Cuyo | 13,6 | 4,9 | **2,79** |
| NEA | 12,7 | 4,8 | **2,67** |
| Patagonia | 5,5 | 2,9 | 1,88 |
| Pampeana | 53,6 | 64,2 | 0,84 |
| AMBA | 0,0 | 18,2 | 0,00 |

χ²(5) = 72,9; p < 10⁻¹³. La granularidad del `P19` no es independiente de la
región: las tres regiones del norte y Cuyo están sobrerrepresentadas entre 2,7 y
2,9 veces, y del AMBA no hay un solo caso.

**La cota.** Son 486 los excluidos por granularidad gruesa —255 con «Argentina»,
110 con una provincia, 121 con un departamento—, el 8,3% de la ventana.
Atribuyéndolos *todos* al tramo de menos de 10.000 habitantes, su tasa pasaría de
12,7 a 27,1 por 100.000 y el RR contra los grandes aglomerados, de 0,45 a
**0,96**.

Ese supuesto es inverosímil por construcción y no se propone como estimación: es
un techo. Pero deja una conclusión incómoda y honesta: **la exclusión por
granularidad tiene, ella sola, palanca suficiente para borrar el efecto
principal**. El valor real está en algún punto entre 0,45 y 0,96, y este trabajo
no puede decir dónde. Es la contracara, del lado del numerador, de la cota del
44,5% que se calculó para el artefacto de las maternidades, y las dos empujan en
la misma dirección.

---

### 3.7 La validación manual del `P19`

El bloqueante que este trabajo arrastró desde su primera revisión era que la tasa
de error del lugar de nacimiento nunca se había medido contra una fuente
independiente. Se midió.

**Diseño.** Muestra de 300 casos estratificada por tamaño de ciudad —metrópoli
contra el resto—, sorteada con semilla fija, mezclada, y presentada sin mostrar
ni el estrato ni el valor cargado, para que la búsqueda no estuviera condicionada
por ninguno de los dos. Se codificaron **133** casos.

**Fuente.** La Base de Datos del Fútbol Argentino (BDFA), consultada manualmente.
Es independiente del corpus que se valida: de 400 declaraciones `P19`
consultadas, 363 provienen de una importación desde Wikipedia y ninguna de BDFA.
La independencia además se verifica en el resultado —dos fuentes que copiaran una
de la otra no discreparían en el 6% de los casos ni lo harían en la dirección
sustantiva que se ve abajo.

**Resultado.** De los 133 codificados, 107 tenían lugar de nacimiento localizable
y 102 resolvieron a un tramo de tamaño.

|  | Wikidata: metrópoli | Wikidata: resto |
|---|---:|---:|
| **BDFA: metrópoli** | 46 | 3 |
| **BDFA: resto** | 3 | 50 |

**Acuerdo del 94,1%.** Y, lo que decide el asunto, **el error no es
diferencial**: 6,1% (IC 95% 1,3–16,9) entre los que Wikidata ubica en una
metrópoli y 5,7% (1,2–15,7) entre los que ubica fuera. OR del error 1,09
(0,21–5,66); Fisher exacto p = 1,00.

Eso importa porque un error *uniforme* no fabrica el gradiente: lo atenúa hacia
el nulo. Aplicando la matriz medida, el RR corregido pasa de 0,599 a **0,547**
(IC 95% por *bootstrap* 0,397–0,682): el efecto no solo sobrevive sino que se
refuerza levemente, que es exactamente lo que predice la desatenuación.

**Y queda por debajo del umbral que lo rompería.** El análisis de sensibilidad de
§3.9 sitúa el punto de quiebre en un 25% de mala clasificación en la dirección
del artefacto. El valor medido es 6,1%, y aun el extremo pesimista de su
intervalo —16,9%— queda por debajo de ese umbral.

**Limitaciones de la validación.** Codificó una sola persona, de modo que no hay
acuerdo entre codificadores que reportar; a cambio cada caso quedó con la URL de
su fuente y es verificable. Son 133 de los 300 previstos, así que los intervalos
son más anchos de lo diseñado. Y 26 casos no se pudieron verificar en ninguna
fuente: si el error se concentrara ahí, la medición lo subestimaría.

---

### 3.8 El «primer club» de H3: el problema era la cobertura, no la exactitud

La misma planilla pidió el club de debut, porque es la variable sobre la que se
apoya H3 entera. La validación separó dos cosas que conviene no confundir.

**Exactitud: nunca fue el problema.** De los 51 casos donde Wikidata tenía un
club cargado, coincide con BDFA en el 88,2% (76,1–95,6). Difiere más cuando el
primer vínculo aparece tarde: 90% de acuerdo si el registro empieza antes de los
21 años, 78% si empieza después.

**Cobertura: ahí estaba el problema.** De los 106 casos con club verificado,
**Wikidata no tenía ninguno cargado en 55 —el 52%**— y esa ausencia no era al
azar: seguía el nivel competitivo del jugador, que es el desenlace.

**Qué se hizo.** Las fichas de Wikipedia (§2.6) cubren 84 de los mismos 106
casos, con 82,1% de acierto (72,3–89,6). El número relevante no es ese sino el
cara a cara: en los 45 casos donde *ambas* fuentes tienen dato, las dos aciertan
**88,9%** (McNemar exacto p = 1,00). La ficha no es un dato de peor calidad;
cubre los casos que Wikidata deja afuera y acierta lo mismo donde compiten.
Además su error no depende del estrato de nacimiento (83,7% contra 80,5%, Fisher
p = 0,78), que es la condición para que no sesgue el contraste.

Sumadas, el club formador queda cargado en el 82,7% de la muestra y la cobertura
del estrato «resto» sube de 12,7% a 72,1%. **El efecto de haberlo corregido se ve
en los resultados**: la migración de H3 baja de 47,1% a 44,5% y el OR de 5,58 a
5,03, exactamente lo que predice haber estado midiendo sobre los que llegaron. El
hallazgo sobrevive; su magnitud estaba inflada.

**Lo que sigue abierto.** Las dos fuentes registran mayormente el debut
profesional y no las inferiores, así que el proxy sigue midiendo algo más tardío
que «dónde se formó». Eso no lo arregla la cobertura.

---

### 3.9 Cuánto tendría que fallar el dato para que el hallazgo se caiga

**Figura 33.** Las dos cotas anteriores —44,5% para el artefacto de maternidad,
0,45 → 0,96 para la granularidad— dicen hasta dónde *podría* llegar el sesgo,
pero no cuánto haría falta para que el resultado desaparezca. Esa es la pregunta
que calibra cuánto preocuparse, y se puede contestar sin medir nada.

El procedimiento es un análisis de sesgo cuantitativo. Se postula una matriz de
mala clasificación: dado que un jugador nació realmente en un lugar del estrato
*i*, ¿con qué probabilidad el `P19` lo ubica en el estrato *j*? Con esa matriz,
el vector de conteos reales sale de resolver **M**ᵀ**n**ᵣₑₐₗ = **n**ₒᵦₛ, y la
incertidumbre se propaga por *bootstrap*. Se barre el escenario que preocupa
—jugadores del interior registrados en la metrópoli— y se busca el punto en que
el intervalo del RR corregido toca el 1.

| % mal clasificado | RR corregido | IC 95% | ¿sigue ≠ 1? |
|---:|---:|---|---|
| 0% | 0,53 | 0,46–0,58 | sí |
| 10% | 0,64 | 0,54–0,74 | sí |
| 20% | 0,76 | 0,62–0,93 | sí |
| **25%** | **0,81** | **0,64–1,02** | **no** |
| 35% | 0,88 | 0,67–1,13 | no |
| 50% | 1,03 | 0,73–1,44 | no |

**El punto de quiebre está en el 25%.** Para que el hallazgo principal deje de
ser distinguible de la ausencia de efecto, **uno de cada cuatro** futbolistas
registrados en un aglomerado de más de 500.000 habitantes tendría que haber
nacido en realidad fuera de él.

Cómo leerlo. No es una estimación del error real —para eso está la validación
manual de §3.7— sino la calibración de cuánto error haría falta. Con un 10% de
mala clasificación el resultado apenas se mueve; recién a partir de un cuarto se
vuelve frágil. Puesto junto al 6,1% medido, el margen es amplio: el error real
está a un cuarto de distancia del que rompería el resultado.

---

### 3.10 Control positivo: el efecto de la edad relativa

**Figura 31.** El placebo de §3.14 muestra que el instrumento no inventa señal
donde no la hay. No muestra que sepa **recuperar** una señal que sí está, y esa
es la objeción que quedaría en pie contra un gradiente plano: que el corpus sea
demasiado ruidoso para detectar nada.

El *relative age effect* es el control positivo natural. Es el hallazgo más
replicado de la literatura sobre desarrollo deportivo: los nacidos justo después
de la fecha de corte de las categorías juveniles son mayores que sus compañeros
de camada y quedan sobrerrepresentados entre los profesionales. En Argentina la
AFA usa el año calendario, así que el corte es el 1 de enero.

| Trimestre de nacimiento | Futbolistas | % observado | % esperado | Obs./Esp. |
|---|---:|---:|---:|---:|
| Q1 (ene–mar) | 2.007 | 34,8 | 24,7 | **1,41** |
| Q2 (abr–jun) | 1.547 | 26,9 | 24,9 | 1,08 |
| Q3 (jul–sep) | 1.247 | 21,6 | 25,2 | 0,86 |
| Q4 (oct–dic) | 959 | 16,6 | 25,2 | **0,66** |

Razón Q1/Q4 = **2,09**; χ²(3) = 443,5; p < 10⁻⁹⁵; *w* = 0,28. El corpus recupera
el efecto con la magnitud que reporta la literatura y con la forma correcta:
caída monótona a lo largo del año, sin escalones.

Y cumple la predicción adicional de que el efecto se intensifica con el nivel
competitivo: la razón Q1/Q4 es 2,88 entre los jugadores de selección mayor, 2,46
en los de Primera argentina y 1,83 en el resto.

**Qué habilita esto.** El mismo pipeline, el mismo corpus y el mismo tipo de test
detectan sin dificultad un sesgo de selección deportiva conocido. El gradiente
plano por tamaño de ciudad por debajo de 10.000 habitantes no se explica,
entonces, por falta de potencia del instrumento.

Una salvedad sobre el denominador: la serie del DEIS es anual y no tiene apertura
mensual, de modo que el esperado se calculó proporcional a los días de cada
trimestre y no a los nacimientos reales de cada mes. La estacionalidad de los
nacimientos argentinos es de pocos puntos porcentuales y no puede producir una
razón de 2,09, pero el número exacto mejoraría con la apertura mensual.

---

### 3.11 Qué queda del tamaño al controlar por pobreza y por distancia

**Figura 29.** Hasta acá el único predictor del modelo fue el tamaño de la
ciudad. Eso deja sin responder la pregunta que importa: si el tamaño mide algo
propio o es un proxy de otra cosa. Se agregan las dos candidatas obvias.

**Distancia al club formador más cercano.** El universo de clubes no se define a
mano: son los 159 clubes argentinos geolocalizados que aparecen como primer club
de al menos un futbolista de la muestra. Para cada ciudad se calcula la distancia
haversine al más cercano (mediana nacional: 79 km). Es una medida cruda —no
distingue un club de Primera con pensión de uno de Federal A, ni tiene en cuenta
que la red cambió a lo largo de las cohortes— y hereda una circularidad: el
universo sale de los mismos datos que el numerador.

**Pobreza estructural.** El censo 2022 publica el NBI por hogar como variable
derivada. Se agrega a departamento como porcentaje de hogares con al menos una
necesidad básica insatisfecha (mediana 7,3%; de 2,6% en La Pampa a 14,2% en
Salta).

| Modelo | AIC | pseudo-R² | IRR (IC 95%) |
|---|---:|---:|---|
| 1. solo tamaño | 3.653,1 | 0,010 | tamaño 1,175 (1,114–1,240) |
| 2. solo distancia | 3.389,3 | 0,009 | distancia 0,825 (0,771–0,882) |
| **3. solo NBI** | **3.429,1** | **0,071** | NBI 0,843 (0,822–0,864) |
| 4. tamaño + distancia | 3.385,4 | 0,011 | tamaño 1,074; distancia 0,847 |
| **5. las tres** | **3.199,8** | **0,066** | tamaño 1,105 (1,042–1,172) |
|  |  |  | distancia 0,981 (0,909–1,059) |
|  |  |  | NBI 0,851 (0,828–0,873) |

Tres resultados, y dos incomodan a la interpretación que el trabajo venía
sosteniendo:

1. **La pobreza estructural es, de lejos, el mejor predictor.** Sola explica
   siete veces más variación que el tamaño (pseudo-R² 0,071 contra 0,010). Cada
   punto porcentual de NBI baja la producción un 15%.
2. **La distancia al club formador deja de importar cuando entra el NBI.** Por sí
   sola es fuerte (IRR 0,825; p < 10⁻⁷); con pobreza en el modelo, se apaga
   (IRR 0,981; p = 0,63). **Era en buena medida un proxy de pobreza**, no una
   medida de acceso. Es evidencia en contra de la lectura del §4.1, que atribuía
   el patrón a la distancia a la infraestructura formativa.
3. **El tamaño sobrevive**, atenuado: de 1,175 a 1,105. No es un proxy de ninguna
   de las dos, pero su efecto es todavía más chico de lo que ya era.

### 3.12 Dónde está la variación: entre departamentos o adentro

**Figura 30.** El pseudo-R² de 0,010 dice que el tamaño explica poco, pero no
dice dónde está lo que queda sin explicar. Esa es la pregunta relevante para un
trabajo cuyo producto principal es un mapa departamental.

Sobre los residuos de Pearson del modelo con las tres covariables se descompone
la variación entre la que separa a un departamento de otro y la que separa a dos
ciudades del mismo departamento. El resultado es **ICC = 0,17**: apenas el 17% de
la variación residual corresponde a diferencias entre departamentos, y el 83%
restante queda entre ciudades vecinas.

**Qué implica.** Dos ciudades del mismo departamento, del mismo tamaño y con la
misma pobreza producen cantidades muy distintas de futbolistas. El mapa
departamental —la **Figura 1**, que es la imagen más citable del trabajo— resume
mal el fenómeno: la unidad a la que el fenómeno ocurre es más chica que el
departamento, o directamente no es geográfica.

Dos salvedades. La descomposición se hace sobre residuos y no es el ICC de un
modelo mixto: no separa la varianza de muestreo de Poisson de la varianza real
entre departamentos, de modo que **sobreestima** el componente de adentro cuando
las ciudades son chicas. El 17% es entonces una cota inferior del agrupamiento
departamental. Y no se ajustó un GLMM propiamente dicho porque la implementación
disponible de Poisson con efectos aleatorios no admite *offset*, y sin la
exposición el modelo diverge.

---

### 3.13 Exploratorio: posición y región

**Estrictamente exploratorio.** De 24 contrastes, siete sobreviven a la
corrección de Benjamini-Hochberg. Seis involucran a las dos regiones con más
casos: el AMBA produce más defensores y menos mediocampistas de lo esperado, y la
región pampeana lo inverso. El séptimo es NEA × defensor, que queda justo del
lado de adentro (*p* corregido = 0,042) y conviene no leer como hallazgo: es el
contraste más débil de los que pasan, en la región con menos casos, dentro de un
análisis que el diseño declara exploratorio. **El mito de «las delanteras del
norte» no aparece**: ni NOA × delantero (*p* corregido = 0,098) ni NEA ×
delantero (0,540) sobreviven a la corrección.

---

### 3.14 Placebo: el mismo análisis en otros deportes

**Figura 28.** La objeción más difícil de contestar contra todo lo anterior no es
metodológica sino de interpretación: que lo que se mide no sea la geografía del
fútbol sino la del país —dónde hay clase media, dónde hay infraestructura
deportiva de cualquier tipo, dónde Wikipedia tiene editores—. Esa objeción se
contesta corriendo el mismo análisis sobre otro deporte.

Se repitió todo el pipeline sobre deportistas argentinos de básquet, rugby, vóley
y hockey: misma ventana de cohortes, mismos filtros de sexo y precisión de fecha,
misma cadena de geocoding, mismo denominador de nacidos vivos y mismos tramos.
Lo único que cambia es el deporte.

Las tasas no son comparables entre deportes —la cobertura de Wikidata es muy
distinta— pero la **forma** sí lo es. En el contraste que define el *birthplace
effect*, ciudades de 50.000 a 100.000 habitantes contra grandes aglomerados:

| Deporte | n (50–100k) | n (>500k) | RR | IC 95% |
|---|---:|---:|---:|---|
| **Básquet** | 39 | 176 | **1,95** | 1,38–2,76 |
| **Fútbol** | 275 | 3.343 | **0,72** | 0,64–0,82 |
| Vóley | 2 | 52 | 0,34 | 0,08–1,39 |
| Hockey | 2 | 33 | 0,53 | 0,13–2,22 |
| **Rugby** | 2 | 210 | **0,08** | 0,02–0,34 |
| *Fútbol femenino* | 12 | 144 | *0,73* | 0,41–1,32 |

**El básquet argentino tiene el *birthplace effect* clásico, con el pico
exactamente donde Côté et al. (2006) lo sitúan**, y sus intervalos no se tocan con
los del fútbol. Por observado sobre esperado, el básquet va 0,40 · 0,85 · **1,88**
· 1,60 · 0,96 a lo largo de los cinco tramos: una U invertida de manual. El
fútbol va 0,56 · 0,71 · 0,90 · 0,92 · 1,24, creciendo hacia la metrópoli. El
rugby está aún más concentrado que el fútbol y el hockey más todavía —el 83% de
los jugadores de hockey nace en el AMBA—, lo que es coherente con que sean
deportes de colegio privado metropolitano.

Por región el contraste es igual de nítido: el básquet produce 2,01 veces lo
esperado en la región pampeana y **0,56 en el AMBA**; el fútbol, 1,47 y 1,20.

**El fútbol femenino es el control interno del control.** No es un placebo —es el
mismo deporte— pero su infraestructura es otra: se profesionalizó en 2019, sus
clubes formadores son otros y su cobertura en Wikidata es mucho más reciente. Su
geografía es **indistinguible** de la del fútbol masculino: RR 0,73 (0,41–1,32)
contra 0,72, forma 0,51 · 0,59 · 0,97 · 0,79 · 1,32 contra 0,56 · 0,71 · 0,90 ·
0,92 · 1,24, y tests de homogeneidad que no rechazan (p = 0,76 por tramo, p = 0,74
por región; V = 0,018 y 0,022, tamaños de efecto que hacen informativo el no
rechazo pese a n = 213). Lo que separa los mapas es el deporte, no la estructura
profesional que lo sostiene ni la época en que se construyó.

Los cuatro placebos difieren significativamente del fútbol en su distribución
regional (χ² de homogeneidad, p < 0,001 en los cuatro). **Ningún artefacto de
medición compartido —el registro de nacimientos, la imputación del denominador,
la cobertura de Wikipedia, el nivel socioeconómico del departamento— puede
producir mapas opuestos para deportes distintos medidos con el mismo
instrumento.** El patrón del fútbol es del fútbol.

*Limitación:* vóley (n=70) y hockey (n=36) tienen muestras demasiado chicas para
leer sus tramos por separado; entran en el contraste binario y en las tablas, no
en la lectura de la forma. Básquet (356) y rugby (243) sí la sostienen.

## 4. Discusión

### 4.1 Por qué el efecto está invertido

El *birthplace effect* clásico se apoya en un supuesto implícito: que la
infraestructura de desarrollo deportivo está razonablemente distribuida, de modo
que lo que diferencia a los lugares es la calidad del entorno de juego informal.
Bajo ese supuesto la ciudad mediana gana: tiene espacio y tiene liga.

En Argentina ese supuesto no se cumple. La formación está concentrada: diez
clubes concentran el 37,6% de la formación registrada del país, y nueve de ellos
están en el AMBA, el Gran Rosario o el Gran La Plata —el décimo, Unión, en el
Gran Santa Fe—. La interpretación natural —y la que sostenían las versiones
anteriores de este trabajo— era que el lugar de nacimiento no mide acá la calidad
del entorno formativo sino **la distancia a la infraestructura formativa**, y que
esa distancia opera como filtro de acceso.

**Medida, esa interpretación no se sostiene.** Cuando la distancia al club
formador más cercano entra al modelo junto con la pobreza estructural del
departamento, su efecto se apaga por completo (IRR 0,981; p = 0,63; §3.11). Sola
parecía fuerte porque los lugares lejos de un club son también los lugares
pobres. Lo que el modelo señala como predictor dominante no es la geografía de
los clubes sino **el NBI**: siete veces más capacidad explicativa que el tamaño
de la ciudad, y un 15% menos de producción por cada punto porcentual de hogares
con necesidades básicas insatisfechas.

Eso reencuadra el hallazgo. El mapa de producción de futbolistas se parece mucho
más al mapa de la pobreza estructural argentina que al mapa de los clubes. La
explicación más simple compatible con estos datos no es «nacer lejos de un club
es una desventaja» sino «nacer pobre lo es», y las regiones que producen un
cuarto de lo esperado son las mismas que encabezan el NBI. Sigue siendo una
asociación sin identificación causal —el NBI departamental es un agregado y opera
acá como control, no como mecanismo estimado— pero es una asociación que existe,
frente a una que se desvanece al controlarla.

Los controles disponibles son dos y no agotan la lista: falta la densidad de
ligas locales, la existencia de pensión en el club y cualquier medida de la red
formativa vigente en la época de cada cohorte —la distancia se calcula contra los
clubes que formaron a alguien en toda la ventana, no contra los que existían el
año en que cada jugador cumplió quince—. Con esas ausencias declaradas, las
asociaciones que siguen son observacionales.

**El placebo acota qué clase de explicación puede servir (§3.14).** Cualquier
mecanismo que se proponga tiene que explicar por qué el básquet argentino, en el
mismo país y las mismas cohortes, tiene el efecto clásico y el fútbol su inverso.
Eso descarta de entrada las explicaciones que no distinguen deportes —el registro
de nacimientos, la estructura urbana, el nivel socioeconómico, la cobertura de
Wikipedia— y deja en pie solo las que dependen de cómo está organizado cada
deporte. La centralización de la formación es una de esas: el básquet argentino
tiene ligas federales fuertes y clubes formadores repartidos por el interior,
mientras que casi el 38% de la formación futbolística registrada está en diez
clubes del AMBA, Rosario, La Plata y Santa Fe. **Sigue siendo una interpretación** —la
organización comparada de las dos estructuras formativas no se mide acá— pero ya
no compite con las explicaciones genéricas: esas quedaron descartadas por diseño.

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
  fuera de un gran aglomerado llegan a la Mayor el 41,1% de las veces contra el
  28,1%.

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
   padrón que incluye 258 «localidades» de menos de 100 habitantes, entre ellas
   `ZONA RURAL`. Sean o no artefacto, no son la categoría «small city» de Côté et
   al. (2006), que arranca en 1.000 habitantes con localidades urbanas.
2. **El reparto intraprovincial es un supuesto con sesgo direccional.** No solo
   es estimado: su error es del +19% en el decil de departamentos más chicos y
   nulo en el más grande (§2.1, Figura 19), y empuja en la misma dirección que el
   hallazgo. Corregirlo llevaría el RR de 0,45 a ~0,53.
3. **El reparto de los partidos divididos es un segundo supuesto.** Para bajar de
   un partido que ya no existe —General Sarmiento, Morón antes de 1994— a los
   partidos actuales, se reparte su población según la proporción que tienen los
   sucesores en el primer censo en que aparecen separados, lo que supone que esa
   proporción describe la que tenían antes de dividirse. Afecta a 44
   departamentos; el criterio de cada equivalencia está en
   `data/reference/crosswalk_departamentos.csv`.
4. **Cobertura de Wikidata.** Es un corpus de notabilidad, no un registro. La
   tasa de error del `P19` **sí quedó medida** en esta versión, sobre 133 casos
   verificados a mano contra la Base de Datos del Fútbol Argentino: 94,1% de
   acuerdo, error no diferencial (§3.7). La verificación fue manual porque el
   `robots.txt` de BDFA bloquea agentes automáticos; el sitio se puede leer en un
   navegador, que es como se hizo. Lo que sigue abierto es la **cobertura**: son
   133 de los 300 casos previstos, así que los intervalos son más anchos de lo
   diseñado, y la cobertura varía al doble entre cohortes (la de 1975–1979 rinde
   el 47,5% del pico de 1985–1989).
5. **La selección por el desenlace en H3 quedó muy reducida, no eliminada.** Con
   el club formador saliendo solo de Wikidata, la cobertura iba del 99,2% en
   jugadores de selección al 12,7% en el resto y H3 describía a los que llegaron
   lejos. Sumadas las fichas de Wikipedia (§2.6) el piso sube a 72,1%, la muestra
   de 1.923 a 3.879 casos y la cobertura por estrato de nacimiento queda plana.
   **El efecto de haberlo corregido se ve en los resultados**: la migración baja
   de 47,1% a 44,5% y el OR de 5,58 a 5,03, que es la dirección que predice haber
   estado midiendo sobre los seleccionados. Queda un 17,3% sin club, concentrado
   en los menos notables, así que los números siguen siendo probablemente cota
   superior. Ninguna otra conclusión del trabajo se apoya en H3.
6. **La comparación de H3 con la población general no es estrictamente
   comparable**: 44,5% (futbolistas, nacimiento → primer club, alrededor de los
   18 años) contra 13,8% (toda la población, todas las edades, nacimiento →
   residencia 2022). La variable `P14` del censo no está cruzada con edad, así
   que la comparación no se puede acotar a las mismas cohortes.
7. **Controles parciales.** Hay dos covariables —pobreza estructural y distancia
   al club formador más cercano (§3.11)— y faltan las demás: densidad de ligas
   locales, existencia de pensión en el club y cualquier medida de la red
   formativa vigente en la época de cada cohorte. La distancia, además, se
   calcula contra los clubes que formaron a alguien en toda la ventana y no
   contra los que existían el año en que cada jugador cumplió quince. El NBI
   departamental resultó el predictor dominante, pero es un agregado y opera como
   control, no como mecanismo estimado: la versión seria necesita el NBI a nivel
   de la localidad. El trabajo sigue siendo descriptivo y las lecturas causales
   de §4.1 y §4.4 son interpretaciones, no estimaciones.
8. **Tamaño de efecto chico donde se lo mide de forma continua.** El tamaño de la
   ciudad explica el 1% de la variación entre ciudades (pseudo-R² = 0,010).
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
frecuencia (OR 1,78; p = 0,027; sin cambios al controlar por cohorte). Es un
contraste dentro de un grupo observado, sin denominador estimado. Si el acceso
midiera talento, la tasa de conversión debería ser igual en los dos grupos; no lo
es. **Eso es evidencia de que el filtro de acceso está dejando afuera jugadores
que habrían rendido.**

Para quien tiene que decidir dónde poner un centro de detección, la implicancia es
concreta y no depende de ninguna de las limitaciones de §4.3: **un juvenil del
interior es, en promedio, mejor apuesta que uno del AMBA con el mismo nivel
alcanzado.** Con 95 casos fuera del AMBA el intervalo es ancho (1,09–2,93) y
merece confirmarse con el padrón real de convocatorias de AFA, que existe y no es
público.

**Lo que el dato solo sugiere.** Que las regiones que producen un cuarto de lo
esperado sean «reservas desaprovechadas» requiere suponer que el talento latente
se distribuye parejo entre regiones —un supuesto razonable pero no testeado acá—.
Y la retención del 11,2% del NEA sale de la submuestra sesgada de H3. La dirección
del argumento es plausible; su magnitud, no está establecida.

Y una advertencia metodológica que sí se sostiene sola: **cualquier métrica de
producción basada en el lugar de nacimiento le atribuye al AMBA jugadores que el
AMBA absorbió, no formó** —y, en la medida en que el parto ocurre en la cabecera,
también le atribuye a las ciudades chicos que nacieron ahí de casualidad.

### 4.5 Qué haría falta para cerrar el argumento

En orden de prioridad:

1. **Completar la validación del `P19`** hasta los 300 casos previstos. Los
   primeros 133 ya están (§3.7) y dan un error del 5,9% no diferencial, pero con
   intervalos más anchos de lo diseñado; llegar a 300 los cierra. El diseño y la
   maquinaria están construidos (`docs/plan-validacion-p19.md`): 300 casos, 150
   por brazo, muestra sorteada con semilla fija, planillas ciegas al estrato y al
   valor cargado, dos codificadores y adjudicación de desacuerdos. Detecta una
   diferencia de diez puntos en la tasa de error y estima la matriz de mala
   clasificación con la precisión necesaria para corregir, no solo para acotar.
   Falta únicamente el juicio humano.

   Hay una restricción que condiciona el resto: **el `P19` sale de Wikipedia**.
   De 400 declaraciones consultadas, 363 tienen como referencia «importado de
   Wikipedia» en algún idioma y solo 3 una fuente externa. Wikipedia no puede ser
   entonces el patrón de oro, porque es el origen del dato.

   Y no hay ninguna fuente argentina estructurada que pueda tomar su lugar por
   vía automática. Se revisó una por una: **BDFA** bloquea en su `robots.txt` los
   agentes automatizados y los *endpoints* de consulta de jugadores;
   **Transfermarkt** permite las rutas de ficha en su `robots.txt` pero sus
   términos de uso (§11) prohíben expresamente el acceso mediante «bots, spiders,
   screen scraping u otros procesos automatizados»; y el sitio de la **AFA** sí
   admite el rastreo —su `robots.txt` solo excluye `/cache/`— pero no publica
   fichas con lugar de nacimiento. Por eso la verificación es necesariamente
   manual, y por eso este hueco sigue abierto en la literatura.
2. **Bajar el análisis a la unidad en la que el fenómeno ocurre.** El 83% de la
   variación residual está entre ciudades del mismo departamento (§3.12), así que
   el nivel departamental es demasiado grueso. Requiere denominadores por
   localidad que hoy son estimados en dos pasos, y es el cambio que más mejoraría
   el trabajo después de validar el `P19`.
3. **Perseguir la pista socioeconómica, que es la que quedó abierta.** El NBI
   departamental resultó el predictor dominante, pero es un agregado y opera como
   control, no como mecanismo. La versión seria necesita el NBI a nivel de radio
   censal —que el censo publica— cruzado con el lugar de nacimiento, y alguna
   medida de la red formativa vigente por cohorte en lugar de una distancia
   calculada sobre toda la ventana.
4. **Un GLMM propiamente dicho** en lugar de la descomposición sobre residuos,
   para separar la varianza de muestreo de Poisson de la varianza real entre
   departamentos. Requiere una implementación de Poisson con efectos aleatorios
   que admita *offset*, que statsmodels no tiene.
5. **Publicar el volcado crudo de Wikidata** con DOI, sin lo cual la reproducción
   es parcial (§6).

---

## 5. Conclusión

Este trabajo se propuso probar el folklore del «crack del interior» con el método
que la literatura internacional usa para el *birthplace effect*, y con un
denominador mejor que el que esa literatura suele emplear: los nacidos vivos de
cada cohorte en cada lugar, en vez de la población censada décadas después.

**El folklore no se sostiene, pero el hallazgo tiene menos forma de la que
parecía.** Los futbolistas argentinos no nacen desproporcionadamente en ciudades
chicas y medianas: nacen desproporcionadamente en los grandes aglomerados y en un
corredor que va del AMBA a Santa Fe. Ahora bien, lo que hay no es un gradiente
invertido sino un **contraste binario** entre las metrópolis y todo lo demás: por
debajo de los 10.000 habitantes no hay ninguna tendencia ordenada, el tamaño de
la ciudad explica el 1% de la variación entre ciudades, y dentro de la selección
los cuatro tramos no metropolitanos son indistinguibles entre sí. Describir el
resultado como «el efecto invertido» sugiere una pendiente en la otra dirección
que los datos no muestran.

**Que el patrón sea del fútbol y no del país está bien establecido.** El mismo
pipeline, sobre el mismo corpus, encuentra el efecto clásico en el básquet
argentino y lo contrario en el rugby. Ningún artefacto de medición compartido
produce mapas opuestos para deportes distintos medidos con el mismo instrumento.
Y el control positivo de la edad relativa muestra que el instrumento recupera
sesgos de selección deportiva cuando existen.

**Lo que el patrón parece medir no es la geografía de los clubes sino la
pobreza.** Con covariables, la distancia al club formador más cercano —que este
trabajo venía proponiendo como explicación— se apaga por completo al entrar el
NBI departamental, mientras que el NBI queda como el predictor dominante, con
siete veces la capacidad explicativa del tamaño de la ciudad. El mapa de
producción de futbolistas se parece más al mapa de la pobreza estructural
argentina que al de la infraestructura formativa. Y la unidad en la que el
fenómeno ocurre es más chica que el departamento: el 83% de la variación residual
separa a ciudades vecinas, no a departamentos, de modo que el mapa departamental
—la imagen más citable del trabajo— es también su resumen más flojo.

**Lo que queda sin cerrar es la medición del lugar de nacimiento, no el
análisis.** Dos sesgos independientes empujan en la dirección del hallazgo y
ninguno está estimado, solo acotado: el registro del parto en la ciudad cabecera
—cota del 44,5% del déficit del interior— y la granularidad diferencial del
`P19`, que excluye del análisis a jugadores del norte y de Cuyo a casi tres veces
la tasa del resto y cuya cota, sola, alcanza para llevar el RR de 0,45 a 0,96. El
efecto real está dentro de esas cotas y este trabajo no puede decir dónde
—aunque sí puede decir cuánto haría falta: para que el hallazgo deje de ser
distinguible del nulo, uno de cada cuatro futbolistas registrados en un gran
aglomerado tendría que haber nacido fuera de él (§3.9)—. Y para la primera de las
dos cotas —la del registro del parto— ahora hay una medición: sobre 133 casos
verificados contra una fuente independiente, el error del `P19` es del 5,9% y no
depende del tamaño de la ciudad (§3.7), muy por debajo del 25% que haría falta
para tumbar el resultado. Con eso, el hallazgo pasa de plausible a razonablemente
establecido; lo que queda es completar la muestra hasta los 300 casos previstos y
acotar la granularidad con el mismo método.

**Para quien detecta talento**, la lectura defendible es más modesta que la
inicial: no hay evidencia de que los pueblos produzcan más futbolistas por
nacido, sí de que las regiones del norte producen entre un cuarto y un tercio de
lo que les correspondería, y el indicio —frágil, dependiente de un solo estrato—
de que el juvenil que llega desde el interior convierte mejor. Esto último merece
confirmarse con el padrón real de convocatorias de la AFA, que existe y no es
público, y sería el aporte más útil que el trabajo podría hacer.

---

## 6. Reproducibilidad

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
