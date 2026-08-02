# Revisión crítica — *¿De dónde salen los futbolistas argentinos?*

**Revisor:** hostil, sin sándwich de feedback.
**Fecha:** 2026-08-01. **Commit revisado:** `3f07dba`. **Snapshot Wikidata:** 2026-07-30.
**Alcance:** diseño de investigación. El código se juzga solo donde compromete un resultado.

---

> ## Estado de los puntos bloqueantes (actualizado 2026-08-01, después de la revisión)
>
> | # | Punto | Estado |
> |---|---|---|
> | B1 | Bug de granularidad `provincia` (110 jugadores fantasma) | ✅ **arreglado** — `geocode_places.py`. Ullum y Tumbaya salieron del ranking; Azul bajó de 29 a 9 jugadores. El análisis departamental pasó de 5.499 a 5.389 jugadores. |
> | B4 | H4 corría con el denominador censal | ✅ **arreglado** — `run_levels_and_flow.py` usa nacidos vivos. χ² de la selección pasó de 13,8 a 26,5. |
> | B6 | Tamaño de efecto y monotonía falsa | ✅ **arreglado** — pseudo-R² = 0,011 reportado en el paper y en la Figura 7; la monotonía se corrigió por «escalón» y se agregó la Figura 20 por decil. |
> | — | El error del denominador tiene signo y pendiente | ✅ **medido y declarado** — §2.1 del paper y **Figura 19**. |
> | — | Números chicos sin control | ⚠️ **parcial** — se agregó funnel plot (**Figura 21**), pero sigue sin haber *shrinkage* ni Bayes empírico. |
> | — | El efecto por cohorte no se probaba | ✅ **agregado** — **Figura 22**. RR plano (0,34 · 0,43 · 0,41 · 0,55). |
> | — | Salidas obsoletas | ✅ **archivadas** en `outputs/tables/_obsoletas/` con su LEEME. |
> | B5 | H3 medido sobre muestra seleccionada por el desenlace | ⚠️ **declarado, no resuelto** — es la limitación 4 del paper y ya no se usa como explicación causal de H1, pero los números siguen en el resumen. |
> | B2 | **Tasa de error del `P19` sin medir** | ❌ **pendiente. Es lo que decide si hay paper.** |
> | B3 | **Artefacto de maternidad sin acotar** | ❌ **pendiente.** El paper ya no afirma la simetría numerador-denominador como hecho establecido (§2.1), pero el artefacto sigue sin medirse. |
>
> **Novedad que cambia el veredicto parcialmente:** se agregó un análisis que **no
> depende de ningún denominador poblacional** (§3.5 del paper): entre los
> futbolistas que ya llegaron a un juvenil de la selección, los nacidos fuera de un
> gran aglomerado llegan a la Mayor un 41,9% de las veces contra un 28,1%
> (OR 1,85; IC 95% 1,14–2,98; p = 0,013; 1,85 ajustado por cohorte). Ninguna de las
> balas de esta review le pega: no usa denominador estimado, el registro del parto
> en la cabecera lo **atenúa** en vez de crearlo, la cobertura de Wikidata es del
> 97% y pareja entre los dos grupos, y compara dentro de un grupo ya filtrado por
> talento. **Ese resultado sí está listo para publicarse; el resto del trabajo
> sigue necesitando B2 y B3.**

---

## Fase 0 — Reconocimiento

### Qué se revisó

`README.md`, `CLAUDE.md`, `config.yaml`, `reports/paper.md`, los 16 módulos de `src/`,
las 45 tablas de `outputs/tables/`, las 13 figuras (leídas como imágenes, no
listadas), y los parquets de `data/processed/`.

### Reproducción

Corrí `python -m src.analysis.run_all` de cero. **Reproduce.** Las cifras centrales
del paper salen idénticas del código:

| Cifra del paper | Valor en el paper | Valor reproducido | ¿Coincide? |
|---|---|---|---|
| RR `<10k` vs `>500k` (H1) | 0,42 (0,38–0,47) | 0,4238 (0,3833–0,4685) | sí |
| χ²(4) H1 esquema principal | 452,2 | 452,226 | sí |
| IRR por *e-fold* de tamaño | 1,181 (1,120–1,246) | 1,1814 (1,1198–1,2464) | sí |
| AIC lineal vs cuadrático | 3.652,8 / 3.654,3 | 3652,83 / 3654,28 | sí |
| n de la muestra H3 | 1.947 | 1947 | sí |
| **n de ciudades en la regresión** | **3.476** | **3459** | **no** |

Una sola discrepancia, menor: `reports/paper.md` §3.1 dice «3.476 ciudades»;
`outputs/tables/regresion_tamano_ciudad.csv` dice `n_ciudades=3459`. Es una errata
de transcripción, no un problema de pipeline. Corregila y listo.

Que reproduzca no es un elogio: es el piso. Pero conviene decirlo porque significa
que todo lo que sigue es una crítica al **diseño**, no a la prolijidad.

---

## Fase 1 — La tesis

### En cinco líneas

> **Pregunta:** ¿los futbolistas argentinos nacen desproporcionadamente en el
> interior y en ciudades chicas y medianas, respecto de los nacimientos reales de
> cada lugar?
> **Afirmación central:** no; el patrón está invertido. La producción crece con el
> tamaño de la ciudad de nacimiento (12,9 → 30,5 cada 100.000 nacidos) y se
> concentra en AMBA y el corredor pampeano. El mecanismo propuesto es que la
> infraestructura de formación está centralizada, de modo que el lugar de
> nacimiento mide distancia a un club formador, no calidad del entorno.
> **Evidencia:** 5.511 futbolistas de Wikidata (cohortes 1975–2008) sobre un
> denominador de nacidos vivos del DEIS; χ², tasas con IC de Poisson, regresión
> binomial negativa; y un análisis de flujo nacimiento → primer club sobre 1.947
> jugadores.

