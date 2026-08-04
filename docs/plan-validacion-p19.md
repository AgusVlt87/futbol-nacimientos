# Plan de validación del `P19`

El último bloqueante del estudio. Este documento fija el diseño; el muestreo lo
genera `src.analysis.build_muestra_validacion` y la corrección la calcula
`src.analysis.run_correccion_p19` una vez que la planilla está codificada.

---

## 1. Qué hay que medir, exactamente

No es «la tasa de error del `P19`». Un error **uniforme** no rompe el estudio:
atenúa el efecto hacia el nulo, de modo que el hallazgo publicado sería una cota
inferior. Lo que rompe el estudio es un error **diferencial por tamaño de
ciudad** —que a los nacidos en pueblos se les asigne mal el lugar más seguido que
a los nacidos en metrópolis—, porque eso puede fabricar el gradiente entero.

Entonces la cantidad a estimar no es un escalar sino una **matriz de mala
clasificación**: dado que un jugador nació realmente en un lugar del tramo *i*,
¿con qué probabilidad Wikidata lo ubica en el tramo *j*? Con esa matriz no se
acota el sesgo: se **corrige** la estimación.

---

## 2. La restricción que define todo el diseño

**El `P19` sale de Wikipedia.** Se consultó la procedencia de las declaraciones
`P19` de una muestra de 400 jugadores del estudio:

| Referencia de la declaración `P19` | Jugadores |
|---|---:|
| «importado de Wikipedia en español» | 167 |
| «importado de Wikipedia en inglés» | 109 |
| «importado de Wikipedia en italiano» | 54 |
| otras Wikipedias | 27 |
| **fuente externa real (Transfermarkt)** | **3** |
| sin ninguna referencia | 34 |

El 91,5 % «tiene referencia», pero es una importación automática desde una
Wikipedia. **Tres de cuatrocientos** tienen una fuente externa.

De ahí se siguen dos cosas, y la segunda es la que suele pasarse por alto:

1. **Wikipedia no puede ser el patrón de oro**, porque es el origen del dato.
   Contrastar `P19` contra la Wikipedia de la que fue importado no valida nada:
   mide la fidelidad del bot, que es cercana al 100 %.
2. **Sí puede ser un tamizaje**, si se usa una Wikipedia *distinta* de la de
   origen. Los artículos en español, inglés e italiano los escriben personas
   distintas; cuando discrepan, hay algo para mirar.

**No existe fuente externa que se pueda automatizar.** Se revisó cada candidata
contra su `robots.txt` y sus términos, que son documentos distintos y no siempre
dicen lo mismo:

| Fuente | `robots.txt` | Términos de uso | Veredicto |
|---|---|---|---|
| **BDFA** | bloquea `ClaudeBot`, `curl`, `wget`, `Python-requests`, `/lista_jugadores.asp?*` y `/api_jugadores_ajax.asp`; `Crawl-delay: 10` | — | **prohibido**, y de forma explícita |
| **Transfermarkt** | `Allow: /`; solo excluye `/ceapi`, `/quickselect`, `/jumplist`, `/navigation/getSubNavigation`. Las rutas de ficha **están permitidas** | §11: prohíbe «bots, spiders, screen scraping u otros procesos automatizados» | **prohibido por los términos**, no por el `robots.txt` |
| **AFA** | solo excluye `/cache/`: **permite el rastreo** | — | permitido, pero **no publica el campo** |

El caso de Transfermarkt merece una nota porque es contraintuitivo y este
proyecto lo tuvo mal documentado un tiempo: su `robots.txt` **no** prohíbe leer
las fichas de jugador. La restricción vive en los términos de uso, que son un
documento aparte y que hay que leer aparte. Afirmar «lo prohíbe el `robots.txt`»
era falso; afirmar «está prohibido» es cierto, pero por otra vía.

Por eso el patrón de oro tiene que construirse a mano, caso por caso.

---

## 3. Tamaño de muestra

Contraste principal: tasa de error en «fuera de un gran aglomerado» contra «en un
gran aglomerado». Dos proporciones, α = 0,05 bilateral, potencia 80 %.

