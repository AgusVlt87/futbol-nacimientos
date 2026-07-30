# ¿De dónde salen los futbolistas argentinos?

### Geografía del nacimiento y de la formación en el fútbol argentino, cohortes 1970–2000

*Análisis reproducible sobre Wikidata y el Censo Nacional 2022 del INDEC.
Snapshot de Wikidata: 30 de julio de 2026.*

---

## Resumen

Se analiza el lugar de nacimiento de 5.451 futbolistas profesionales argentinos
nacidos entre 1970 y 2000, contra un denominador poblacional emparejado por
cohorte construido con los microdatos del Censo Nacional 2022. Se obtienen tres
resultados.

**Primero: el *birthplace effect* clásico no aparece en Argentina, y lo que
aparece es su inverso.** La producción per cápita crece de forma monótona con el
tamaño de la ciudad de nacimiento, de 17,5 futbolistas por cada 100.000
habitantes de la cohorte en localidades de menos de 10.000 habitantes a 30,5 en
aglomerados de más de 500.000 (RR 0,57; IC 95% 0,52–0,63). El término cuadrático
de un modelo binomial negativo no aporta ajuste: no hay pico en las ciudades
medianas.

**Segundo: el mapa federal no separa capital de interior, sino un corredor
pampeano del resto del país.** Santa Fe produce 2,2 veces lo que le
correspondería por población y CABA 2,6; el NOA produce un tercio de lo
esperado. La región pampeana (36,2 por 100.000) supera al AMBA (31,9) y triplica
al NOA (10,7).

**Tercero, y es el hallazgo central: la formación está mucho más concentrada que
el nacimiento.** El 46,6% de los futbolistas se forma en una provincia distinta
de aquella en la que nació, contra el 13,8% de la población general que reside
fuera de su provincia de nacimiento (OR 5,47; IC 95% 5,02–5,96). Entre los
nacidos en pueblos de menos de 10.000 habitantes, el 94,6% se forma en otro
departamento, a una mediana de 282 km. El NEA retiene al 11,2% de los
futbolistas que nacen en su territorio; el AMBA, al 91,9%.

El estudio replica por primera vez, con método y baseline poblacional, un
fenómeno sobre el que en Argentina solo había descripción periodística.

---

## 1. Introducción

### 1.1 El *birthplace effect*

El *birthplace effect* —también llamado *place of early development effect*— es
uno de los hallazgos más replicados en la investigación sobre desarrollo
deportivo. Côté y colegas (2006) documentaron que las ciudades chicas y medianas
producen desproporcionadamente más atletas de elite que las grandes urbes y que
las zonas rurales, con un óptimo típicamente situado entre los 50.000 y los
100.000 habitantes. La explicación habitual combina tres mecanismos: espacio
físico y seguridad para el juego libre, densidad social suficiente para sostener
competencia organizada pero no tanta como para generar barreras de acceso, y
relaciones entrenador-jugador más estables.

El fenómeno se ha estudiado sobre todo en Norteamérica y Europa, con réplicas
para el fútbol en varios países y una revisión sistemática específica de la
disciplina.

### 1.2 El caso argentino y el vacío que llena este trabajo

Argentina es un caso de interés obvio: exporta futbolistas en volumen y tiene un
relato nacional muy establecido sobre su origen. El «crack del interior», el
potrero, el pueblo chico que da campeones del mundo —Gualeguay, 44.000
habitantes, dos— describe con precisión el patrón que el *birthplace effect*
predice.

Ese relato, sin embargo, nunca fue puesto a prueba. Lo que existe es periodismo
descriptivo: listas de jugadores por provincia, sin denominador poblacional y
por lo tanto sin capacidad de distinguir «produce muchos» de «vive mucha gente».
Este trabajo es, hasta donde alcanza nuestra búsqueda, el primer análisis
estadístico del *birthplace effect* en el fútbol argentino.

### 1.3 Hipótesis

- **H1.** Los futbolistas están sobrerrepresentados entre los nacidos en
  ciudades chicas y medianas respecto de lo esperado por la distribución
  poblacional.