La tesis **se puede reconstruir**. No es un repo de análisis sueltos: hay una
pregunta, una respuesta y una cadena de evidencia. Eso lo pone por encima de la
mayoría de lo que se presenta como proyecto de datos.

### Test del resultado invertido

**Lo pasa a medias, y la mitad que falla es la que importa.**

Lo pasa en lo formal: `config.yaml` fija los cortes de tamaño, el test, el
baseline y la corrección por comparaciones múltiples **antes** de ver el
resultado, y ordena reportar dos esquemas de partición para que el efecto no
dependa de la grilla (`config.yaml:191-203`). Eso es cuasi-preregistro y es
genuinamente buena práctica. Si el resultado hubiera dado el clásico, el aparato
habría sido el mismo.

Lo falla en lo narrativo. H3 estaba especificada como **hipótesis de flujo**
(`CLAUDE.md` §2: «existe una migración sistemática entre el lugar de nacimiento y
el club formador»). En el paper terminado, H3 dejó de ser una hipótesis y pasó a
ser **la explicación causal de H1** (`reports/paper.md` §4.1: «los datos de H3
muestran por qué el patrón se da vuelta»). Un resultado descriptivo fue promovido
a mecanismo después de conocer el resultado que tenía que explicar. Estructuralmente
eso es HARKing, aunque no haya habido intención.

Y el mecanismo tiene una implicación temporal que nadie testeó. Si la
centralización de las academias es la causa, la brecha debería **ensancharse** por
cohorte. La corrí:

| Década de nacimiento | n | RR `<10k` vs `>500k` | IC 95% |
|---|---:|---:|---|
| 1970 (desde 1975) | 559 | 0,34 | 0,25–0,48 |
| 1980 | 2.040 | 0,43 | 0,36–0,50 |
| 1990 | 2.064 | 0,41 | 0,35–0,48 |
| 2000 (censurada) | 585 | 0,55 | 0,42–0,72 |

Plana, con IC solapados, y si algo se mueve es en la **dirección contraria** a la
que predice el mecanismo del §4.1. Treinta años de cohortes durante los cuales la
estructura de inferiores del fútbol argentino cambió mucho, y el efecto no se
mueve. Eso no refuta el mecanismo, pero es la prueba más obvia que el repo tenía a
mano y no corrió.

### Test del «¿y?»

**Hoy no lo pasa.**

La respuesta ambiciosa está en `reports/paper.md` §4.4: el NEA retiene el 8,3% de
sus futbolistas, luego hay «reservas desaprovechadas» y la inversión en
infraestructura formativa fuera del corredor central «tiene, a priori, un retorno
esperado alto». Eso sí le cambiaría algo a alguien: AFA, clubes, política
deportiva provincial.

Pero **todo ese «¿y?» descansa sobre H3**, y H3 está medida sobre una muestra
seleccionada por el desenlace (Fase 2, punto 3-bis). Sacale H3 y lo que queda es
«en las ciudades grandes se registran más futbolistas por nacido», que está a un
paso de «donde están los clubes se anotan los jugadores». Interesante; no
accionable.

---

## Fase 2 — El roast

### 1. Denominador — **resuelve lo grande, esconde un sesgo direccional**

Empiezo por lo que está bien, en una línea como corresponde: **pasar de población
censada 2022 a nacidos vivos del DEIS por cohorte es la mejor decisión del
proyecto**, está bien argumentada (`src/clean/build_denominators.py:1-28`) y
corrige un sesgo que iba en contra del hallazgo. Eso es trabajo real.

Ahora el problema. El dato del DEIS es **provincial**. Para bajar a departamento,
`estimar_por_departamento` (`src/clean/build_denominators.py:118-127`) reparte los
nacimientos provinciales según la **participación de cada departamento en la
población residente** del censo más cercano. El paper llama a esto «el único
supuesto de la cadena» y lo declara validado.

**Medí el sesgo de ese supuesto y no es neutro respecto de la variable explicativa.**
Sobre `qa_validacion_denominador_detalle.csv`, ratio estimado/real por decil de
tamaño del departamento:

| Decil (nacimientos reales) | Mediana de nacimientos | Estimado / real |
|---|---:|---:|
| 0 (más chico) | 435 | **1,171** |
| 1 | 1.205 | 1,097 |
| 2 | 2.021 | 1,063 |
| 4 | 3.914 | 1,026 |
| 7 | 12.996 | 0,999 |
| 9 (más grande) | 60.160 | 0,990 |

Spearman(tamaño, ratio) = **−0,355, p = 1,3 × 10⁻¹⁶**.

El denominador de los departamentos más chicos está **inflado un 17%**, y el de
los grandes está bien. Un denominador inflado deprime la tasa. **El error de
imputación empuja exactamente en la dirección del titular.** No lo explica entero
—corregir 17% lleva el RR de 0,42 a ~0,49, sigue muy por debajo de 1— pero es un
sesgo sistemático correlacionado con la variable de interés, que el paper reporta
como «error mediano 9%» sin decir que ese error tiene signo y tiene pendiente.

**Y la validación es circular.** El paper valida el reparto contra RENAPER
(r = 0,993). Dos objeciones:

- **RENAPER es por residencia/registro, no por ocurrencia.** La distribución de
  la tasa bruta de natalidad departamental de RENAPER tiene media 15,5 y el 97,2%
  de los departamentos-año entre 8 y 30 por mil. Si fuera por lugar de ocurrencia,
  las cabeceras con maternidad regional tendrían TBN de tres dígitos y los
  departamentos rurales cerca de cero. No es lo que se ve. Validar un reparto
  *por población residente* contra una fuente *por residencia* es casi una
  tautología: mide que la gente vive donde vive.
- **r = 0,993 entre unidades que van de 435 a 60.160 nacimientos no mide
  exactitud, mide tamaño.** Cualquier reparto proporcional al tamaño da esa
  correlación. La cifra honesta ya está en el repo (error mediano 9,1%) y es la
  que hay que reportar; la r es decorativa y en el paper aparece primero.

