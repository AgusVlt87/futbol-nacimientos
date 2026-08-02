# Re-análisis — tercera pasada

**Fecha:** 2026-08-02 · **Commit:** `3f07dba` (+ working tree sin commitear)
**Snapshot Wikidata:** 2026-07-30
**Alcance:** Parte 1 diagnóstico independiente, Parte 2 expansión. No se tocó código.

---

## Aviso previo: la lectura ciega salió parcialmente comprometida

La Fase 0 pedía no abrir `CLAUDE.md` antes de mirar la evidencia. **El harness lo
inyecta automáticamente en el contexto al arrancar la sesión**, así que llegué a
los datos habiendo leído ya el planteo del proyecto, las hipótesis y —lo más
contaminante— la sección «Trampas encontradas», que anticipa varios hallazgos.

Lo que sí se respetó: no abrí `README.md`, `reports/paper.md` ni `docs/roast.md`
hasta terminar la Fase 1. El anclaje contra la *crítica anterior* está intacto;
el anclaje contra la *narrativa del propio repo* no del todo. Los dos hallazgos
principales de esta pasada (§1.4) no están en `CLAUDE.md` ni en ningún otro
documento del repo, así que no los heredé de ahí.

**Reproducción.** `python -m src.analysis.run_all` corre limpio y `git diff` sobre
`outputs/tables/` queda vacío. Todo lo que sigue es reproducible.

---

# PARTE 1 — DIAGNÓSTICO

## 1.1 Qué pregunta contestan estos datos

Literalmente, y sin adornos:

> De cada 100.000 nacimientos **registrados** en un lugar de la Argentina entre
> 1975 y 2008, ¿cuántos corresponden a personas que hoy tienen una entrada de
> Wikidata que las describe como futbolistas profesionales y que declara ese
> lugar en `P19`?

Las tres piezas de esa frase importan:

- **«Registrados»** — el denominador provincial es el conteo del DEIS de nacidos
  vivos; el numerador es lo que un editor de Wikipedia escribió como lugar de
  nacimiento. Que las dos cosas signifiquen lo mismo es un supuesto, no un dato
  (ver §1.3).
- **«Entrada de Wikidata»** — no es un padrón de futbolistas profesionales. Es un
  corpus de notabilidad.