- **H2.** El interior produce más futbolistas per cápita que el AMBA.
- **H3.** Existe una migración sistemática entre el lugar de nacimiento y el
  club formador.
- **H4.** El efecto se intensifica con el nivel competitivo alcanzado.
- **Exploratorio.** Asociación entre posición y región de nacimiento.

---

## 2. Métodos

### 2.1 Muestra

**Fuente.** Wikidata, vía SPARQL sobre el endpoint público, paginado por año de
nacimiento. Snapshot del 30 de julio de 2026, fechado en
`data/raw/wikidata/_snapshot.json`. La ocupación se consultó expandiendo
subclases (`wdt:P106/wdt:P279* wd:Q937857`) y la pertenencia por ciudadanía
argentina (`wdt:P27 wd:Q414`).

**Construcción de la muestra** (tabla `qa_players_filtros.csv`):

| Paso | n | Descartados |
|---|---:|---:|
| Futbolistas argentinos en Wikidata | 9.115 | — |
| Con precisión de fecha de nacimiento ≥ año | 8.976 | 139 |
| Muestra masculina | 8.649 | 327 |
| Con lugar de nacimiento (`P19`) | 8.290 | 359 |
| Con lugar resuelto dentro de Argentina | 7.711 | 579 |
| **Cohortes 1970–2000 (muestra de análisis)** | **5.451** | 2.260 |

La muestra se restringe a varones porque la literatura del *birthplace effect*
está construida casi enteramente sobre fútbol masculino y porque la muestra
femenina de Wikidata (348 jugadoras) tiene una cobertura de naturaleza
suficientemente distinta como para que mezclarlas confunda más de lo que aporta.

**Ventana de cohortes.** El límite lo impone el denominador, no la fuente. El
denominador principal cuenta a las personas que en 2022 tenían la edad
correspondiente a cada cohorte de nacimiento: hacia atrás, la mortalidad y la
emigración erosionan ese conteo; hacia adelante, las carreras están censuradas a
derecha. La ventana 1970–2000 corresponde a personas de 22 a 52 años en 2022.

### 2.2 Resolución geográfica

Los nombres de lugares argentinos en Wikidata son inconsistentes: hay homónimos
entre provincias (cuatro localidades se llaman Santa Rosa), variantes
ortográficas, y entidades que son provincias o partidos y no ciudades. Resolver
por *string* garantiza error.

**El lugar de nacimiento se resuelve por coordenada** (`P625`) contra la API
Georef del Estado argentino, que devuelve el departamento y la provincia
oficiales. El nombre se usa solo como chequeo cruzado al asignar la localidad
censal. Resultado (tabla `qa_geocoding.csv`): de 1.084 lugares distintos, 624 se
asignaron con coincidencia de nombre **y** proximidad, 167 solo por proximidad
(mediana: 2,2 km) y 19 corresponden a barrios de CABA.

**La granularidad de cada entidad se clasifica antes de usarla.** Veinte lugares
de nacimiento son provincias, 83 son departamentos o partidos, dos son regiones
(«Cuyo», «Gran Buenos Aires») y cuatro son países. El centroide de una provincia
no ubica a nadie: esas entidades se resuelven solo hasta el nivel que les
corresponde y quedan fuera del análisis por localidad. El caso más consecuente
es la entidad «Argentina», que 255 jugadores tienen como lugar de nacimiento;
su centroide cae en el departamento Presidente Roque Sáenz Peña de Córdoba y,
sin este filtro, convertía a General Levalle —5.674 habitantes— en la tercera
cuna de futbolistas del país.

**CABA se trata como una unidad** y no como sus 15 comunas: asignar a un
jugador la comuna donde cae el centroide de «Buenos Aires» no significa nada.

### 2.3 Denominador poblacional

El corazón del método: nadie está sobrerrepresentado sin comparar contra cuánta
gente vive en cada lugar.

**Fuente.** Microdatos tabulados por radio censal del Censo Nacional de
Población, Hogares y Viviendas 2022 (INDEC), publicados en `datos.gob.ar`. El
radio censal es la unidad atómica; de él se derivan departamento, localidad
censal, aglomerado urbano y condición urbano/rural. Los totales reproducen las
cifras oficiales publicadas.