**CABA queda fuera de la validación.** `validar_contra_renaper`
(`src/clean/build_denominators.py:139`) hace `dropna(subset=["departamento_id"])`,
y las 11 filas de CABA en RENAPER tienen `departamento_id` nulo. Es decir: la
jurisdicción que encabeza H2 con obs/esp = 2,63 y 962 jugadores es la única que el
control de calidad no toca.

**Lo más serio: el argumento de simetría del §2.1 no vale en el nivel donde vive
el hallazgo.** El paper defiende la comparación así (`reports/paper.md:106-110`):

> «la serie del DEIS cuenta nacimientos **ocurridos**, por lugar del parto, que es
> exactamente la definición que usa el `P19` de Wikidata […] quien nació en una
> maternidad de la Capital figura en la Capital en las dos puntas del cociente.»

Eso es cierto **a nivel provincia**, donde el DEIS es dato real. A nivel
departamento y ciudad —donde viven H1, el ranking de cunas y las Figuras 1, 4, 7 y
11— el denominador ya **no** es por ocurrencia: es por población residente
repartida. El numerador sigue siendo `P19`. La simetría que hace válida la tasa se
rompe justo en el nivel donde se mide el efecto, y el paper la afirma sin
calificar el nivel.

Intenté verificar la premisa comparando DEIS y RENAPER por provincia 2012–2022 y
**no se puede distinguir**: dan casi lo mismo (CABA: DEIS 397.191 vs RENAPER
402.492, −1,3%; Buenos Aires, ratio 0,997). O RENAPER también es por ocurrencia, o
el DEIS no es por ocurrencia como se afirma. **No verificado**, y el paper lo
presenta como hecho establecido que sostiene toda la comparación.

### 2. Nacimiento ≠ formación y el artefacto de las maternidades — **lo esconde. Es el punto de falla.**

El repo declara la limitación «nacer ≠ formarse» seis veces y con honestidad
(`README.md:150`, `reports/paper.md` §2.6, §4.3.1). Pero **declara la limitación
conceptual y esquiva la mecánica**: en Argentina el parto ocurre donde hay
maternidad, y eso reasigna sistemáticamente bebés de pueblos y parajes a la
cabecera departamental.

La única defensa del paper es el argumento de simetría del §2.1, que acabo de
mostrar que no aplica por debajo de provincia. Sin esa defensa, no queda nada:
**el artefacto no está medido, ni acotado, ni testeado.**

Y hay evidencia directa de que el tramo chico está contaminado. El bin `<10k`
—3,34 millones de nacimientos en el denominador, 431 jugadores— se construye sobre
`tamano_localidad.parquet`, que incluye:

| Localidad | Población |
|---|---:|
| `ZONA RURAL` (dept. 06644) | 4 |
| `Paraje La Ruta` | 6 |
| `Club de Pesca Saavedra` | 6 |
| `Villa Lynch Pueyrredón` | 2 |

**264 «localidades» tienen menos de 100 habitantes.** El decil más chico de
ciudades tiene población mediana **72**. Nadie nace en un paraje de seis personas:
esos partos ocurren en la cabecera y se registran ahí, en el DEIS **y** en
Wikidata. Resultado: el numerador de esas unidades es estructuralmente cero,
mientras el denominador se les llena por reparto poblacional. Es el mecanismo del
punto 1 y el de este punto operando sobre las mismas celdas.

Además, es un problema de validez de constructo, no solo de sesgo: el `<10k` de
este trabajo mezcla pueblos reales con parajes dispersos, y no es la categoría
«small city» de Côté et al., que arranca en 1.000 habitantes con localidades
urbanas. La comparación con la literatura del §3.1 compara cosas distintas.

**Lo que el repo sí distingue:** nacimiento vs primer club (H3, con proxy
declarado). **Lo que no distingue en ningún lado:** lugar de nacimiento vs lugar
de **crianza**. Es la variable que la propia literatura que el paper cita señala
como la que importa, y no existe en el pipeline.

### 3. Definición de la muestra — **ignora la pregunta de fondo**

`config.yaml:22-38` justifica bien las reglas *internas* (ciudadanía vs
nacimiento, exclusión femenina, dedup). Lo que nunca se pregunta es:
**¿qué fracción de los futbolistas profesionales argentinos reales está en
Wikidata?** No hay una sola comparación contra un padrón externo (AFA, BDFA,
Soccerway, fichajes de AFA).

El propio repo tiene la evidencia de que la cobertura es mala y variable.
`diagnostico_censura_cohortes.csv`: la cohorte 1975–1979 rinde **47,5% del pico**
de 1985–1989. El paper atribuye esa caída a cobertura
(`reports/paper.md:130-132`). O sea: se sabe que la cobertura varía **al doble**
entre cohortes, se lo dice, y no se lo mide contra nada.

Y «futbolista en Wikidata» no es una definición de nivel: es notabilidad. Los
tiers T1–T4 (`config.yaml:49-68`) son una buena idea, pero T4 («resto») son 2.574
jugadores cuyo único atributo común es tener artículo. No es una categoría
competitiva, es un residuo.

### 4. Calidad de la fuente / tasa de error de `P19` — **ignora, y encima hay un bug**

**La tasa de error de `P19` no está medida contra ninguna fuente independiente.**
Cero. El repo valida con rigor el *geocoding* de `P19` —que está muy bien hecho,
por coordenada contra Georef, con clasificación de granularidad previa
(`src/clean/geocode_places.py:116-135`)— pero eso valida **dónde cae la coordenada
que Wikidata declara**, no si Wikidata declara la verdad. Son cosas distintas y el
paper las trata como una sola.

Es el punto 4 del pedido y la respuesta es: no se hizo. Todo lo demás está
construido sobre un dato sin validar.

