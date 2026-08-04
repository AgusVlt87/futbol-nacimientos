# Sincronización del paper — 2026-08-03 / 04

Verificación de `reports/paper.md` y `paper/paper.tex` contra `outputs/tables/`,
y corrección de lo que divergía. Rama `fix/paper-sync-clubes`.

**Nivel aplicado: 2 con un arreglo de pipeline por delante.** Se arregló un bug
que partía cada club en varias filas, se corrigieron 20 cifras de prosa en los
dos documentos, se reescribieron tres afirmaciones que los datos contradecían, y
se portó al `.md` una sección de resultados que solo estaba en el `.tex` y que el
`.md` además negaba.

---

## Estado del repo al empezar

| Chequeo | Resultado |
|---|---|
| Working tree limpio | ✅ |
| Suite de tests | ✅ 90 passed |
| `sync_tablas_paper --check` | ✅ verde (y ese verde era el problema, ver abajo) |
| Pipeline reproduce | ✅ 74/74 tablas byte a byte |
| Bloqueantes que muevan números | ❌ uno, encontrado acá |

`_run.json` marcaba tres módulos con un `config_sha256` viejo. Falsa alarma —el
`config.yaml` solo había cambiado en el bloque `ingest.wikipedia`— pero se
verificó congelando `outputs/tables/`, recorriendo los tres módulos y comparando:
74 de 74 idénticas.

---

## Lo que cambió de signo

### 1. La concentración de la formación, y el club que la calculaba mal

`run_futbol.py` agrupaba por `["primer_club_qid", "primer_club"]`: por QID **y
por nombre**. `primer_club` guarda el texto visible del enlace cuando el dato
sale de una ficha de Wikipedia, o sea lo que tipeó cada editor. Q18640 llega como
«Gimnasia (LP)», «Gimnasia La Plata», «Gimnasia y Esgrima de La Plata» y cuatro
variantes más. Un club se partía en tantas filas como grafías tuviera: Boca en
cuatro, Newell's en siete. **116 de 159 QIDs partidos, 3.832 de 3.955 jugadores
afectados.**

Es la otra mitad de la trampa 16: resolver las redirecciones arregló el QID y
dejó el nombre crudo de cada fuente.

`run_seleccion.py` tenía la misma falla y peor: agrupaba por `primer_club` a
secas, sin QID.

La tabla del §3.3 cambia de **orden**, no solo de valores:

| Publicado | | Corregido | |
|---|---:|---|---:|
| Boca Juniors | 202 | Boca Juniors | **216** |
| River Plate | 123 | River Plate | **177** |
| **Racing Club** | **110** | Newell's Old Boys | **159** |
| Vélez Sarsfield | 99 | Vélez Sarsfield | **157** |
| Newell's Old Boys | 98 | Rosario Central | **155** |
| Rosario Central | 94 | **Estudiantes LP** | **130** |

Racing sale del top 6 y entra Estudiantes. Concentración:

| | antes | ahora |
|---|---:|---:|
| top 5 | 16,0% | **21,8%** |
| top 10 | 26,6% | **37,6%** |
| top 20 | 40,7% | **59,7%** |

Y el paper decía **48% / 71%**, que no salían de ninguna tabla: eran de cuando
H3 tenía 1.923 casos. O sea que la afirmación publicada estaba mal y la tabla que
debía corregirla también.

**No toca H3**: la migración (44,5%), el OR (5,03), los saldos y las retenciones
se calculan por jugador. Tampoco H1, H2, H4, el placebo ni §3.5 — la conversión
juvenil → Mayor da idéntica después del arreglo.

### 2. §3.6 — el NEA sí sobrevive a la corrección

Sobreviven **siete** contrastes a Benjamini-Hochberg, no seis, y el séptimo es
NEA × defensor (*p* corregido = 0,042). El paper decía «ningún contraste que
involucre al NOA o al NEA sobrevive».