**Baseline principal: `census_cohort`.** Para la cohorte nacida en el año *Y*,
el denominador es la población de edad (2022 − *Y*) en la unidad geográfica.
Esto controla la estructura etaria, que difiere fuertemente entre el AMBA y el
NOA y que un denominador de población total confundiría con producción de
talento.

**«Tamaño de ciudad» = aglomerado urbano cuando existe.** Lanús no es una ciudad
de 200.000 habitantes: es una porción de un conurbano de 16,2 millones, y para
el *birthplace effect* eso es lo que importa. Se usa la definición de aglomerado
del propio INDEC. Se reporta también la variante con la localidad censal aislada
como control (§3.1).

**Baselines alternativos.** Se reportan cuatro más, todos en
`outputs/tables/`: población total en los censos 1991, 2001, 2010 y 2022, y
—solo a nivel provincial— el conteo de personas censadas en 2022 que declararon
haber **nacido** en cada provincia (variable `P14`). Este último es
conceptualmente superior para H2 porque cuenta nacimientos y no residencia, de
modo que la migración interna no lo distorsiona.

### 2.4 Estadística

Chi-cuadrado de bondad de ajuste contra la distribución poblacional real —nunca
uniforme—, con Cohen's *w* y Cramér's *V*. Tasas por 100.000 habitantes con
intervalo exacto de Poisson (Garwood), elegido porque muchos departamentos
tienen cero, uno o dos jugadores y ahí la aproximación normal produce
intervalos que incluyen valores negativos. Razones de tasas e *odds ratios* con
IC 95% (Woolf, con corrección Haldane-Anscombe ante celdas vacías). Regresión
binomial negativa con *offset* logarítmico de la población. Corrección de
Benjamini-Hochberg en los cruces exploratorios.

Regla transversal: ningún hallazgo se apoya solo en un p-valor.

### 2.5 La limitación central: nacer ≠ formarse

Wikidata da el lugar de **nacimiento**, no el de **desarrollo**. La literatura
reciente sugiere que el lugar de nacimiento por sí solo es un predictor flojo y
que lo que pesa es la transición entre dónde se nace y dónde se crece
deportivamente. El análisis base (H1, H2) es la metodología clásica del campo y
es válido, pero mide una cosa acotada.

Para H3 se construyó un proxy del club formador: el vínculo jugador-club (`P54`)
con la fecha de inicio (`P580`) más temprana registrada, excluyendo selecciones.
**Es un proxy y así debe leerse.** Wikidata suele omitir las divisiones
inferiores, con lo cual el primer club listado es muchas veces el de debut
profesional y no el de formación; y la cobertura del dato es muy desigual por
nivel: 99,4% entre los jugadores de selección mayor contra 14,4% en el resto de
la muestra (tabla `qa_niveles_y_primer_club.csv`). Los resultados de H3 se
apoyan en 2.088 jugadores con origen y club formador ubicados en Argentina.

---

## 3. Resultados

### 3.1 H1 — El efecto aparece invertido

**Figura 4** (`fig04_tasa_por_tramo`), **Figura 7** (`fig07_scatter_tamano_tasa`),
tablas `h1_tramos_principal.csv` y `h1_tramos_cote2006.csv`.

| Tamaño de la ciudad | Futbolistas | Población de la cohorte | Tasa /100.000 | IC 95% | RR vs >500k |
|---|---:|---:|---:|---|---|
| <10k | 406 | 2.321.573 | 17,5 | 15,8–19,3 | 0,57 (0,52–0,63) |
| 10–50k | 558 | 2.805.133 | 19,9 | 18,3–21,6 | 0,65 (0,60–0,71) |
| 50–100k | 276 | 1.142.199 | 24,2 | 21,4–27,2 | 0,79 (0,70–0,90) |
| 100–500k | 625 | 2.594.808 | 24,1 | 22,2–26,1 | 0,79 (0,72–0,86) |
| **>500k** | **3.326** | **10.895.497** | **30,5** | **29,5–31,6** | 1,00 |