**Y encontré un modo de falla concreto que el proyecto no vio.** El filtro de
granularidad anula el departamento para `pais` y `region`
(`src/clean/geocode_places.py:267-269`) pero **no para `provincia`**. Resultado:
**110 jugadores cuyo `P19` es literalmente una provincia** entran igual al análisis
departamental, clavados en el departamento donde cae el centroide provincial:

| Provincia declarada como lugar de nacimiento | Departamento receptor | Jugadores fantasma |
|---|---|---:|
| Buenos Aires | Azul | 20 |
| Córdoba | Tercero Arriba | 18 |
| Santa Fe | General López | 17 |
| Mendoza | Capital | 10 |
| Chaco | San Fernando | 7 |
| Tucumán | Famaillá | 7 |
| San Juan | Ullum | 3 |
| Jujuy | Tumbaya | 3 |

Efecto sobre las tasas departamentales:

| Departamento | Jugadores | Fantasmas | Tasa publicada | Tasa real | Inflado |
|---|---:|---:|---:|---:|---:|
| Ullum (San Juan) | 3 | 3 | 102,7 | **0,0** | ∞ |
| Tumbaya (Jujuy) | 3 | 3 | 80,4 | **0,0** | ∞ |
| Azul (Bs. As.) | 29 | 20 | 75,5 | 23,4 | +222% |
| Tercero Arriba (Córdoba) | 32 | 18 | 48,2 | 21,1 | +129% |
| Famaillá (Tucumán) | 11 | 7 | 48,9 | 17,8 | +175% |
| General López (Santa Fe) | 61 | 17 | 57,0 | 41,1 | +39% |

**Ullum y Tumbaya aparecen en el top-12 nacional de tasa departamental con un
número construido enteramente con jugadores fantasma.** Su cuenta verdadera es
cero.

Esto es exactamente la **trampa 1 de `CLAUDE.md`** —el caso «Argentina» → General
Levalle, que el proyecto documenta con orgullo como resuelta— reproducida un nivel
más arriba. Se blindó el país y la región; se dejó la provincia abierta.

### 5. Números chicos — **lo esconde**

**No hay shrinkage, ni empirical Bayes, ni funnel plot.** Nada. `src/analysis/stats.py`
tiene IC exacto de Poisson (bien elegido, y el comentario de la línea 80-83
explica por qué) pero el IC ensancha la barra, no corrige el ranking.

Existe una bandera `reportable` en `h2_departamentos.csv` (42 de 526 en `True`),
pero **la tabla publica las 526 filas y la Figura 1 mapea todo**. La bandera no se
usa donde importa.

Leí la Figura 1 como imagen. Su clase de color más oscura es **«38 – 163»**. El
163 es Magdalena: **6 jugadores**, IC 95% 59,8–354,7. El extremo superior de la
escala cromática del mapa insignia del trabajo está anclado en ruido de Poisson.
El top-12 por tasa incluye Magdalena (6 jugadores), Ullum (3, todos fantasma),
«2 de Abril» (2 jugadores), Tumbaya (3, todos fantasma) y Castelli (4).

**¿Mapa de talento o mapa de varianza?** Las dos cosas: el núcleo AMBA–pampeano es
señal robusta y se ve claramente. Las **colas son varianza**, y son justo las que
producen titulares («las cunas son Rafaela, Gran Santa Fe…»).

### 6. MAUP — **lo resuelve, y es lo mejor del trabajo**

Crédito, en una línea como corresponde: se reportan provincia, departamento y
localidad; H1 se corre con aglomerado y con localidad censal aislada
(`h1_robustez_localidad_sola.csv`, RR 0,42 vs 0,39); y hay dos esquemas de corte
de tamaño con la justificación explícita de que «si el efecto aparece con uno solo,
es un artefacto de la partición» (`config.yaml:186`). El hallazgo **no** es una
decisión de agregación, y está probado.

Dos huecos: H2 nunca se corre a nivel aglomerado (y la limitación 5 del README
reconoce que el nivel departamental está roto en metrópolis fragmentadas — Capital
de Mendoza, 114,9 por 100.000, es el caso), y la Figura 1 sigue siendo
departamental.

### 7. Comparaciones múltiples — **se aplica donde es barato**

Bien: los 24 contrastes de posición × región llevan Benjamini-Hochberg
(`src/analysis/stats.py:129-144`, `config.yaml:266`), sobreviven 6, y el paper
reporta honestamente que el mito de «las delanteras del norte» no aparece.

Mal: la corrección se aplica **solo** ahí. `tests_bondad_ajuste.csv` tiene 12
tests. `h4_tests.csv` tiene 8. `h2_provincias*.csv` son 24 provincias × 6
baselines. Ninguno lleva corrección. La regla del proyecto («obligatoria en los
cruces exploratorios») se cumple al pie de la letra y se esquiva en espíritu: los
contrastes confirmatorios son más y no se corrigen.

### 8. Confusores — **ignora por completo, y después escribe en clave causal**

**No hay un solo control.** La regresión binomial negativa tiene exactamente una
covariable: `log(población)` (`regresion_tamano_ciudad.csv`). No hay distancia a un
club con inferiores, ni existencia de pensión, ni NBI o nivel socioeconómico, ni
densidad de ligas locales, ni migración interna. El análisis es **puramente
descriptivo**.

Peor: **el mecanismo que el paper propone nunca es una variable en ningún modelo.**
El §4.1 concluye que el lugar de nacimiento «mide la distancia a la infraestructura
formativa». La distancia a la infraestructura formativa no se calcula en ninguna
parte del pipeline.

Como pide el encargo, las frases en clave causal, una por una:

| Ubicación | Frase | Problema |
|---|---|---|
| `paper.md` §4.1 | «en Argentina el lugar de nacimiento no mide la calidad del entorno formativo, **mide la distancia a la infraestructura formativa**» | Afirmación causal sobre una variable que no existe en ningún modelo. Está en negrita. |
| `paper.md` §4.1 | «**Nacer cerca de uno es una ventaja difícil de compensar**» | Efecto causal individual desde tasas agregadas sin controles. |
| `paper.md` §4.1 | «esa distancia **opera como un filtro**, no como un entorno» | Mecanismo afirmado, no estimado. |
| `paper.md` §3.3 | «Los clubes **muestran el mecanismo** con nombre y apellido» | «Mecanismo» para describir una tabla cruzada de una muestra sesgada. |
| `paper.md` §4.4 | «las regiones que hoy producen un cuarto de lo esperado **son reservas desaprovechadas**» | Requiere suponer talento latente uniforme entre regiones. El supuesto nunca se enuncia. |
| `paper.md` §4.4 | «no describe una región sin futbolistas: **describe una región sin lugar donde formarlos**» | Retórica causal sobre un dato de cobertura de Wikidata del 8,3% de retención. |
| `paper.md` §4.4 | «La inversión en infraestructura formativa fuera del corredor central **tiene, a priori, un retorno esperado alto**» | Recomendación de política derivada de estadística descriptiva sin controles. |
| `paper.md` §4.4 | «le atribuye al AMBA talento que el AMBA **no produjo sino que absorbió a los quince años**» | Afirmación sobre trayectorias individuales; ver punto 9. |
| `README.md:44` | «**No es un artefacto de Wikidata.**» | Ver punto 3-bis: prueba contra una amenaza, se enuncia contra todas. |

El §4.3 lista seis limitaciones y ninguna es «no hay controles». Es la que falta.

### 9. Falacia ecológica — **parcialmente, y en la conclusión**

A favor: H3 es genuinamente individual (cada jugador tiene su par nacimiento →
primer club, con distancia en km). Eso es la forma correcta de escapar del
problema y está bien hecho.

En contra, dos:

- El OR 5,58 del abstract compara un estadístico **individual** (47,1% de 1.947
  futbolistas) contra un **marginal agregado del censo** (13,8% de 42.640.509
  personas). No son la misma clase de objeto.
- El §4.4 salta de tasas agregadas a oportunidad individual: «una región sin lugar
  donde formarlos», «talento que el AMBA absorbió a los quince años». Ninguna
  observación del dataset es una trayectoria individual de crianza.

### 10. Dimensión temporal — **media hecha**

Existe `temporal_region_decada.csv` con la evolución por región y década, con
marca de censura. Bien.

**No existe H1 × cohorte.** El efecto de tamaño de ciudad —el hallazgo principal—
nunca se corta por década. Lo corrí yo (Fase 1): plano, 0,34 / 0,43 / 0,41 / 0,55,
IC solapados, sin ensanchamiento. Falta esa mitad de la investigación y además el
resultado incomoda al mecanismo del §4.1.

---

### Hallazgos adicionales (no estaban en la lista)

#### 3-bis. H3 está medida sobre una muestra seleccionada por el desenlace — **grave**

`qa_niveles_y_primer_club.csv` reporta la cobertura del primer club por tier, y el
paper la cita como limitación. Lo que no se reporta es **qué le hace eso a la
composición de la muestra**:

| Tier | % de la muestra completa | % de la muestra H3 | Factor |
|---|---:|---:|---:|
| T1 selección | 4,8% | 12,8% | ×2,7 |
| T2 Europa top | 5,3% | 10,8% | ×2,0 |
| T3 Primera AR | 43,2% | 67,7% | ×1,6 |
| **T4 resto** | **46,7%** | **8,6%** | **×0,18** |

La muestra de H3 está enriquecida al doble en jugadores de elite y **vaciada cinco
veces y media** del resto. Y los jugadores de elite son precisamente los que se
fueron a Boca y River.

Por lo tanto:

- **«El 47,1% se forma fuera de su provincia»** no es una estimación poblacional.
  Es la tasa de migración de una muestra elegida por haber llegado lejos.
- **«Diez clubes concentran el 48% de toda la formación del país»** es casi
  mecánico: Wikidata registra el primer club de los que terminaron siendo
  famosos; los famosos salieron de clubes grandes; luego los clubes grandes
  dominan la distribución registrada. El número mide la política editorial de
  Wikipedia, no la estructura formativa argentina.

El paper dice que los números de H3 «deben leerse como orden de magnitud»
(§4.3.1) y a continuación los usa como titular del abstract, del README y como
**explicación causal de H1** en el §4.1. Un dato no puede ser orden de magnitud en
la sección de limitaciones y mecanismo confirmado en la discusión.

#### 3-ter. La comparación con la población general no es comparable

47,1% (futbolistas, nacimiento → primer club, medido a los ~15-20 años) contra
13,8% (población general, nacimiento → residencia 2022, **todas las edades**,
n = 42.640.509, incluidos bebés y niños que todavía no migraron).

Peor: **no se puede arreglar con estos datos.** Verifiqué que
`pop_dept_nacprov.parquet` no tiene columna de edad — coincide con lo que
`CLAUDE.md` ya anota, que `P14` es un marginal por radio sin cruzar con `EDAD`. El
denominador correcto (varones de las mismas cohortes) no existe en la fuente. La
opción no es mejorar la comparación: es sacarla del abstract o rodearla de
advertencias.

#### B. H4 corre con el denominador que el propio paper declara inválido

`src/analysis/run_levels_and_flow.py:39-40`:

```python
pob_tramo  = ciudades.groupby(col, observed=False)["pob_cohorte_ciudad"].sum()
pob_region = denom_dept.groupby("region")["pob_cohorte"].sum()
```

`pob_cohorte_ciudad` es **población censada 2022 por cohorte de edad** — el
denominador que `reports/paper.md` §2.1 encabeza con «**Lo que no sirve**». H1 y
H2 se migraron a nacidos vivos del DEIS en la revisión del 2026-07-31; H4 no.