- **Por debajo de provincia**, el denominador ya no es un conteo: es un reparto
  del total provincial según población censal
  ([build_denominators.py:118-127](src/clean/build_denominators.py#L118-L127)).

## 1.2 Qué sostienen los datos, y con qué alcance

Lo que encontré antes de leer nada del repo:

**A. El *birthplace effect* clásico no aparece; aparece invertido.**
[h1_tramos_principal.csv](outputs/tables/h1_tramos_principal.csv): 12,9 futbolistas
cada 100.000 nacidos en localidades `<10k` contra 30,5 en aglomerados `>500k`
(RR 0,42; IC 0,38–0,47). El tramo 50–100k, el óptimo que predice la literatura,
no muestra pico. Alcance: sostenido, con la salvedad de §1.4.

**B. El gradiente es idéntico en los cuatro niveles competitivos.** Esto lo
verifiqué yo y es más fuerte de lo que parece.
[h4_tramos_por_nivel.csv](outputs/tables/h4_tramos_por_nivel.csv), RR `<10k` vs `>500k`:

| Nivel | RR | Cobertura de Wikidata |
|---|---:|---|
| T1 selección mayor | 0,489 | prácticamente censal |
| T2 Europa top | 0,363 | muy alta |
| T3 Primera AR | 0,424 | media |
| T4 resto | 0,425 | baja |

**Si el efecto lo fabricara la cobertura de Wikidata, T1 debería mostrar el
gradiente más débil. Muestra el mismo.** Esta es la mejor defensa que el proyecto
tiene y sobrevive intacta a todo lo demás de este documento.

**C. La distribución por tamaño no varía con la notoriedad del jugador.** Corté la
muestra por `sitelinks` (número de Wikipedias con artículo). % de jugadores
nacidos en `>500k`:

| sitelinks | n | % en `>500k` |
|---|---:|---:|
| 1 | 1.130 | 62,8 |
| 2–3 | 776 | 63,0 |
| 4–9 | 2.482 | 63,7 |
| 10+ | 860 | 65,3 |

Descarta la hipótesis de que «Buenos Aires» sea la etiqueta perezosa que se le
pone al jugador poco documentado. Es un chequeo que el repo no hace y que sale
a favor del repo.

**D. Hay cunas reales de ciudad chica, y el análisis por tramos las entierra.**
Ordenando ciudades con más de 20.000 nacimientos en la ventana: Rafaela 98,0 ·
Gran Santa Fe 72,8 · Concordia 66,9 · Gran Rosario 58,3 · Casilda 57,1 ·
Pergamino 55,2 · Tandil 53,6 · Junín 46,3 · Balcarce 42,9 — contra Gran Buenos
Aires 31,2. El promedio del tramo `<10k` (12,9) es un promedio sobre miles de
localidades con cero. **La heterogeneidad dentro del tramo es mucho más grande
que la diferencia entre tramos**, y las tablas de cinco filas no la muestran.

## 1.3 Tres explicaciones alternativas

**Alternativa 1 — El parto ocurre donde hay maternidad.** Un chico de un pueblo de
3.000 habitantes nace en la cabecera departamental. Vacía el tramo chico y llena
el grande, en el numerador. *Qué haría falta:* la serie de nacidos vivos por
**residencia de la madre** contrastada contra la de ocurrencia. **Existe** y está
verificada (§2.A1).

**Alternativa 2 — Wikidata no enumera futbolistas, enumera notables, y el umbral
de notabilidad es geográfico.** Un jugador con 200 partidos en el Torneo Federal A
no tiene artículo; uno con 3 partidos en Boca sí. *Qué haría falta:* un padrón
independiente de futbolistas profesionales. *Estado:* **parcialmente descartada
por B**, que es el argumento fuerte del repo.

**Alternativa 3 — Migración interna de las familias.** Un chico nacido en
Santiago del Estero en 1980 y criado en La Matanza cuenta como NOA. *Dirección:*
esto **infla** el interior, o sea empuja contra el hallazgo. *Qué haría falta:*
lugar de crianza o de club formador. No existe en el pipeline.

## 1.4 Abogado del diablo — y acá aparece lo que nadie vio

Construí el mejor caso posible de que el resultado más llamativo es un artefacto.
Encontré dos defectos **verificables y no declarados en ninguna parte del repo**.

### Defecto 1 — Los códigos de departamento cambian entre censos y el pipeline no lo maneja

`participacion_departamental()`
([build_denominators.py:109-115](src/clean/build_denominators.py#L109-L115)) reparte
los nacimientos provinciales usando el censo más cercano al año de nacimiento
(1991, 2001, 2010, 2022). Pero **44 de 532 departamentos no existen en los cuatro
censos**, porque el INDEC recodificó partidos: 19 aparecen en un solo censo y 25
en tres.

Concordia (Entre Ríos) es `30014` en 1991 y `30015` desde 2001. Como los
nacimientos 1975–1996 se asignan al censo 1991 y los posteriores a 2001+, **los
nacimientos de Concordia quedan partidos entre dos códigos distintos**:

```
dept 30015 (Concordia, geografía 2022): 36.775 nacimientos 1975–2008, 23 jugadores
dept 30014 (Concordia, código 1991):    66.988 nacimientos,            0 jugadores
```

Los jugadores se geocodifican contra Georef, que devuelve códigos 2022, así que
**los 23 jugadores de Concordia caen todos en `30015`, contra un tercio de sus
nacimientos**. Tasa publicada: 62,5 por 100.000. Tasa real: en torno a 22.

El total provincial se conserva (Entre Ríos suma 762.141 en los dos casos), por
eso el error es invisible: **solo se rompe el reparto interno**.

**Lo mismo pasa en el Gran Buenos Aires, y ahí pesa mucho más.** Los partidos que
se subdividieron en 1994 (General Sarmiento → San Miguel / José C. Paz / Malvinas
Argentinas; Morón → Morón / Hurlingham / Ituzaingó; Esteban Echeverría → Esteban
Echeverría / Ezeiza) tienen todos sus nacimientos 1975–1996 en códigos que ya no
existen.

Consecuencia directa: en
[build_denominators.py:202](src/clean/build_denominators.py#L202) el
`merge(..., how="left")` contra `tamano_localidad` —que solo tiene geografía
2022— **descarta en silencio los departamentos con código viejo**:

```
denominador por departamento:  22.997.565 nacimientos
denominador por ciudad:        21.948.264 nacimientos
                               ─────────────────────
perdidos:                       1.049.301  (4,6 %)
```

De ese millón, **727.803 son partidos del Gran Buenos Aires**. El efecto es
inflar la tasa de los aglomerados grandes, que es exactamente la dirección del
titular.

Efecto en el ranking departamental —donde el daño es mayor—:

| Depto | Tasa publicada | Problema |
|---|---:|---|
| 06505 Magdalena | 162,98 | denominador truncado |
| 06568 Morón | 93,08 | denominador truncado |
| 30015 Concordia | 62,54 | denominador truncado |
| 06270 Ezeiza | 54,22 | denominador truncado |
| 94007 (T. del Fuego) | **0,00** | 33.605 nacimientos, 0 jugadores: departamento fantasma |

**La cabecera del ranking departamental y la clase de color más oscura de la
Figura 1 están dominadas por departamentos afectados.**

*Cota del daño sobre H1:* si se devuelve todo el millón perdido al tramo `>500k`
(cota superior), la tasa baja de 30,5 a 27,8 y el RR del `<10k` sube de 0,424 a
0,464. **H1 sobrevive**: 12,9 sigue muy por debajo de 27,8. El defecto es grave
para el mapa departamental y para las cunas, no para el titular de H1.

### Defecto 2 — La lista de partidos del AMBA en `config.yaml` está corrida

[config.yaml:144-168](config.yaml#L144-L168) enumera los 24 partidos del Gran
Buenos Aires con un comentario por línea. **Contrasté cada código contra
`c2022_codigos_departamentos.xlsx`, el padrón oficial del INDEC que el propio
repo descarga: 12 de los 24 códigos apuntan a otro departamento que el que dice
el comentario.**

| En config | Comentario | Lo que ese código es en INDEC 2022 |
|---|---|---|
| `06441` | Lomas de Zamora | **La Plata** |
| `06490` | Malvinas Argentinas | **Lomas de Zamora** |
| `06515` | Merlo | **Malvinas Argentinas** |
| `06525` | Moreno | **Marcos Paz** |
| `06529` | Morón | **no existe** |
| `06560` | Quilmes | **Moreno** |
| `06568` | San Fernando | **Morón** |
| `06638` | San Isidro | **Pilar** |
| `06648` | San Miguel | **Presidente Perón** |
| `06749` | Tigre | **San Fernando** |
| `06756` | Tres de Febrero | **San Isidro** |
| `06805` | Vicente López | **Tigre** |

La lista está desplazada un lugar a partir de Lomas de Zamora. Resultado: el
«AMBA» del estudio **excluye Merlo, Quilmes, San Miguel, Tres de Febrero y
Vicente López** (`06539`, `06658`, `06760`, `06840`, `06861`, ninguno en la lista)
**e incluye La Plata, Marcos Paz, Pilar y Presidente Perón**, que no son GBA.

No es un desajuste numerador/denominador —`region_of()`
([geo_units.py:92-112](src/clean/geo_units.py#L92-L112)) usa la misma lista para
las dos puntas— pero **la variable no mide lo que su nombre dice**, y el resultado
cambia de signo.

Recalculado con los 24 códigos correctos, más los cuatro códigos viejos del GBA
reasignados:

| Región | Publicado | Corregido | Δ |
|---|---:|---:|---:|
| **Pampeana** | 29,54 | **34,55** | +17 % |
| **AMBA** | **35,03** | 28,27 | −19 % |
| Cuyo | 15,22 | 15,22 | — |
| Patagonia | 12,71 | 12,71 | — |
| NEA | 9,58 | 9,58 | — |
| NOA | 8,20 | 8,20 | — |

**El orden se da vuelta: la región pampeana pasa a producir más que el AMBA.**
Y el contraste central:

| | Publicado | Corregido |
|---|---:|---:|
| AMBA | 35,03 | 28,27 |
| Interior | 20,02 | 21,55 |
| **RR Interior/AMBA** | **0,572** | **0,762** |

La brecha se achica un 45 %. El numerador casi no se mueve (1.859 → 1.872), porque
lo que entra (Quilmes 83, Vicente López 34, Tres de Febrero 32, Merlo 31, San
Miguel 14) casi compensa lo que sale (La Plata 155, Pilar 21). **Lo que se mueve
es el denominador: 5,31 M → 6,62 M.**

**Veredicto del abogado del diablo:** el caso *sí* sale convincente, pero no
contra todo el trabajo. Contra:

- el mapa departamental y el ranking de cunas → **contaminados**;
- la afirmación «la producción se concentra en el AMBA» → **se da vuelta**;
- el titular de H1 (más grande = más futbolistas) → **sobrevive**, con el efecto
  algo más chico;
- el contraste centro/norte (Pampeana 34,6 vs NOA 8,2) → **intacto**;
- el resultado juveniles → Mayor (§3.5 del paper) → **intacto**, no usa
  denominador.

### Defecto 3 (menor) — Dos denominadores distintos conviviendo

[h2_regiones.csv](outputs/tables/h2_regiones.csv) y
[h4_regiones_por_nivel.csv](outputs/tables/h4_regiones_por_nivel.csv) reportan
nacimientos distintos para la misma región:

| Región | h2 (por departamento) | h4 (por ciudad) | Δ |
|---|---:|---:|---:|
| Pampeana | 8.801.582 | 7.833.752 | −967.830 |
| Patagonia | 1.204.246 | 1.144.460 | −59.786 |
| NEA | 2.663.171 | 2.641.486 | −21.685 |

Las diferencias son **exactamente** los departamentos huérfanos del Defecto 1. Es
el mismo bug visto desde otro lado, y hace que las tablas de H2 y las de H4 /
selección no sean comparables entre sí.

---

## 1.5 Fase 2 — Contraste con lo que el repo afirma

Acá viene la parte que me obliga a ser justo: **el paper es notablemente
autocrítico y ya declara casi todo lo que encontré por mi cuenta en §1.1–1.3.**
El artefacto de maternidad está como limitación 1 de §4.3, el sesgo direccional
del reparto está medido en §2.1 con su Figura 19, el tamaño de efecto chico está
reportado, la forma de escalón está reportada, la selección por desenlace de H3
está declarada. Un documento que dice «la defensa metodológica más fuerte del
estudio no aplica en el nivel donde se mide el efecto principal»
([paper.md:148-150](reports/paper.md#L148-L150)) no está escondiendo la pelota.

Los deltas que quedan, entonces, son pocos pero concretos.

### Afirmación sin respaldo

**(a) «El reparto intraprovincial es el único supuesto de la cadena»**
([paper.md:111](reports/paper.md#L111)). Falso: hay un segundo supuesto no
declarado y no cumplido, que la geografía departamental es estable entre 1991 y
2022. Los Defectos 1 y 2 viven ahí.

**(b) «El orden de las provincias no cambia con ninguno de ellos»**
([paper.md:154](reports/paper.md#L154)) y «se probaron seis denominadores
distintos» ([paper.md:325](reports/paper.md#L325)). Los seis denominadores comparten
la misma cadena de reparto y el mismo padrón geográfico. Probar seis variantes de
un mismo estimador no es robustez ante el error que ese estimador tiene.

**(c) La tabla regional de §3.2 no coincide con las tablas del repo.** Cinco de
seis filas están desactualizadas:

| Región | Paper §3.2 | h2_regiones.csv |
|---|---:|---:|
| AMBA | 1.859 / 35,0 | 1.859 / 35,03 ✓ |
| Pampeana | 2.659 / 30,2 | 2.600 / 29,54 ✗ |
| Cuyo | 280 / 16,1 | 265 / 15,22 ✗ |
| Patagonia | 159 / 13,2 | 153 / 12,71 ✗ |
| NEA | 269 / 10,1 | 255 / 9,58 ✗ |
| NOA | 285 / 8,7 | 269 / 8,20 ✗ |

Los números del paper suman 5.511; los de la tabla, 5.401. **El paper conserva la
tabla de antes del arreglo de los 110 jugadores fantasma.** El χ² también quedó
viejo (1.050,7 en el paper contra 1.094,4 en `tests_bondad_ajuste.csv`).

### Salto de alcance

**(d)** §4.2: «el AMBA pasó de estar por debajo de la región pampeana a estar por
encima» ([paper.md:527-528](reports/paper.md#L527-L528)) — presentado como una
lección metodológica sobre el denominador. Con la definición correcta de AMBA
**esa inversión no ocurre**: la pampeana sigue arriba. La lección general es real
(las áreas metropolitanas tienen menos hijos por habitante) pero el ejemplo
elegido para ilustrarla es el artefacto.

**(e)** Resumen: «CABA produce 2,6 veces lo que le correspondería»
([paper.md:37](reports/paper.md#L37)). Sostenido aritméticamente, pero CABA es
**la única jurisdicción que la validación del denominador no toca**: verifiqué que
`qa_validacion_denominador_detalle.csv` tiene 511 departamentos de 23 provincias y
**cero filas de CABA** (`dropna` en
[build_denominators.py:139](src/clean/build_denominators.py#L139)). El número que
encabeza H2 es el único sin control de calidad.

### Evidencia desperdiciada

**(f) El test por nivel competitivo está subutilizado.** El paper lo usa en §3.4
como escudo contra el sesgo de cobertura, pero no muestra la comparación que lo
hace contundente: los cuatro RR (0,489 / 0,363 / 0,424 / 0,425) **lado a lado**.
Es el argumento más fuerte del trabajo y está enterrado en una tabla.

**(g) La heterogeneidad dentro de tramo no se explota.** Rafaela produce 98 por
100.000 y el Gran Buenos Aires 31. El paper lo menciona como curiosidad
([paper.md:328-332](reports/paper.md#L328-L332)) y concluye «no alcanza para
sostener el patrón general». Pero la pregunta «¿qué distingue a Rafaela, Casilda,
Pergamino y Tandil del resto de las ciudades de su tamaño?» es más interesante
que el promedio del tramo, y los datos la habilitan.

**(h) La estabilidad por `sitelinks`** (§1.2.C) no está calculada en ningún lado y
es un chequeo de sesgo gratis que sale a favor.

---

## 1.6 Fase 3 — Contraste con `docs/roast.md`

El roast es sólido. Clasificación:

### Convergente (las dos pasadas, por separado — alta confianza)

| Punto | Roast | Esta pasada |
|---|---|---|
| Artefacto de maternidad como amenaza principal | §2 | §1.3 alt. 1 |
| El reparto sub-provincial es imputación, no dato | §1 | §1.1 |
| El efecto es escalón, no gradiente | §D | §1.2.D |
| Números chicos contaminan el ranking departamental | §5 | §1.4 (por otra causa) |
| Cobertura de Wikidata decae con la edad de la cohorte | §3 | §1.2 |
| H3 medido sobre muestra seleccionada por desenlace | §3-bis | coincido |
| Sin controles; §4.1 escrito en clave causal | §8 | coincido |

### Solo el roast — mi veredicto sobre cada uno

- **Validación circular contra RENAPER y CABA excluida (§1).** *El roast tiene
  razón y se me pasó la parte de la circularidad.* Verifiqué la exclusión de CABA:
  511 departamentos, 0 de CABA. Confirmado.
- **Corrección por comparaciones múltiples solo en lo exploratorio (§7).**
  *Correcto y se me pasó.*
- **Figura 7 dibuja y ajusta muestras distintas (§F).** *Correcto.* Está declarado
  en la nota al pie, lo que lo hace honesto pero no lo hace buena práctica.
- **Encuadre frente a la literatura (Fase 3).** *Correcto, y ya fue incorporado* —
  el paper §4.1 ahora dice «no descubre un mecanismo nuevo».
- **Bug de granularidad `provincia`, 110 jugadores fantasma (§4).** *Correcto en su
  momento y **ya está arreglado**.* Verificado: `granularity` tiene 110 casos
  `provincia`, todos con `region` nula y fuera del análisis departamental.
- **B4, H4 con denominador censal.** *Arreglado.* `h4_tramos_por_nivel.csv` ahora
  usa nacimientos.

### Solo esta pasada

- **Discontinuidad de códigos departamentales** (§1.4, Defecto 1). Ni el roast ni
  el paper lo mencionan. 1.049.301 nacimientos desaparecidos.
- **Lista del AMBA corrida en `config.yaml`** (§1.4, Defecto 2). Da vuelta el
  orden AMBA/Pampeana.
- **Dos denominadores conviviendo entre tablas** (§1.4, Defecto 3).
- **Tabla regional del paper desactualizada** (§1.5.c).
- **Estabilidad del efecto por `sitelinks`** (§1.2.C) — a favor del repo.
- **Los cuatro RR por nivel casi idénticos** (§1.2.B) — a favor del repo, y más
  fuerte de lo que el propio paper reclama.

### Contradicción directa

**Una, y creo que el roast se equivoca en el énfasis.**

El roast concluye que «el hallazgo principal no está identificado» porque el sesgo
de imputación (+17 %) más el artefacto de maternidad podrían dar cuenta de la
inversión. **La evidencia del §1.2.B lo contradice y el roast no la usa**: el
gradiente es el mismo en la selección mayor (RR 0,489), donde la cobertura es
censal, que en T4 (0,425). Ninguno de los dos artefactos que el roast invoca
predice esa invariancia — el de maternidad afecta a los seleccionados igual que
al resto, cierto, pero el de cobertura no, y aun así el RR no se mueve.

Sumado a mi propia cota (corregir el Defecto 1 lleva el RR de 0,42 a ≤0,46) y a
la del roast (corregir la imputación lo lleva a ~0,49), **los tres correctivos
juntos dejan el RR en torno a 0,5, todavía a mitad de camino del 1,0 que haría
falta para anular el efecto.** Mi lectura es que H1 está sub-identificado en
magnitud pero no en signo, y que el roast subestima esa diferencia. Donde el roast
acierta de lleno es en el ranking departamental y en las cunas, que sí son
irrecuperables sin arreglos.

Donde el roast se queda corto por el otro lado: dio por buena la geografía. Su
veredicto se apoya en «el código se juzga solo donde compromete un resultado», y
los dos defectos que encontré comprometen resultados publicados.

---

## 1.7 Bloqueantes

Ordenados por cuánto invalidan.

| # | Bloqueante | Qué invalida | Estado |
|---|---|---|---|
| **BL1** | **Códigos de departamento no estables entre censos**; 1.049.301 nacimientos (4,6 %) desaparecen del denominador de ciudad, 727.803 de ellos del GBA | Figura 1, `h2_departamentos`, ranking de cunas, Figura 11; sesga H1 al alza | nuevo |
| **BL2** | **Lista del AMBA corrida en `config.yaml:144-168`**, 12 de 24 códigos erróneos | «AMBA es la región que más produce» (se da vuelta), H2 AMBA/interior, Figuras 3 y 5 | nuevo |
| **BL3** | **Artefacto de maternidad sin acotar** | H1, H2, todo lo que use tasa por nacido a nivel sub-provincial | del roast, sigue abierto |
| **BL4** | **Tasa de error del `P19` sin medir contra padrón independiente** | la muestra entera | del roast, sigue abierto |
| **BL5** | **Sesgo direccional del reparto** (+17 % en el decil chico) | magnitud de H1 | medido y declarado; sin corregir |
| **BL6** | **H3 sobre muestra seleccionada por desenlace** | 47,1 %, «10 clubes = 48 %», retención del NEA | declarado; sigue en el resumen |
| **BL7** | **Tabla regional del paper desactualizada** | §3.2 | trivial de arreglar |

BL1 y BL2 son de arreglo mecánico (horas, no días) y hay que hacerlos **antes**
que cualquier otra cosa, porque cambian los números que todo lo demás cita.

**Lo que no es bloqueante y está bien resuelto:** el cambio a nacidos vivos como
denominador, la resolución geográfica por coordenada contra Georef, el
cuasi-preregistro de `config.yaml`, el doble esquema de cortes, la reproducción
exacta del pipeline, el diseño de §3.5 y el test por nivel competitivo.

---

# PARTE 2 — EXPANSIÓN

Cambio de modo. Todo lo que sigue se apoya en fuentes que verifiqué que existen.

## 2.A — Expansiones que reparan

### A1. Nacidos vivos por **residencia de la madre** — resuelve BL3

**Verificado.** `datos.gob.ar` publica *«Nacidos Vivos Registrados por
Jurisdicción de Residencia de la Madre - República Argentina»* (Ministerio de
Salud, dataset
`nacidos-vivos-registrados-por-jurisdiccion-de-residencia-de-la-madre-republica-argentina`),
con recursos CSV/XLSX por año, cobertura aproximada 2005–2023.

**Qué agrega:** es *la* serie contrafáctica. El repo usa la de nacimientos
**ocurridos** y afirma —sin poder verificarlo— que `P19` sigue la misma
definición. Con las dos series se puede medir, provincia por provincia, cuánta
diferencia hay entre «dónde ocurrió el parto» y «dónde vive la madre». Ese
diferencial es una **cota empírica del artefacto de maternidad**, que hoy no
tiene ninguna.

**Qué la haría fracasar:** la cobertura arranca en 2005, fuera de la ventana
1975–2008. Da una cota contemporánea, no histórica, y hay que declararlo así. Y
es jurisdiccional: no baja a departamento, que es donde más duele.

**Esfuerzo:** 1–2 días. **Marca:** repara BL3 (parcialmente).

### A2. Crosswalk histórico de códigos de departamento — resuelve BL1

**Qué requiere:** ninguna fuente nueva. `pop_dept_historica.parquet` ya tiene la
evidencia; falta la tabla de equivalencias 1991→2001→2010→2022. Se puede construir
semiautomáticamente cruzando geometrías del IGN, o a mano: son 44 departamentos.

**Qué agrega:** devuelve 1.049.301 nacimientos al denominador y corrige el mapa
departamental entero. Es el arreglo con mejor relación resultado/esfuerzo del
proyecto.

**Qué la haría fracasar:** los casos sin correspondencia 1:1 (un partido viejo que
se parte en tres) obligan a repartir por población, que reintroduce un supuesto —
menor que el actual, pero hay que declararlo.

**Esfuerzo:** 1 día. **Marca:** repara BL1.

### A3. Validación de `P19` contra BDFA — resuelve BL4

**Fuente:** `https://www.bdfa.com.ar/` — Base de Datos del Fútbol Argentino, fichas
con lugar de nacimiento y cobertura de ascenso y ligas provinciales. **Verificá
condiciones de uso antes de automatizar nada**; para una muestra de 150–200 fichas
la consulta manual es viable y no plantea problema.

**Qué agrega:** dos cosas distintas. (i) La tasa de error de `P19`, **estratificada
por tramo de tamaño** —solo importa si el error es diferencial—. (ii) Una
estimación de cuántos futbolistas profesionales del interior faltan en Wikidata,
que es la alternativa 2 de §1.3.

**Qué la haría fracasar:** que BDFA copie de Wikipedia. Hay que chequear
independencia de fuentes antes de contar el resultado como validación.

**Esfuerzo:** 2–3 días. **Marca:** repara BL4.

### A4. Éxito graduado en vez de tiers

**Fuente:** Wikidata `P54` con `P580`/`P582` (ya ingestado en `careers.parquet`),
más `P1350` (partidos jugados) donde exista.

**Qué agrega:** T4 «resto» son 2.437 jugadores cuyo único atributo común es tener
artículo. Una variable continua —años de carrera registrados, número de clubes,
máxima liga alcanzada— convierte un residuo en un gradiente y permite preguntar
si el origen predice **cuán lejos** se llega, no solo si se llega.

**Qué la haría fracasar:** `P1350` tiene cobertura muy baja en Wikidata para el
fútbol argentino. Verificar antes de diseñar sobre eso.

**Esfuerzo:** 1 día. **Marca:** mejora la variable dependiente de H4.

## 2.B — Expansiones que amplían

### B1. Test placebo con otro deporte — la validación externa más barata

**Verificado por SPARQL contra el endpoint, hoy.** Argentinos con `P19` y fecha de
nacimiento en la ventana 1975–2008:

| Deporte | n con `P19` en la ventana |
|---|---:|
| Básquet masculino | **396** |
| Rugby masculino | **291** |
| Fútbol femenino | **252** |
| Básquet femenino | 56 |

**Qué agrega:** es la pregunta que más cambia el paper. Si el mapa del básquet
—donde el corredor Bahía Blanca–Junín–Córdoba es folklore conocido— sale distinto
del de fútbol, hay algo específicamente futbolístico y el hallazgo se refuerza. Si
sale idéntico, lo que se está midiendo es infraestructura general o el registro
civil, **y eso reescribe el trabajo entero**. En los dos sentidos es informativo.

**Qué la haría fracasar:** con n=396 alcanza para provincia/región y para el
contraste binario metrópoli vs resto; **no alcanza para los cinco tramos de
tamaño**. Diseñar el test sobre el contraste binario, que es además la forma real
del efecto (§1.2.D). Y el sesgo de cobertura de Wikidata es distinto entre
deportes, lo que limita comparar niveles absolutos: la comparación válida es de
*forma geográfica*, no de tasa.

**Esfuerzo:** 2 días, reusando todo el pipeline. **Marca:** condicionada a BL1 y
BL2 (necesita la geografía arreglada), pero **es prioritaria igual** porque
diagnostica BL3 desde afuera.

### B2. Interacción efecto de edad relativa × tamaño de localidad

**Fuente:** ya está en el repo. `analysis_players.parquet` tiene `dob` con
`dob_precision`; los nacimientos por mes salen de las estadísticas vitales del
DEIS.

**Qué agrega:** si en los pueblos chicos hay menos competencia por cupo, el RAE
debería ser más débil ahí que en el conurbano. **Que la interacción exista o no
exista es un hallazgo en los dos sentidos**, y es más publicable que cualquiera de
los dos efectos por separado. Además es un test indirecto del mecanismo de acceso
que el paper propone en §4.1 y hoy no puede medir.

**Qué la haría fracasar:** `dob_precision` tiene que ser 11 (día) para tener mes;
verificar cuántos de los 5.511 lo cumplen. Y el denominador de nacimientos por mes
por tamaño de localidad no existe: hay que usar la estacionalidad nacional como
aproximación y declararlo.

**Esfuerzo:** 2 días. **Marca:** condicionada a BL1.

### B3. Fútbol femenino como grupo de contraste

**Fuente:** Wikidata, 252 casos verificados en la ventana. `config.yaml:35` ya
argumenta por qué se analiza aparte.

**Qué agrega:** infraestructura de formación radicalmente distinta y mucho más
reciente. Si el efecto de tamaño es más débil en el fútbol femenino, apoya la
lectura de que lo que se mide es densidad de infraestructura y no entorno de
juego.

**Qué la haría fracasar:** n=252 concentrado en cohortes recientes, con censura a
derecha severa. Sirve para el contraste binario, no para más.

**Esfuerzo:** 1 día. **Marca:** condicionada a BL1.

### B4. Movilidad residencial como baseline de migración

**Verificado.** RENAPER, dataset *«Movilidad Residencial en Argentina»* en
`datos.gob.ar`, con recursos «Movilidad residencial **interdepartamental**
(Decenio 2012–2022)» y «Emigrantes e inmigrantes por departamento».

**Qué agrega:** ataca la limitación 5 del paper. Hoy el 47,1 % de migración
futbolística se compara contra el 13,8 % de `P14` del censo, que es un marginal de
todas las edades sin cruzar con cohorte — comparación que el propio paper admite
que no es comparable. RENAPER da flujos **por departamento y por década**, mucho
más cerca del objeto correcto.

**Qué la haría fracasar:** 2012–2022 no son las cohortes de los futbolistas, y
mide cambios de domicilio declarado, no migración a los 15 años por fútbol.
Mejora la comparación; no la resuelve.

**Esfuerzo:** 2 días. **Marca:** condicionada a BL6.

### B5. Nivel socioeconómico departamental como covariable

**Verificado.** `datos.gob.ar`, *«Puestos de trabajo por departamento/partido y
sector de actividad»* (Secretaría de Industria y Comercio / CEP XXI). Además el
Censo 2022 ya ingestado permite construir indicadores de hogar por radio.

**Qué agrega:** el paper reconoce en su limitación 6 que no hay **ni una sola**
covariable más allá del tamaño. Una sola variable socioeconómica ya permite
preguntar si el tamaño de ciudad sigue prediciendo algo una vez controlado por
ingreso o empleo formal — y el §4.1, que hoy es interpretación pura, pasaría a
tener algo detrás.

**Qué la haría fracasar:** falacia ecológica; son covariables de área, no de
individuo. No convierte el trabajo en causal, solo lo hace menos ingenuo.

**Esfuerzo:** 3 días. **Marca:** condicionada a BL1.

## 2.C — Expansiones estéticas

Las figuras actuales están bien hechas: `style.Figura` resuelve el problema de
layout que documenta `CLAUDE.md`, la Figura 4 declara en su propio subtítulo que
el resultado contradice la literatura, y la Figura 22 explica en la nota al pie
qué habría que ver si el mecanismo fuera cierto. El listón está alto.

### C1. Mapa bivariado: tasa × precisión — *esta es la que revela el problema*

Coroplético departamental con dos dimensiones: color = tasa, saturación o textura
= ancho relativo del IC de Poisson. **Va primero, no último**, porque es la figura
que muestra de un vistazo que la cola alta del mapa actual es varianza y que los
departamentos con código roto son fantasmas. Responde algo que la tabla no
responde: *dónde tengo derecho a mirar*.

*Requiere:* nada nuevo, `h2_departamentos.csv` ya trae los IC y la bandera
`reportable`. **Marca:** diagnostica BL1.

### C2. Small multiples de cuencas de captación por club

Una cuenca por club grande, misma escala, todas juntas. Muestra en una imagen los
dos modelos que el paper describe en texto: Rosario Central capta a 0 km, Boca a
277 km.

*Requiere:* `clubs_resolved.parquet` + `careers.parquet`, ya en el repo.
**Marca:** condicionada a BL6 (la muestra de H3 está sesgada; la figura hereda el
sesgo y hay que rotularlo).

### C3. Cuenca real vs Voronoi

Partición de Voronoi entre clubes de primera contra la cuenca observada de cada
uno. Muestra quién capta más lejos de lo que «le corresponde» por geografía.
Convierte una intuición en una métrica.

*Requiere:* coordenadas de clubes (ya están) + `shapely`. **Marca:** condicionada
a BL6.

### C4. Beeswarm de mes de nacimiento coloreado por tamaño de localidad

El RAE y su interacción con el tamaño en un solo gráfico, sin agregar.
**Marca:** condicionada a B2.

### C5. Paleta derivada de escudos

Extraer los colores dominantes del escudo de cada club como paleta del mapa de ese
club. Resuelve asignar veinte colores arbitrarios y hace el mapa legible sin
leyenda. **Nota:** los escudos son marcas registradas; para exploración interna no
hay problema, y la paleta derivada es más segura que el escudo reproducido si el
destino es publicación. Conviene chequearlo antes de maquetar.

### C6. Cartograma de la corrección

Ya existe `fig06_cartograma_provincias`. La versión que agrega algo es el **par
antes/después de BL1+BL2**: dos cartogramas lado a lado mostrando cuánto se mueve
el mapa al arreglar la geografía. Es la figura que justifica el trabajo de
reparación.

## Fuentes verificadas en esta pasada

Consultadas hoy contra su endpoint, no citadas de memoria:

| Fuente | Estado | Para qué |
|---|---|---|
| DEIS — Nacidos vivos por **residencia de la madre** (`datos.gob.ar`, Min. Salud, ~2005–2023) | ✅ verificado vía CKAN | A1 · cota del artefacto de maternidad |
| RENAPER — **Movilidad Residencial** interdepartamental 2012–2022 (`datos.gob.ar`) | ✅ verificado vía CKAN | B4 · baseline de migración |
| CEP XXI — **Puestos de trabajo por departamento** (`datos.gob.ar`) | ✅ verificado vía CKAN | B5 · covariable socioeconómica |
| Wikidata — básquet / rugby / fútbol femenino AR | ✅ contado vía SPARQL (396 / 291 / 252) | B1, B3 · placebo y contraste |
| INDEC — `c2022_codigos_departamentos.xlsx` | ✅ ya en el repo; con él se detectó BL2 | A2 |
| BDFA (`bdfa.com.ar`) | ⚠️ existe; **términos de uso no verificados** | A3 · validación de `P19` |

No verificado y por lo tanto no propuesto como fuente: cualquier padrón de AFA de
convocatorias juveniles (el paper lo menciona como no público, y no lo confirmé).

---

## Fase 5 — Plan priorizado

| # | Ítem | Tipo | Confianza | Esfuerzo | Qué desbloquea |
|---|---|---|---|---|---|
| 1 | Crosswalk histórico de códigos de departamento (A2) | reparación | solo esta pasada, **verificado con números** | 1 día | BL1 · mapa departamental, cunas, denominador de ciudad |
| 2 | Corregir la lista del AMBA en `config.yaml:144-168` | reparación | solo esta pasada, **verificado contra INDEC** | 1 h | BL2 · da vuelta AMBA vs Pampeana |
| 3 | Re-correr el pipeline y actualizar §3.2 del paper | reparación | solo esta pasada | 2 h | BL7 |
| 4 | Nacidos vivos por residencia de la madre (A1) | reparación | convergente | 1–2 días | BL3 |
| 5 | Validar `P19` contra BDFA (A3) | reparación | convergente | 2–3 días | BL4 |
| 6 | Test placebo con básquet (B1) | ampliación | solo esta pasada | 2 días | diagnostica BL3 desde afuera; puede reescribir el paper |
| 7 | Mapa bivariado tasa × precisión (C1) | estética | convergente | 4 h | hace visible BL1 y las colas de Poisson |
| 8 | Shrinkage / Bayes empírico en tasas departamentales | reparación | convergente (roast I1) | 1 día | BL5 parcial |
| 9 | Degradar o restringir H3 (roast B5) | reparación | convergente | 1 día | BL6 |
| 10 | Éxito graduado (A4) | ampliación | solo esta pasada | 1 día | mejora la variable dependiente |
| 11 | Interacción RAE × tamaño (B2) | ampliación | del encargo | 2 días | hallazgo nuevo publicable |
| 12 | Covariable socioeconómica (B5) | ampliación | convergente (roast §8) | 3 días | permite escribir §4.1 sin clave causal vacía |
| 13 | Fútbol femenino (B3) | ampliación | del encargo | 1 día | contraste de infraestructura |
| 14 | Movilidad residencial RENAPER (B4) | ampliación | solo esta pasada | 2 días | arregla la comparación 47,1 % vs 13,8 % |
| 15 | Small multiples de cuencas + Voronoi (C2, C3) | estética | del encargo | 2 días | condicionada a BL6 |
| 16 | Beeswarm RAE (C4) | estética | del encargo | 4 h | condicionada a B2 |
| 17 | Paleta de escudos (C5) | estética | del encargo | 1 día | legibilidad |
| 18 | Cartograma antes/después (C6) | estética | solo esta pasada | 4 h | documenta el efecto de la reparación |

---

## Cierre

**Qué es este proyecto hoy.** Un pipeline reproducible y honesto, con una decisión
metodológica genuinamente buena —el denominador de nacidos vivos por cohorte, que
es mejor que el de buena parte de la literatura del *birthplace effect*— y un
resultado central que sobrevive a los chequeos que sí se pueden hacer con estos
datos: el efecto clásico no aparece en Argentina, aparece invertido, y el
gradiente es el mismo entre los jugadores de selección, donde Wikidata es censal,
que entre los del montón. Encima hay un resultado —el de conversión de juveniles a
la Mayor, §3.5— que no depende de ningún denominador y que está listo. El paper es
inusualmente autocrítico: declara sus limitaciones con más rigor que el promedio
de lo publicado.

Y tiene dos bugs de geografía que nadie había visto y que mueven números
publicados. Uno hace desaparecer un millón de nacimientos del denominador de
ciudad, el 70 % de ellos del Gran Buenos Aires. El otro tiene la mitad de los
códigos del AMBA apuntando al departamento equivocado, y al corregirlo la región
pampeana pasa a producir más que el AMBA — o sea, **la afirmación «la producción
se concentra en el AMBA» se da vuelta**. Ninguno de los dos toca el titular de H1,
pero los dos tocan H2, el mapa departamental y el ranking de cunas.

**Qué podría ser.** Con el crosswalk de departamentos, la lista del AMBA
corregida, la serie por residencia de la madre acotando el artefacto de
maternidad, y una validación de `P19` contra BDFA, el trabajo pasa de «resultado
sub-identificado en magnitud» a «resultado identificado con cota declarada». Con
el placebo de básquet encima, pasa a poder distinguir entre «esto es del fútbol» y
«esto es del registro civil», que es la pregunta que hoy no puede contestar y que
un revisor va a hacer.

**La diferencia entre las dos cosas.** Los ítems 1 a 3 son un día y medio de
trabajo mecánico y son los que más números mueven. Los ítems 4 a 7 son otras dos
semanas. Ahí ya hay paper. Todo el bloque de ampliación —RAE, femenino,
socioeconómico, cuencas— es un segundo trabajo, y conviene tratarlo como tal:
agregarle variables a una medición que todavía tiene la geografía rota produce
output más lindo y más equivocado.

**Y la advertencia que va con todo esto:** los dos defectos que encontré son de la
clase que no falla ruidosamente. Los totales provinciales cuadran, el pipeline
corre limpio, los tests pasan y el `git diff` sale vacío.
`tests/test_geo_units.py:115` verifica que La Matanza sea AMBA —y `06427` es de
los doce códigos que están bien—, así que el test pasa mientras doce de sus
vecinos apuntan a otro partido. Es el mismo patrón que las «trampas» que
`CLAUDE.md` ya documenta: el error entra por un padrón que cambió de códigos y
nadie vuelve a mirar. **Vale la pena un test que compare la lista del AMBA y el
padrón de departamentos contra el xlsx del INDEC que el repo ya descarga**, en vez
de contra códigos escritos a mano.