Se corrigió el conteo y se agregó el séptimo, con la salvedad de que es el más
débil de los que pasan, en la región con menos casos, dentro de un análisis
declarado exploratorio. **La conclusión sobre el mito de las delanteras del norte
se mantiene y ahora se apoya en los contrastes que corresponden**: NOA ×
delantero (0,098) y NEA × delantero (0,540), ninguno significativo.

### 3. §3.7 — los cuatro placebos, no tres

Los cuatro difieren del fútbol en distribución regional con p < 0,001; el vóley
(2,9 × 10⁻⁴) era el que estaba del otro lado del corte. El paper subestimaba su
propio resultado.

---

## La divergencia entre los dos documentos

`reports/paper.md` no tenía la sección de covariables y su limitación 7 decía
«**Sin controles.** No hay ninguna covariable más allá del tamaño de la ciudad».
`paper/paper.tex` sí la tiene, completa, con figura y con la limitación redactada
como «Controles parciales». **El `.md` negaba un análisis que el repo hizo y que
el `.tex` reporta.**

Como la decisión de incluirlo ya estaba tomada y escrita, portarlo es
sincronización y no autoría nueva. Se agregaron al `.md`:

- **§3.8 Qué queda del tamaño al controlar por pobreza y por distancia**
- **§3.9 Dónde está la variación: entre departamentos o adentro**
- el ítem **Séptimo** del resumen
- la limitación 7 reescrita como «Controles parciales»
- §4.1 reencuadrado: la interpretación de «distancia a la infraestructura
  formativa» **no se sostiene medida**, porque la distancia se apaga al entrar el
  NBI (IRR 0,981; p = 0,63). Eso ya estaba en el `.tex` y ahora está en los dos.

**Y el `.tex` tenía su propia deuda**: toda la fila de modelos con distancia
estaba una tanda atrasada (universo de 109 clubes en vez de 159, mediana 95 km en
vez de 79, IRR 0,854 en vez de 0,825, p = 0,75 en vez de 0,63). Además su
limitación 4 seguía diciendo que «la tasa de error del `P19` no está medida»
mientras el propio `.tex` tiene una subsección que la mide. Corregido.

---

## Cifras corregidas

Veinte, en los dos documentos según dónde aparecieran.

| Ubicación | Decía | Dice |
|---|---|---|
| §2.1 | Spearman −0,355 | **−0,362** |
| §2.1, §4.3-2 | +17% decil chico; RR corregido ~0,52 | **+19%; ~0,53** |
| §2.1 | «de 435 a 60.160 nacimientos» | **38 a 266.434** |
| §2.1 (.tex) | 83,8% dentro del 20% | **84,1%** |
| §2.2 | «3 en 2005–2009» | **2005–2008** |
| §2.4 | dos regiones | **tres** |
| §2.4 | departamental 5.389 | **5.401** |
| §3.1 | deciles (7 de 10 valores mal) | **22,7 · 4,6 · 13,7 · 4,9 · 7,2 · 9,4 · 13,1 · 11,2 · 15,7 · 24,6** |
| §3.1 | AIC 3.654,3 / 3.652,8 | **3.654,6 / 3.653,1** |
| §3.1 | p = 0,11 y 0,44 | **0,12 y 0,45** |
| §3.1, resumen, §4.3-8 | pseudo-R² 0,011 | **0,010** |
| §3.1 | devianza explicada 2,6% | **2,5%** |
| §3.1 | «a 100.000 hab van de 3 a 100» | **las trece ciudades de 90–110k van de 0 a 98** |
| §3.2 | χ²(5) = 1.050,7; *w* = 0,44 | **1.110,8; 0,45** |
| §3.3 | NEA «uno de cada doce» | **uno de cada nueve** |
| §3.3, §4.1 | 48% / 71%; «la mitad» | **37,6% / 59,7%** |
| §3.4 | 7,5 · 7,0 · 8,6 · 9,2 | **7,4 · 6,9 · 8,2 · 9,0** |
| §3.5 | 347 juveniles | **337** |
| §4.1 | «un 42% de las veces» | **41,1% contra 28,1%** |
| §4.1 (.tex) | cohortes 0,34 · 0,43 · 0,41 · 0,55 | **0,36 · 0,45 · 0,43 · 0,58** |
| §4.3-1 | 264 localidades <100 hab | **258** |
| §4.4 | retención del 8,3% del NEA | **11,2%** |