| Tramo | Denominador H1 (DEIS, nacidos) | Denominador H4 (censo 2022) | Diferencia |
|---|---:|---:|---:|
| `<10k` | 3.339.078 | 2.739.291 | **−18,0%** |
| `10–50k` | 3.418.174 | 3.286.082 | −3,9% |
| `>500k` | 10.975.566 | 12.393.779 | +12,9% |

El denominador viejo es 18% más chico en `<10k` y 13% más grande en `>500k`: las
tablas de H4 son **sistemáticamente más favorables a los pueblos** que las de H1, y
el paper las presenta lado a lado como si fueran comparables.

Concretamente, el §3.4 mezcla las dos procedencias **en el mismo párrafo**: cita
χ²(4) = 13,8 (que sale de `h4_tests.csv`, denominador censal) junto a «15
seleccionados por millón contra 7» (que sale de `futbol_seleccion_por_tramo.csv`,
denominador de nacidos). Son dos denominadores distintos en dos oraciones
consecutivas.

#### C. El escudo del sesgo de cobertura prueba menos de lo que se le hace decir

El §3.4 y el `README.md:44` usan la selección mayor —cobertura 97,4%— para
concluir «no es un artefacto de Wikidata». El argumento es válido **contra la
amenaza de cobertura** y no dice absolutamente nada **contra el artefacto de
maternidad** (punto 2), que es la amenaza más probable y que afecta a los
seleccionados exactamente igual que al resto. Un seleccionado nacido en una
maternidad del Gran Buenos Aires y criado en un pueblo cuenta como `>500k` en las
dos puntas del cociente, sea o no famoso.

Se testea una amenaza y se enuncia la conclusión contra todas.

Y dentro de la selección **tampoco hay gradiente**, hay un escalón
(`futbol_seleccion_por_tramo.csv`):

| Tramo | Por millón | IC 95% |
|---|---:|---|
| `<10k` | 7,49 | 4,85–11,05 |
| `10–50k` | 7,02 | 4,50–10,45 |
| `50–100k` | 8,59 | 4,29–15,37 |
| `100–500k` | 9,20 | 6,06–13,39 |
| `>500k` | **15,31** | 13,08–17,80 |

Los cuatro tramos chicos son indistinguibles entre sí. El paper escribe «el
gradiente por tamaño se sostiene en los cuatro niveles»; lo que se sostiene es un
contraste binario metrópoli vs todo lo demás.

#### D. La monotonía es falsa tal como está enunciada

El paper (§3.1, abstract, `README.md:22`) y el subtítulo de la Figura 7 dicen que
la tasa «crece de forma monótona» con el tamaño. Por decil de tamaño de ciudad:

| Decil | Población mediana | Jugadores | Tasa /100.000 |
|---|---:|---:|---:|
| 0 | 72 | 3 | **22,6** |
| 1 | 220 | 2 | 4,6 |
| 2 | 375 | 10 | 14,0 |
| 3 | 574 | 7 | 4,9 |
| 4 | 908 | 15 | 8,5 |
| 5 | 1.362 | 23 | 8,8 |
| 6 | 2.116 | 53 | 13,3 |
| 7 | 3.584 | 90 | 11,3 |
| 8 | 7.260 | 260 | 16,0 |
| 9 | 23.492 | 4.773 | 25,9 |

**Tres de nueve pasos bajan.** El decil más chico tiene la tercera tasa más alta.
Los deciles 0–8 juntos —todas las ciudades por debajo de ~10.000 habitantes—
contienen 463 de 5.248 jugadores y **no muestran tendencia**: rebotan entre 4,6 y
22,6 sin orden. Todo el «gradiente» es el salto del decil 9.

La monotonía aparece únicamente cuando se colapsa a los cinco bins de
`config.yaml`, que fusionan nueve deciles sin señal en cuatro categorías anchas.
Es un artefacto de la partición — exactamente el riesgo que el propio
`config.yaml:186` dice estar controlando.

Y esto no es cosmético: un escalón único en el decil superior es **precisamente la
firma** que producirían el artefacto de maternidad y el sesgo de imputación
actuando juntos. La forma del efecto es compatible con el artefacto y no con un
gradiente de entorno.

#### E. La regresión no reporta tamaño de efecto — violando la regla del propio proyecto

El paper reporta IRR = 1,181 y p < 0,0001. No reporta cuánta variación explica.
Lo calculé sobre el mismo modelo:

- **Pseudo-R² de McFadden = 0,011**
- **Devianza explicada = 2,6%**

El tamaño de la ciudad explica **el 1% de la variación** en la tasa de producción
entre ciudades. La Figura 7 lo muestra sin querer: a 10⁵ habitantes las ciudades
van de 3 a 100 por 100.000.

`CLAUDE.md` §6 dice: «**ningún hallazgo se apoya solo en un p-valor.** Reportar
estadístico, gl, p, tamaño de efecto e IC». La regla se cumple en las tablas de
tramos (con `w`, `V`, RR, IC) y **se incumple exactamente en la regresión**, que es
donde el resultado es más débil.

#### F. La Figura 7 ajusta y dibuja datos distintos

Su nota al pie: «El scatter excluye ciudades con menos de 5.000 nacidos en la
cohorte […]; el ajuste y los deciles usan todas». La nube que el lector ve y el
modelo cuya recta se le superpone **no son la misma muestra**. Está declarado, lo
cual es correcto, pero una figura cuyo elemento visual y cuyo elemento inferencial
usan poblaciones distintas no debería publicarse así.

#### G. Salidas obsoletas conviviendo con las vigentes

Tres tablas de `outputs/tables/` son de las 18:34 del 2026-07-30 y **ya no las
regenera ningún script**:

- `h1_robustez_cohorte_1970_1984.csv`
- `h1_robustez_cohorte_1985_2000.csv`
- `h2_provincias_baseline_nacimiento.csv`