χ²(4) = 193,4; p < 10⁻⁴⁰; *w* = 0,19; n = 5.191.

La tasa crece de forma monótona con el tamaño. **El tramo de 50.000 a 100.000
habitantes —el óptimo que predice la literatura— no muestra ningún pico**: está
por debajo del tramo mayor y no se distingue del de 100.000 a 500.000.

Con los cortes de Côté et al. (2006), para poder comparar con la literatura, el
resultado es el mismo: de 12,1 por 100.000 en localidades de menos de 1.000
habitantes a 30,5 en las de más de 500.000, con un único quiebre menor en el
tramo 250–500k (χ²(6) = 206,6; *w* = 0,20).

**Regresión** (`regresion_tamano_ciudad.csv`). Modelo binomial negativo sobre
3.476 ciudades con *offset* logarítmico de la población de la cohorte: cada
*e-fold* de tamaño multiplica la tasa por 1,118 (IC 95% 1,061–1,179; p < 0,0001).
Al agregar el término cuadrático, **ni el término lineal ni el cuadrático
resultan significativos y el AIC empeora** (3.656,9 contra 3.655,0). No hay
curva en U invertida que ajustar.

**Robustez.** El patrón se sostiene en las tres variantes probadas:

| Variante | RR <10k vs >500k | IC 95% |
|---|---|---|
| Principal (aglomerado urbano) | 0,57 | 0,52–0,63 |
| Unidad = localidad censal aislada | 0,39 | 0,35–0,44 |
| Cohortes 1970–1984 | 0,53 | 0,44–0,64 |
| Cohortes 1985–2000 | 0,59 | 0,52–0,67 |

La variante por localidad aislada acentúa el efecto, lo cual es esperable: al
partir el conurbano en piezas, muchos nacidos en el AMBA pasan al tramo
100–500k. La comparación entre cohortes muestra una atenuación leve en la más
joven cuyo origen no podemos atribuir con los datos disponibles; el gradiente no
se invierte en ninguna.

### 3.2 H2 — Un corredor pampeano, no un interior

**Figura 1** (`fig01_mapa_departamentos_tasa`), **Figura 3**
(`fig03_mapa_provincias_obs_esp`), **Figura 5** (`fig05_tasa_por_region`),
**Figura 6** (`fig06_cartograma_provincias`).

Por región (χ²(5) = 762,4; *w* = 0,37):

| Región | Futbolistas | Tasa /100.000 | IC 95% | RR vs AMBA |
|---|---:|---:|---|---|
| Pampeana | 2.612 | 36,2 | 34,8–37,6 | 1,13 |
| AMBA | 1.862 | 31,9 | 30,5–33,4 | 1,00 |
| Cuyo | 283 | 19,3 | 17,1–21,7 | 0,60 |
| NEA | 262 | 14,2 | 12,6–16,1 | 0,45 |
| Patagonia | 154 | 12,9 | 10,9–15,1 | 0,40 |
| NOA | 278 | 10,7 | 9,5–12,1 | 0,34 |

**H2, tal como estaba formulada, no se sostiene.** Tomado en bloque, el interior
produce *menos* que el AMBA: 25,1 contra 31,9 por 100.000 (RR 0,79; IC 95%
0,74–0,83). Lo que sí ocurre es que **una parte del interior —la pampeana— supera
al AMBA**, mientras el NOA, el NEA y la Patagonia producen entre un tercio y
menos de la mitad de lo esperado.

Por provincia, los extremos son nítidos:

| | Provincia | Futbolistas | Tasa /100.000 | Obs./Esp. |
|---|---|---:|---:|---:|
| 1 | CABA | 1.009 | 70,8 | 2,62 |
| 2 | Santa Fe | 938 | 60,2 | 2,22 |
| 3 | Córdoba | 565 | 33,6 | 1,24 |
| 4 | La Pampa | 46 | 29,4 | 1,09 |
| 5 | Entre Ríos | 180 | 29,2 | 1,08 |
| … | | | | |
| 22 | La Rioja | 14 | 7,9 | 0,29 |
| 23 | Salta | 47 | 7,5 | 0,28 |
| 24 | Catamarca | 14 | 7,2 | 0,27 |