| Error en metro | Error en interior | n por grupo | n total |
|---:|---:|---:|---:|
| 5 % | 15 % | 141 | 282 |
| 5 % | 20 % | 76 | **152** |
| 5 % | 25 % | 49 | 98 |
| 10 % | 25 % | 100 | 200 |
| 10 % | 30 % | 62 | 124 |

Y la precisión para **estimar** —que es lo que hace falta para corregir, no solo
para detectar—:

| n por estrato | IC 95 % si el error real es 15 % | ancho |
|---:|---|---:|
| 100 | 8,6 % – 23,5 % | 15 pts |
| 150 | 9,4 % – 21,4 % | 12 pts |
| 200 | 10,4 % – 20,7 % | 10 pts |

**Recomendación: 150 por brazo, 300 en total.** Detecta con holgura una
diferencia de 10 puntos y da una matriz de mala clasificación con precisión
suficiente para corregir. Con 152 alcanza para detectar 5 % vs 20 %, pero los
intervalos quedan demasiado anchos para corregir con ellos.

---

## 4. Diseño en dos fases

Codificar 300 casos a mano es caro. El muestreo en dos fases lo abarata sin
perder validez.

### Fase A — tamizaje automático sobre los 5.248 (gratis)

Para cada jugador se extrae el campo **del infobox** —no de la prosa— de todas
las Wikipedias donde tenga artículo:

- `es`: `lugar de nacimiento` / `nacimiento`
- `en`: `birth_place`
- `it`: `luogo di nascita`

Se usa el infobox y no el texto libre porque el matching sobre prosa da falsos
desacuerdos: la Wikipedia inglesa a menudo omite el lugar o lo escribe con otra
granularidad. En una prueba de 20 casos con matching de texto plano, 14 daban
«discrepa» y casi todos eran artefactos de la extracción.

Salida: bandera `discrepancia_idiomas` ∈ {sin\_datos, coinciden, discrepan}.

**Esta bandera no es la verdad.** Es un predictor barato de dónde está la verdad.

### Fase B — codificación manual estratificada (300 casos)

Se estratifica por **tamaño de ciudad × bandera de tamizaje** y se asigna la
muestra con más peso donde se espera más error (asignación de Neyman). Los
estratos sobremuestreados se reponderan al estimar, de modo que la estimación
sigue siendo insesgada para la población.

Reglas del protocolo:

1. **Dos codificadores independientes.** Se reporta el acuerdo entre ambos
   (κ de Cohen) antes de cualquier resultado. Un κ bajo invalida la medición.
2. **Ciego al estrato.** La planilla no muestra el tramo de tamaño ni la bandera
   de tamizaje, y las filas van mezcladas. Si el codificador sabe que está
   mirando un caso «de pueblo», busca distinto.
3. **Ciego al `P19`, en lo posible.** El codificador escribe primero el lugar
   que encuentra en las fuentes, y recién después el sistema lo compara con el
   `P19`. Evita el sesgo de confirmación.
4. **Se registra la fuente usada** (URL o cita) para cada caso. Sin fuente, el
   caso queda como `no_verificable`, que es un resultado y no un descarte.
5. **No se usan fuentes prohibidas.** BDFA y Transfermarkt quedan afuera.
   Admisibles: sitio oficial del club, prensa del debut, entrevistas, archivos
   provinciales, actas municipales, el propio jugador en redes.

### Taxonomía del desenlace

No alcanza con «correcto / incorrecto». Se codifica el **tipo**, porque cada uno
tiene una consecuencia distinta sobre la estimación:

| Código | Qué pasó | Efecto sobre el estudio |
|---|---|---|
| `exacto` | `P19` coincide con la localidad real | ninguno |
| `cabecera` | nació en un pueblo, figura la ciudad cabecera | **el artefacto que se busca** |
| `grueso` | figura la provincia o el departamento | ya se excluye; confirma §3.6 |
| `otra_localidad` | otra localidad del mismo tramo | ruido, no sesgo |
| `otro_tramo` | otra localidad de otro tramo | sesgo, dirección a medir |
| `crianza` | figura donde se crió, no donde nació | inverso del artefacto |
| `no_verificable` | no se encontró fuente | se reporta aparte |