La primera usa el denominador censal viejo y una ventana que arranca en **1970** —
la que `build_denominators.verificar_cobertura` ahora **aborta con excepción** por
el hueco 1971–1974 del DEIS. Es decir: el repo publica una tabla producida por una
configuración que el propio repo ahora declara inválida, sin ninguna marca que lo
indique. Un lector de `outputs/` no tiene forma de distinguirlas de las vigentes.

---

## Fase 3 — Novedad y veredicto

### Frente a la literatura

Verificado con acceso web:

| Referencia | Estado | Qué dice |
|---|---|---|
| Côté, MacDonald, Baker & Abernethy (2006), «When "where" is more important than "when": birthplace and birthdate effects on the achievement of sporting expertise», *Journal of Sports Sciences* 24(10):1065–1073 | **verificado** | Sobrerrepresentación en ciudades < 500.000; mejores odds < 100.000. |
| Hernández-Simal, Calleja-González, Lorenzo Calvo & Aurrekoetxea-Casaus (2024), «Birthplace Effect in Soccer: A Systematic Review», *Journal of Human Kinetics* | **verificado** | Tres ejes: tamaño/densidad, sociodemografía y **proximidad a centros de rendimiento**. Reporta evidencia contradictoria: hay estudios con jugadores de elite viniendo de áreas densas y «no consistent advantage» en fútbol. **Argentina no aparece.** |
| «The geography of talent development», *Frontiers in Sports and Active Living* (2022), PMC9582327 | **parcialmente verificado** | Confirma la banda 50.000–99.999 como la de mayor probabilidad. Autoría y año exactos: **no verificados**. |
| «Place Matters», *Sports* (MDPI) 12(4):99 | **NO VERIFICADO** | El servidor devolvió 403. **La cifra de «~38% más de chances de debutar» que `CLAUDE.md` §5 atribuye a este trabajo no está verificada.** No citarla hasta chequearla. |

**Lo que aporta:** el hueco argentino es real —la revisión sistemática de 2024 no
menciona Argentina— y el denominador de nacidos vivos por cohorte es mejor que el
de buena parte de la literatura, que usa población censal contemporánea. Eso es
una contribución metodológica genuina.

**Lo que no aporta, y el paper insinúa que sí:** el §4.1 presenta el efecto
invertido como identificación de una «condición de contorno» de la literatura. Pero
**la revisión sistemática que el propio paper cita como lectura de fondo ya
documenta hallazgos que favorecen a las áreas densas, ya reporta que en fútbol no
hay ventaja consistente de las ciudades chicas, y ya identifica la proximidad a
centros de rendimiento como uno de sus tres ejes.** El «mecanismo nuevo» del §4.1
es uno de los tres temas de la revisión. Encontrar el efecto invertido en un país
más no es un hallazgo estructural; es una réplica que cae del lado que la
literatura ya sabía que existía.

Aporte real, entonces: **replicación en un país nuevo con mejor denominador.** Ni
mecanismo nuevo, ni condición de contorno. Está bien —es publicable— pero hay que
decirlo así.

### Veredicto

> **(b) Acá hay una nota de blog muy buena, no todavía un paper.**

Tres líneas de justificación:

1. **El hallazgo principal no está identificado.** La inversión del efecto es del
   mismo orden de magnitud que el sesgo de imputación que medí (+17% en el
   denominador de las unidades chicas, correlacionado con la variable explicativa)
   más el artefacto de maternidad, que no está acotado en ninguna parte. Y la forma
   del efecto —un escalón único en el decil superior, sin gradiente debajo— es la
   firma esperada del artefacto, no la de un entorno.
2. **El mecanismo está medido sobre una muestra seleccionada por el desenlace.**
   H3 sostiene todo el «¿y?» del trabajo y su muestra está enriquecida ×2,7 en
   seleccionados y vaciada ×5,5 del resto.
3. **Hay un bug que contamina el ranking departamental** (110 jugadores fantasma;
   dos departamentos del top-12 nacional con cuenta verdadera cero).

Ninguna de las tres es fatal para el proyecto. Las tres son fatales para *este*
borrador.

**Qué hace falta para que sea (a):** los seis puntos bloqueantes de la Fase 4. No
requieren infraestructura nueva —el pipeline está construido y reproduce— sino
trabajo de validación. Es cuestión de una a dos semanas, no de otro proyecto.

**Si llegara a (a), dónde:** *Journal of Human Kinetics* (publicó la revisión de
2024, tiene apetito por el tema), *International Journal of Sports Science &
Coaching*, o *Frontiers in Sports and Active Living*. No *Journal of Sports
Sciences*, salvo que la validación de `P19` salga excepcionalmente bien.

**El argumento con el que el revisor más hostil lo rechaza, en su forma más
fuerte:**

> «Los autores miden dónde se registró un nacimiento, no dónde se crió un
> deportista. Su denominador por debajo del nivel provincial es una imputación
> cuyo error es del 17% en las unidades más chicas y está correlacionado con la
> variable explicativa. La inversión que reportan es del mismo orden que la suma
> del sesgo de imputación y del artefacto de captación de maternidades, que no
> acotan. El argumento de simetría numerador-denominador que ofrecen como defensa
> es válido a nivel provincial y ellos lo aplican a nivel de ciudad, que es donde
> vive su hallazgo. Sin una validación de `P19` contra un padrón independiente, el
> resultado central no está identificado; y el mecanismo que proponen se estima
> sobre una submuestra seleccionada por el desenlace que quiere explicar.»

Ese párrafo se puede desactivar entero. Hoy no está desactivado.

---

## Fase 4 — Plan de mejora

Separado como se pidió: **arreglar un error** (`FIX`) vs **esto ya es otro paper**
(`OTRO`).

### Bloqueante — sin esto no hay paper