La estructura del mapa es un eje que va de Rosario a Santa Fe capital y se
extiende hacia el sur de Córdoba y el norte de Buenos Aires. Los departamentos
de mayor producción con al menos 30 jugadores lo confirman: Marcos Juárez
(Córdoba) 102,2 por 100.000, Castellanos (Santa Fe) 90,0, Caseros (Santa Fe)
89,9, La Capital (Santa Fe) 74,8, General López (Santa Fe) 74,4.

**El orden no depende del baseline.** Se probaron cinco denominadores distintos
y CABA y Santa Fe encabezan en todos. Con el baseline de población *nacida* en
cada provincia —el conceptualmente correcto, porque no lo afecta la migración—
CABA marca 2,65 y Santa Fe 2,19. Con la población total del censo de 1991,
próxima al momento de nacimiento de la cohorte, CABA 2,04 y Santa Fe 2,01.

### 3.3 H3 — La formación está mucho más concentrada que el nacimiento

**Figura 8** (`fig08_flujos_nacimiento_club`), **Figura 9**
(`fig09_migracion_por_tamano`).

Este es el resultado con más consecuencias.

**Comparado con la población general, el futbolista migra cinco veces más.**

| Grupo | n | Fuera de su provincia |
|---|---:|---:|
| Futbolistas (nacimiento → club formador) | 2.088 | **46,6%** |
| Población general (nacimiento → residencia, Censo 2022) | 42.640.509 | 13,8% |

OR 5,47 (IC 95% 5,02–5,96). El punto de comparación es lo que vuelve
interpretable el número: sin saber que apenas el 13,8% de los argentinos vive
fuera de su provincia de nacimiento, un 46,6% no dice nada.

**El gradiente por origen es el hallazgo dentro del hallazgo:**

| Tamaño de la ciudad de nacimiento | n | Cambia de departamento | Cambia de provincia | Distancia mediana al club |
|---|---:|---:|---:|---:|
| <10k | 148 | 94,6% | 58,8% | 282 km |
| 10–50k | 229 | 97,8% | 64,6% | 310 km |
| 50–100k | 110 | 86,4% | 63,6% | 262 km |
| 100–500k | 243 | 86,0% | 66,7% | 470 km |
| >500k | 1.300 | 51,3% | 36,5% | **7 km** |

Nacer en una ciudad grande significa formarse a siete kilómetros de casa. Nacer
en un pueblo significa, con probabilidad de 19 sobre 20, irse.

**Por región de origen**, la asimetría es estructural:

| Región | n | Cambia de provincia | Retención | Saldo neto |
|---|---:|---:|---:|---:|
| AMBA | 740 | 35,7% | 91,9% | **+621** |
| Pampeana | 1.021 | 44,6% | 50,9% | −408 |
| Cuyo | 85 | 55,3% | 47,1% | −33 |
| Patagonia | 66 | 77,3% | 28,8% | −43 |
| NOA | 87 | 81,6% | 25,3% | −60 |
| NEA | 89 | 95,5% | 11,2% | −77 |

El 70,8% de los futbolistas nacidos en el NEA se forma en el AMBA. Del NOA, el
56,3%. De la Patagonia, el 60,6%. El AMBA retiene a nueve de cada diez de los
suyos y absorbe el excedente de todas las demás regiones.

### 3.4 H4 — El efecto no lo fabrica la cobertura de Wikidata

**Tablas** `h4_tramos_por_nivel.csv`, `h4_regiones_por_nivel.csv`,
`h4_contraste_elite.csv`.

La objeción más seria contra todo lo anterior es el sesgo de cobertura: si
Wikidata registra mejor a los jugadores de ciudades grandes, el patrón podría
ser un artefacto del corpus y no del fútbol. La prueba está en los jugadores de
selección mayor, donde la cobertura de Wikidata es prácticamente censal.