---

## 4-bis. Cuánto error haría falta para que importe

Antes de gastar veinte horas conviene saber cuánto está en juego. La maquinaria
de corrección ya está construida, así que se puede simular: se postula una tasa
de mala clasificación, se corrige el conteo y se mira dónde queda el RR.

Barriendo el escenario que preocupa —jugadores del interior registrados en la
metrópoli, que es el artefacto de la maternidad de cabecera—:

| % mal clasificado | RR corregido | IC 95 % | ¿sigue ≠ 1? |
|---:|---:|---|---|
| 0 % | 0,53 | 0,47–0,58 | sí |
| 10 % | 0,64 | 0,54–0,74 | sí |
| 20 % | 0,76 | 0,62–0,93 | sí |
| **25 %** | **0,81** | **0,65–1,02** | **no** |
| 35 % | 0,88 | 0,68–1,13 | no |
| 50 % | 1,03 | 0,73–1,44 | no |

**El punto de quiebre está en el 25 %.** Para que el hallazgo se caiga, uno de
cada cuatro futbolistas registrados en un gran aglomerado tendría que haber
nacido en realidad fuera de él.

Eso calibra la expectativa en dos direcciones. Hacia abajo: con un 10 % de error
el resultado apenas se mueve, así que un error moderado no cambia nada. Hacia
arriba: un cuarto es mucho, pero no es absurdo para un país donde el parto ocurre
en la cabecera departamental, y por eso hay que medirlo en vez de suponerlo.

**Cuidado con la dirección.** El parámetro que importa es el error entre los
observados como metrópoli —gente que figura ahí y viene del interior—. El error
en la dirección contraria *refuerza* el hallazgo en vez de debilitarlo. Es fácil
invertirlo al leer una tabla de resultados; está documentado en el docstring de
`simular()`.

Reproducir: `python -m src.analysis.run_correccion_p19 --curva`

---

## 5. Qué se hace con el resultado

Con la matriz **M** de mala clasificación estimada, el estudio pasa de acotar a
corregir:

1. **Corrección del vector de conteos.** Si `n_obs` es el vector observado por
   tramo y `M` la matriz estimada, el vector corregido es la solución de
   `M' · n_real = n_obs`. Se propaga la incertidumbre de `M` por bootstrap y se
   recalcula el RR con su intervalo.
2. **Análisis de sesgo cuantitativo.** Se reporta el RR observado, el corregido y
   el rango que resulta de la incertidumbre de `M`. Reemplaza a las dos cotas que
   hoy tiene el paper (44,5 % de maternidad, 0,45 → 0,96 de granularidad) por un
   intervalo estimado.
3. **Si el error resulta no diferencial**, el hallazgo queda establecido y el
   trabajo pasa de «plausible» a «establecido»: es el escenario en que el paper
   se publica sin asteriscos.
4. **Si resulta diferencial y grande**, el hallazgo principal se cae —y eso
   también es un resultado publicable, porque documenta un modo de falla que
   afecta a toda la literatura que use corpus colaborativos.

Las cuatro salidas son informativas. Ese es el sentido de hacerlo.

---

## 6. Esfuerzo estimado

| Tarea | Esfuerzo |
|---|---|
| Fase A: tamizaje automático (código + corrida) | 1 día |
| Fase B: 300 casos × 2 codificadores, ~4 min por caso | ~20 h de trabajo humano, repartibles |
| Adjudicación de desacuerdos entre codificadores | 3 h |
| Corrección y reescritura de §3.1, §3.6 y §4.3 | 1 día |

Es un fin de semana de dos personas, no un programa de investigación. Y es lo
único que separa a este trabajo de estar cerrado.

---

## 7. Lo que ya está construido

- `src.analysis.build_muestra_validacion` — genera la muestra estratificada, la
  mezcla, oculta el estrato y escribe la planilla de codificación en blanco.
- `src.analysis.run_correccion_p19` — consume la planilla codificada, calcula el
  acuerdo entre codificadores, estima la matriz de mala clasificación y produce
  el RR corregido con su intervalo por bootstrap.

Falta únicamente el juicio humano: llenar la planilla.