| # | Qué | Dato que hace falta | Esfuerzo | Tipo |
|---|---|---|---|---|
| B1 | **Arreglar el bug de granularidad `provincia`.** Agregar `"provincia"` a `demasiado_grueso` en `src/clean/geocode_places.py:267`, o resolver esos 110 casos solo a nivel provincial. Re-correr todo el pipeline. | ninguno | 1 h + re-corrida | `FIX` |
| B2 | **Validar `P19` contra una fuente independiente.** Muestra estratificada de 150–200 jugadores por tramo de tamaño; contrastar lugar de nacimiento contra ficha de club, BDFA o prensa. Reportar tasa de error **por tramo** — el sesgo importa solo si es diferencial. | trabajo manual o semi-automático; ninguna fuente prohibida | 2–3 días | `FIX` |
| B3 | **Acotar el artefacto de maternidad.** Primer paso: establecer con la documentación del DEIS y del RENAPER **cuál es el criterio real de cada serie** — el paper lo afirma y yo no pude verificarlo (dan lo mismo a nivel provincial, ver punto 1). Si existe una tabulación por residencia de la madre, contrastarla contra la de ocurrencia y medir cuánto del déficit de los pueblos sobrevive al cambio de criterio. Si no existe desagregación sub-provincial, **decirlo y bajar el tono del §2.1**, que hoy afirma la simetría como hecho. | documentación metodológica DEIS/RENAPER; tabulación por residencia **si existe** (no verificado) | 2 días | `FIX` |
| B4 | **Unificar el denominador de H4.** `src/analysis/run_levels_and_flow.py:39-40` → usar `nacimientos_cohorte`. Re-correr §3.4. | ninguno | 1 h | `FIX` |
| B5 | **Degradar H3 o restringirlo.** Opción A: restringir a T1+T2 (cobertura 90–97%) y reportarlo como hallazgo *sobre la elite*, no sobre la población. Opción B: retirar «10 clubes = 48%» y el 47,1% del abstract y del README. En cualquier caso: **H3 no puede seguir siendo la explicación causal de H1** en el §4.1. | ninguno | 1 día (mayormente reescritura) | `FIX` |
| B6 | **Reportar tamaño de efecto de la regresión y corregir la monotonía.** Publicar pseudo-R² (0,011) y devianza explicada (2,6%). Reemplazar «crece de forma monótona» por la descripción correcta: escalón en el decil superior, sin señal por debajo de ~10k. Corregir el subtítulo de la Figura 7 y la errata 3.476 → 3.459. | ninguno | 2 h | `FIX` |

### Importante — sin esto el paper sale débil

| # | Qué | Esfuerzo | Tipo |
|---|---|---|---|
| I1 | **Shrinkage / empirical Bayes** en tasas departamentales, más funnel plot. Mapear estimaciones encogidas o filtrar la Figura 1 por `reportable`. Elimina de un saque el problema de las colas. | 1 día | `FIX` |
| I2 | **Reencuadrar o retirar la comparación con población general** (47,1% vs 13,8%). No es reparable con `P14`, que no tiene edad. Sacarla del abstract. | 2 h | `FIX` |
| I3 | **Corrección por comparaciones múltiples en los contrastes confirmatorios**, no solo en los exploratorios. | 3 h | `FIX` |
| I4 | **Incorporar H1 × cohorte al pipeline** (ya lo corrí: RR plano 0,34–0,55) y confrontar el §4.1 con el resultado. Si el mecanismo de centralización no predice esto, decirlo. | 3 h | `FIX` |
| I5 | **Reescribir §4.1 y §4.4 en registro descriptivo.** Nueve frases marcadas en el punto 8. Sin controles no hay causalidad; o se agregan los controles, o se cambia el verbo. | 4 h | `FIX` |
| I6 | **Limpiar `outputs/`.** Borrar o mover las tres tablas obsoletas; agregar un `_run.json` con fecha, commit y config hash a cada corrida. | 1 h | `FIX` |
| I7 | **Depurar el bin `<10k`.** Decidir explícitamente qué se hace con las 264 «localidades» de menos de 100 habitantes y con `ZONA RURAL`. Como mínimo, reportar H1 con y sin ellas. | 4 h | `FIX` |
| I8 | **Corregir el §1.1 y el §4.1 frente a la revisión de 2024.** Reconocer que la evidencia en fútbol ya era mixta y que la proximidad a centros de rendimiento ya era uno de sus ejes. Verificar o retirar la cifra del 38%. | 3 h | `FIX` |

### Nice to have

| # | Qué | Esfuerzo |
|---|---|---|
| N1 | H2 a nivel aglomerado, no solo departamento. | 4 h |
| N2 | Sensibilidad del tamaño de ciudad con población histórica de localidad (censos 1991/2001/2010), que `config.yaml:238` ya deja preparado. | 2 días |
| N3 | Cartograma y mapa de flujos en versión interactiva. | 1 día |

### Esto ya es otro paper — no lo metas en este

| Qué | Por qué es otro paper |
|---|---|
| **Distancia a academia como covariable** | Requiere georreferenciar los sistemas de inferiores y la capacidad de pensión por año. Es un dataset propio y no existe. |
| **Controles socioeconómicos** (NBI, densidad de ligas locales) | Cambia la pregunta de «dónde nacen» a «qué explica dónde nacen». Es un diseño distinto. |
| **El paper de formación en serio** | H3 hecho bien necesita un dataset real de club formador, no `P54` de Wikidata. Ese es el trabajo valioso que el `CLAUDE.md` §5 identifica como «la versión fuerte», y es un estudio completo por sí mismo. |
| **Fútbol femenino** | Cobertura y literatura distintas, como el propio `config.yaml:35` argumenta. |

---

## Resumen de una línea

El pipeline es sólido y reproduce; el denominador de nacidos vivos es una mejora
real sobre la literatura; y el hallazgo central no está identificado porque el
sesgo de imputación medido, el artefacto de maternidad no acotado y un bug de 110
jugadores fantasma empujan todos en la misma dirección que el titular.