**El gradiente por tamaño de ciudad se sostiene en los cuatro niveles**, incluido
el de selección (χ²(4) = 16,8; p = 0,002; *w* = 0,24; n = 303), con RR de 0,65
(IC 95% 0,44–0,97) para el tramo <10k contra >500k. También se sostiene el
gradiente regional en todos los niveles.

En cambio, **H4 tal como estaba formulada no se sostiene**: no hay evidencia de
que la elite provenga más de ciudades chicas. Entre T1 y T2 el 16,9% nació en
ciudades de menos de 50.000 habitantes, contra el 18,8% del resto de la muestra
(OR 0,88; IC 95% 0,70–1,09).

### 3.5 Serie temporal

Tabla `temporal_region_decada.csv`. El orden entre regiones se mantiene estable
en las cohortes de 1970, 1980 y 1990. La cohorte de 2000 muestra tasas un orden
de magnitud menores en todas las regiones por censura a derecha —esos jugadores
todavía están debutando— y no debe leerse como caída.

### 3.6 Exploratorio: posición y región

Tabla `exploratorio_posicion_region.csv`. **Estrictamente exploratorio.** De 24
contrastes, seis sobreviven a la corrección de Benjamini-Hochberg, y todos
involucran a las dos regiones con más casos: el AMBA produce más defensores
(OR 1,39; IC 95% 1,23–1,57) y menos mediocampistas (OR 0,69; 0,60–0,78) de lo
esperado, y la región pampeana lo inverso. **El mito de «las delanteras del
norte» no aparece**: ningún contraste que involucre al NOA o al NEA sobrevive a
la corrección. Estos resultados no se presentan como hallazgo confirmatorio y
requieren un diseño propio para ser tomados en serio.

---

## 4. Discusión

### 4.1 Por qué el efecto está invertido

El *birthplace effect* clásico se sostiene sobre un supuesto implícito: que la
infraestructura de desarrollo deportivo está razonablemente distribuida, de modo
que lo que diferencia a los lugares es la calidad del entorno de juego informal
y la accesibilidad de la competencia organizada. Bajo ese supuesto, la ciudad
mediana gana: tiene espacio y tiene liga.

En Argentina ese supuesto no se cumple, y los datos de H3 explican por qué el
patrón se da vuelta. Las divisiones inferiores de los clubes que producen
futbolistas profesionales están concentradas en el AMBA y en el corredor
pampeano. Nacer cerca de una es una ventaja enorme y difícil de compensar: quien
nace lejos necesita ser detectado, mudarse en la adolescencia y sostener esa
mudanza. El 94,6% de migración departamental entre los nacidos en pueblos, con
una mediana de 282 km, es la medida de ese costo.

Dicho de otro modo: en Argentina el lugar de nacimiento no mide la calidad del
entorno formativo, mide la **distancia a la infraestructura formativa**. Y esa
distancia opera como un filtro, no como un entorno.

Esto sugiere que el resultado no contradice a la literatura sino que identifica
su condición de contorno. Sería informativo replicar este diseño en otros países
con sistemas de formación igualmente centralizados.

### 4.2 La dirección de los sesgos

Los dos sesgos más grandes empujan **en contra** del hallazgo principal, lo que
lo vuelve conservador.

**Migración.** El denominador cuenta residentes en 2022, no nacimientos. Los
pueblos y las provincias del norte son exportadores netos de población: sus
denominadores están subestimados y por lo tanto sus tasas **sobre**estimadas. El
censo permite cuantificarlo a nivel provincial: la razón entre residentes y
nacidos es 0,83 en Chaco, 0,84 en Formosa y 0,85 en Corrientes, contra 1,20 en
Buenos Aires. Corregir en esa dirección haría el gradiente más pronunciado, no
menos.

**Cobertura de Wikidata.** Si el corpus sobrerrepresenta a los jugadores
notables y la notoriedad correlaciona con nacer en una ciudad grande, el efecto
estaría inflado. El control de §3.4 aborda exactamente esto: entre los jugadores
de selección mayor, donde la cobertura es prácticamente completa, el gradiente
persiste.

### 4.3 Limitaciones