Tres de éstas eran incoherencias internas: el mismo documento ya traía el valor
bueno en otro lado.

También se corrigió que los diez clubes que más forman **no** están todos en el
AMBA, Rosario o La Plata: nueve lo están, y el décimo (Unión) es del Gran Santa
Fe.

---

## Por qué el chequeo daba verde

`--check` auditaba 7 cifras de prosa. Las 20 desactualizadas estaban **todas**
fuera de esa lista, y las tablas sí estaban al día. El verde era correcto y no
significaba nada.

Tres cosas cambiaron para que no se repita:

1. **`CIFRAS` pasó de 7 a 19 entradas**: χ² de H2, muestra departamental,
   pseudo-R², AIC, n de juveniles, retención del NEA, concentración top-10 y
   top-20, pseudo-R² del NBI, IRR de la distancia con NBI, primer decil y RR de
   la cohorte del 70.
2. **Las dos series que vivían dentro del código de las figuras ahora son
   tablas.** `fig20` escribe `h1_deciles_tamano.csv` y `fig22` escribe
   `temporal_rr_pueblo_metropoli.csv`. Eran justamente las que se habían
   desfasado sin alarma, porque no había nada contra qué compararlas.
3. **La auditoría de prosa entró a la suite de tests**
   (`test_las_cifras_de_la_prosa_coinciden_con_las_salidas`). Antes vivía solo en
   el CLI, así que `pytest` daba verde con el texto desfasado.

Y un test nuevo para el bug de clubes: `tests/test_clubes_por_qid.py` verifica
que ningún QID aparezca en dos filas, que la concentración cuadre con el ranking
y que la tabla de selección también vaya por QID.

---

## Verificación

| | |
|---|---|
| `sync_tablas_paper --check` | ✅ verde, 14 tablas + **19** cifras de prosa, en los dos documentos |
| Suite de tests | ✅ **95 passed** (eran 90; +3 de clubes, +2 de prosa) |
| Numerales de la prosa del `.md` | 628 extraídos; los 17 sin match directo son años, URLs y dos cifras históricas documentadas en `docs/impacto-lote-1.md` (1.049.301) y en el crudo (General Levalle, 5.674 hab) |

Durante el trabajo el chequeo nuevo encontró **dos** cifras que se me habían
pasado a mano —el AIC del `.tex` y la serie de cohortes del `.tex`—, que es
exactamente para lo que se agregó.

---

## Lo que queda abierto

1. **Los dos documentos siguen siendo documentos distintos.** El `.tex` tiene
   cinco subsecciones de resultados que el `.md` no: granularidad del `P19`,
   validación manual del `P19`, el «primer club» de H3, cuánto tendría que fallar
   el dato, y el control positivo de edad relativa. Más «Qué haría falta para
   cerrar el argumento» y una Conclusión. **No las porté**: eso no es sincronizar
   cifras, es decidir si el `.md` debe ser el `.tex` o un resumen de él. Es tuya
   la decisión.
2. **`_run.json` sigue mintiendo** sobre `run_all`, `run_criterio_denominador` y
   `run_placebo` hasta que se los vuelva a correr y grabe el manifiesto.
3. **`paper/paper.pdf` está sin recompilar** — hay que pasarle `paper/compilar.ps1`.
4. El `README.md` quedó corregido en las mismas cifras (migración, retención,
   Boca, cobertura de H3, covariables, pseudo-R², +19%) y ya no se contradice
   solo en «Sin controles», pero **no tiene chequeo automático**: es el próximo
   candidato a desfasarse.