1. **Nacer ≠ formarse.** El análisis base mide nacimiento. H3 aborda la
   transición con un proxy imperfecto: el vínculo `P54` más temprano con fecha,
   que muchas veces es el club de debut y no el de formación, y cuya cobertura
   es del 99,4% en la elite contra el 14,4% en el resto. La dirección de ese
   sesgo no es obvia y los números de H3 deben leerse como orden de magnitud.
2. **Cobertura de Wikidata.** Es un corpus de notabilidad, no un registro. El
   análisis por nivel competitivo acota el problema pero no lo elimina.
3. **Baseline temporal.** El tamaño de cada localidad se mide en el censo 2022,
   no en la infancia del jugador. Las poblaciones históricas por departamento
   (1991, 2001, 2010) permiten controlar a nivel provincial y no cambian el
   orden; a nivel de localidad no hay serie histórica disponible y no se
   interpoló.
4. **Unidad geográfica en áreas metropolitanas fragmentadas.** Las tasas por
   departamento se inflan en el núcleo de los aglomerados que cruzan límites
   administrativos: Capital de Mendoza aparece con 181,8 por 100.000 porque
   recibe a los nacidos en todo el Gran Mendoza contra el denominador de un solo
   departamento. Por eso el análisis de tamaño de ciudad usa aglomerados, y por
   eso los rankings departamentales deben leerse con esa salvedad.
5. **Solo fútbol masculino.**

### 4.4 Implicancias para la detección de talento

Si el patrón geográfico refleja acceso a infraestructura y no distribución de
talento, entonces las regiones que hoy producen un tercio de lo esperado son
reservas desaprovechadas y no zonas pobres en jugadores. La retención del 11,2%
en el NEA no describe una región sin futbolistas: describe una región sin lugar
donde formarlos.

Dos consecuencias prácticas. La primera es que la inversión en infraestructura
formativa fuera del corredor pampeano tiene, a priori, un retorno esperado alto.
La segunda es metodológica y vale para cualquier sistema de captación: una
métrica de producción basada en el lugar de nacimiento le atribuye al AMBA
talento que el AMBA no produjo sino que absorbió a los quince años.

---

## 5. Reproducibilidad

Todo el pipeline es código; `data/raw/` no se edita y cada descarga deja un
manifiesto fechado con URL y SHA-256. El snapshot de Wikidata está fechado
porque el corpus cambia a diario. Las decisiones de diseño —cohortes, cortes de
tamaño, regla de desambiguación, baseline— están en `config.yaml` con su
justificación, y las funciones que comparten numerador y denominador tienen
tests.

```powershell
python -m src.ingest.wikidata_players
python -m src.ingest.wikidata_places
python -m src.ingest.wikidata_careers
python -m src.ingest.wikidata_clubs
python -m src.ingest.indec_census
python -m src.ingest.georef
python -m src.ingest.ign_boundaries
python -m src.clean.build_players
python -m src.clean.build_population
python -m src.clean.crosswalk_localidades
python -m src.clean.geocode_places
python -m src.clean.build_analysis_dataset
python -m src.clean.build_careers
python -m src.clean.geocode_clubs
python -m src.analysis.run_all
python -m src.analysis.run_levels_and_flow
python -m src.viz.make_figures
```

### Fuentes

- **Wikidata**, consultada vía SPARQL. Licencia CC0. Snapshot 2026-07-30.
- **INDEC**, Censo Nacional de Población, Hogares y Viviendas 2022, microdatos
  tabulados por radio censal; y radios censales de 1991, 2001, 2010 y 2022.
- **API Georef**, Servicio de Normalización de Datos Geográficos de la
  Administración Pública Nacional.
- **IGN**, capas SIG de unidades territoriales.

Transfermarkt no se utilizó: sus términos prohíben el scraping automatizado.

### Lecturas de fondo

Se listan como punto de partida bibliográfico; las afirmaciones de §1.1 deben
verificarse contra estas fuentes antes de cualquier publicación formal.

- Revisión sistemática del *birthplace effect* en fútbol:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11571467/
- «Place Matters» — nacimiento contra lugar de desarrollo:
  https://www.mdpi.com/2075-4663/12/4/99
- The geography of talent development:
  https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.1031227/full
