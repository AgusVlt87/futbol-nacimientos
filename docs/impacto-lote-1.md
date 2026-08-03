# Impacto del lote 1 — reparación de la geografía

**Rama:** `fix/geografia-departamental` · **Base:** `c138fca` (sobre `3f07dba`)
**Fecha:** 2026-08-02 · **Alcance ejecutado:** BL1, BL2, BL7
**Baseline congelado:** `outputs/_baseline_3f07dba/` (50 tablas)

Antes de tocar nada se verificó el determinismo del pipeline como corresponde:
dos corridas completas producen las 50 tablas **byte a byte idénticas**. Todo lo
que cambió abajo lo cambió este lote, no el ruido.

---

## 1. Qué se arregló

| | Antes | Ahora |
|---|---|---|
| Partidos del AMBA | 24 códigos escritos a mano, **12 apuntaban a otro partido** | 24 nombres resueltos contra el padrón del INDEC |
| Códigos de departamento | 44 de 532 cambian entre censos; nada lo verificaba | crosswalk de 15 componentes en CSV versionado |
| Nacimientos perdidos dept → ciudad | **1.049.301** (4,6 %) | **51** (2 departamentos deshabitados, declarados) |
| Departamentos en el denominador | 526, de los cuales 16 eran códigos muertos | 515, todos vigentes en 2022 |
| Verificación de conservación | ninguna | corta el pipeline, **grupo por grupo** |

Los 51 nacimientos que quedan fuera son Islas del Atlántico Sur (1) y Antártida
Argentina (50): no tienen ninguna localidad censal. Están declarados en
`SIN_LOCALIDAD_CENSAL` y el pipeline los reporta, no los descarta en silencio.

---

## 2. Números publicados que se movieron

**27 de las 50 tablas cambiaron.** Las 23 restantes son idénticas, y cuáles son
importa tanto como cuáles cambiaron (§2.6).

### 2.1 H1 — tamaño de ciudad

| Tramo | Nacidos antes | Nacidos ahora | Tasa antes | Tasa ahora | RR antes | RR ahora |
|---|---:|---:|---:|---:|---:|---:|
| <10k | 3.339.078 | 3.385.077 | 12,91 | **12,73** | 0,424 | **0,449** |
| 10–50k | 3.418.174 | 3.491.322 | 16,62 | **16,27** | 0,546 | **0,574** |
| 50–100k | 1.280.832 | 1.338.281 | 21,47 | **20,55** | 0,705 | **0,725** |
| 100–500k | 2.934.614 | 2.994.490 | 21,50 | **21,07** | 0,706 | **0,743** |
| >500k | 10.975.566 | 11.788.344 | 30,46 | **28,36** | 1,00 | 1,00 |

El numerador no se mueve en ningún tramo (431 / 568 / 275 / 631 / 3.343). Todo el
cambio es denominador. **El sentido de H1 se sostiene**: 12,7 sigue muy por
debajo de 28,4.

Cae dentro de la cota que el diagnóstico había anticipado (RR ≤ 0,464).

### 2.2 H2 — regiones. **Acá se da vuelta el orden**

| Región | Tasa antes | Tasa ahora | RR vs AMBA antes | RR vs AMBA ahora |
|---|---:|---:|---:|---:|
| **Pampeana** | 29,54 | **34,55** | 0,84 | **1,22** |
| **AMBA** | **35,03** | 28,27 | 1,00 | 1,00 |
| Cuyo | 15,22 | 15,22 | 0,43 | 0,54 |
| Patagonia | 12,71 | 12,71 | 0,36 | 0,45 |
| NEA | 9,58 | 9,58 | 0,27 | 0,34 |
| NOA | 8,20 | 8,20 | 0,23 | 0,29 |

Cuyo, Patagonia, NEA y NOA no cambian en absoluto: el error era interno a Buenos
Aires. Lo que cambia es el reparto AMBA / Pampeana, y **cambia de orden**.

| | Antes | Ahora |
|---|---:|---:|
| AMBA | 35,03 | 28,27 |
| Interior (no AMBA) | 20,64 | 22,22 |
| **RR Interior/AMBA** | **0,589** | **0,786** |

La brecha entre el AMBA y el interior se achica un 45 %.

### 2.3 Ranking departamental

De 510 departamentos comparables, **19 cambiaron de tasa y 18 de ellos más del
50 %**. El resto del mapa está intacto: el error estaba concentrado, no difuso.

| Depto | Tasa antes | Tasa ahora | Cambio |
|---|---:|---:|---:|
| Magdalena | **162,98** | 64,71 | −60 % |
| 2 de Abril | 99,40 | 32,01 | −68 % |
| Morón | 93,08 | 32,51 | −65 % |
| Colón (ER) | 87,36 | 33,35 | −62 % |
| Villaguay | 44,86 | 15,48 | −65 % |
| Concordia | 62,54 | 22,17 | −65 % |
| Ezeiza | 54,22 | 23,56 | −57 % |
| Hurlingham | 26,87 | 9,41 | −65 % |
| Ituzaingó | 32,13 | 11,26 | −65 % |
| San Miguel | 25,37 | 10,00 | −61 % |
| José C. Paz | 29,43 | 11,70 | −60 % |
| Malvinas Argentinas | 15,71 | 6,21 | −61 % |
| Esteban Echeverría | 25,46 | 10,86 | −57 % |
| San Salvador | 26,56 | 10,00 | −62 % |

**Magdalena, que encabezaba el ranking con 162,98 y anclaba el extremo superior
de la escala de color de la Figura 1, era un artefacto.** El nuevo primero es
Capital de Mendoza (103,09), que no cambió y que el paper ya declara como caso
de metrópoli fragmentada (limitación 10).

**16 departamentos fantasma salieron del ranking** —códigos de censos viejos con
nacimientos y cero jugadores, entre ellos General Sarmiento con 259.572
nacimientos—. **5 departamentos reales entraron**, que antes no existían para el
análisis:

| Depto | Jugadores | Tasa |
|---|---:|---:|
| Ushuaia | 7 | 26,79 |
| Chascomús | 3 | 15,31 |
| Río Grande | 2 | 6,31 |
| Tolhuin | 0 | 0,00 |
| Lezama | 0 | 0,00 |

Por eso la n del test departamental sube de 5.389 a 5.401: **12 jugadores
estaban siendo descartados** por caer en departamentos que el denominador no
tenía.

### 2.4 Ranking de cunas

**El top-8 de ciudades no se movió**: Rafaela (98,0), Gran Santa Fe (72,8), Gran
Rosario (58,3), Tandil (53,6), Gran San Nicolás (40,2), Gran Río Cuarto (31,9),
Gran Paraná (31,5), Mar del Plata (31,5). Ninguna estaba afectada.

El ranking **departamental** de cunas sí: Morón salía segundo con 93,1 y ya no
está en el top-6.

| Puesto | Antes | Ahora |
|---|---|---|
| 1 | Capital (Mendoza) 103,1 | Capital (Mendoza) 103,1 |
| 2 | **Morón 93,1** | Castellanos 85,5 |
| 3 | Castellanos 85,5 | Caseros 74,1 |
| 4 | Caseros 74,1 | La Capital 69,6 |
| 5 | La Capital 69,6 | Marcos Juárez 67,4 |
| 6 | Marcos Juárez 67,4 | CABA 63,0 |

### 2.5 χ² y regresión

| Test | χ² antes | χ² ahora |
|---|---:|---:|
| H1 esquema principal | 452,2 | **382,1** |
| H1 esquema cote2006 | 486,5 | **412,0** |
| H1 localidad censal aislada | 633,7 | **692,5** |
| H1 solo cohortes ≤ 2002 | 439,0 | **372,0** |
| H2 regiones | 1.094,4 | **1.110,8** |
| H2 departamentos | 4.176,0 | **3.762,3** |
| H2 provincias (todas las variantes) | sin cambio | sin cambio |

Regresión binomial negativa: IRR por *e-fold* de tamaño **1,181 → 1,175**
(IC 1,114–1,240), n de ciudades **3.459 → 3.477**.

La variante de localidad aislada se movió en dirección contraria a las otras;
está anotado como P2 en `hallazgos-pendientes.md`.

### 2.6 Lo que **no** cambió, y por qué importa

| Tabla | Por qué es la prueba de que el arreglo es el correcto |
|---|---|
| `h2_provincias.csv` y sus 5 baselines alternativos | El denominador provincial es dato real del DEIS, ajeno al reparto interno. Que no se muevan confirma que el error era sub-provincial. |
| `seleccion_conversion_*` (§3.5 del paper) | No usan denominador poblacional. El diagnóstico predijo que quedarían intactas y quedaron intactas: **el resultado más fuerte del trabajo no depende de nada de esto**. |
| `h4_contraste_elite.csv` | OR 0,89 (0,71–1,13), sin cambio. |
| `diagnostico_censura_cohortes.csv` | Provincial. Sin cambio. |
| `h3_migracion_por_tamano_origen.csv` | Individual, sin denominador. Sin cambio. |

### 2.7 Cambios menores

- **H4 por nivel**, RR `<10k` vs `>500k`: T1 0,489→0,518 · T2 0,363→0,385 ·
  T3 0,424→0,449 · T4 0,425→0,450. **El paralelismo entre los cuatro niveles se
  mantiene**, que es el argumento anti-sesgo-de-cobertura del §3.4.
- **Selección Mayor por región** (por millón): AMBA 17,1→14,2; Pampeana
  17,4→17,8. Acá también el AMBA deja de encabezar.
- **Selección Mayor por tramo**: `>500k` 15,3→14,3; `<10k` 7,5→7,4.
- **H3 retención**: AMBA 91,6 %→90,8 %; Pampeana 49,6 %→48,9 %. El resto igual.
- **Validación del denominador**: error mediano 9,09 %→9,05 %; dentro del 20 %
  83,76 %→84,15 %.

---

## 3. Figuras

**Se regeneraron las 26**, porque todas leen de `outputs/tables/` y dejar
figuras viejas conviviendo con tablas nuevas es exactamente el modo de falla que
este lote vino a cerrar. Las que cambian de contenido:

| Figura | Qué cambia |
|---|---|
| **fig01** mapa departamental de tasas | Lo más afectado. Desaparecen 16 polígonos «sin datos» que eran códigos muertos, entran 5 departamentos reales, y **el extremo superior de la escala de color pasa de 163 a 103**. |
| **fig02** mapa departamental de conteos | Cambia la grilla de departamentos (526→515). |
| **fig04** tasa por tramo | Todas las barras y el eje. |
| **fig05** tasa por región | **Se invierte el orden de las dos primeras barras.** El título hardcodeado dice «El AMBA y la Pampa…» y ahora la primera es la Pampa (ver P4 en `hallazgos-pendientes.md`). |
| **fig07** scatter tamaño/tasa | 3.477 ciudades en vez de 3.459; recta de ajuste. |
| **fig11** cunas | El panel de ciudades no se mueve; el de departamentos sí. |
| **fig13** selección | Tasas por región y tramo. |
| **fig19** sesgo del denominador | Recalculado. |
| **fig20** deciles | Recalculado. |
| **fig21** funnel departamental | Cambia la nube entera. |
| **fig22** efecto por cohorte | RR por década. |
| **fig24** sensibilidad del denominador | Recalculado. |
| **fig25 / fig26** flujo y retención | Cambios menores. |

Sin cambio de contenido: fig03, fig06, fig08, fig09, fig10, fig12, fig14–18,
fig23.

---

## 4. Afirmaciones del paper que quedaron falsas

**Listadas, no reescritas.** El encuadre lo decidís vos.

### 4.1 Se dan vuelta

1. **Resumen, tercer punto** — «*la producción se concentra en el AMBA y en un
   corredor pampeano*» y «*El AMBA (35,0 cada 100.000) y la Pampa (30,2)
   cuadruplican al NOA (8,7)*».
   El AMBA es 28,3 y la Pampeana 34,6: **la Pampeana produce más**. Y la relación
   con el NOA es 3,5× y 4,2×, no «cuadruplican» las dos.

2. **§3.2** — «*El interior no produce más que el AMBA: produce menos, y en el
   norte produce cuatro veces menos*».
   La segunda mitad se sostiene (NOA 8,2 contra Pampeana 34,6). La primera se
   debilita mucho: RR 0,79, no 0,59.

3. **§4.2** — «*En la misma corrección, el AMBA pasó de estar por debajo de la
   región pampeana a estar por encima*».
   **Esa inversión era el bug.** Con el AMBA bien definido, la pampeana sigue
   arriba. La lección general del párrafo (las áreas metropolitanas tienen menos
   hijos por habitante) sigue en pie; el ejemplo con que se ilustra, no.

4. **§4.1** — «*diez clubes concentran la mitad de la formación registrada del
   país, y están todos en el AMBA, Rosario o La Plata*».
   Sigue siendo cierta como frase, pero **La Plata ya no es AMBA** en la
   definición corregida, y el párrafo la usa como si el AMBA fuera el centro de
   todo. Revisar el encuadre.

### 4.2 Quedan desactualizadas en magnitud

5. **§2.1** — «*El reparto intraprovincial es el único supuesto de la cadena*».
   Falso ya antes de este lote y falso ahora: hay un segundo supuesto, el reparto
   de los partidos divididos (P5 en `hallazgos-pendientes.md`), que hay que
   agregar a §4.3.

6. **§3.1** — «*de 8,4 por 100.000 en localidades de menos de 1.000 habitantes a
   30,5 en las de más de 500.000*». El 30,5 es ahora 28,4.

7. **§3.1** — «*cada e-fold de tamaño multiplica la tasa por 1,181 (IC
   1,120–1,246)*» → 1,175 (1,114–1,240). Y «*3.459 ciudades*» → 3.477.

8. **§3.1, robustez** — la tabla de tres variantes: 0,42 / 0,39 / 0,41 pasa a
   0,45 / 0,36 / 0,44. **La variante de localidad aislada ahora se separa más de
   la principal, no menos** (ver P2).

9. **§3.1** — «*Con el denominador anterior —población censada en 2022— este mismo
   RR daba 0,57. El denominador correcto fortalece el hallazgo*». El contraste
   sigue existiendo pero ahora es 0,57 contra 0,45, no contra 0,42.

10. **§3.4** — «*15,3 seleccionados por millón […] contra 7,5*» → 14,3 contra 7,4.
    Y «*Por región, 17 por millón en el AMBA contra 2 en el NOA*» → 14 contra 2,
    con la Pampeana (17,8) por encima del AMBA.

11. **§3.3** — retención del AMBA «*91,6 %*» → 90,8 %; Pampeana 49,4 % → 48,9 %.

12. **Toda mención a «526 departamentos»** → 515. Y la n del test departamental
    5.389 → 5.401.

### 4.3 Lo que se refuerza

13. **§3.4** — «*El gradiente por tamaño se sostiene en los cuatro niveles*».
    Sigue siendo cierto y ahora es más parejo (0,52 / 0,39 / 0,45 / 0,45).

14. **§3.5 entero** — intacto, dígito por dígito. El diseño que se hizo para no
    depender del denominador efectivamente no dependía del denominador.

15. **§4.3, limitación 8** — «*un departamento con dos jugadores encabeza el
    ranking per cápita por puro ruido de Poisson*». Sigue siendo cierta, pero el
    ejemplo que la motivaba (Magdalena, 6 jugadores, 163 por 100.000) era además
    un error de denominador, no solo varianza.

---

## 5. Qué queda del diagnóstico

| Bloqueante | Estado |
|---|---|
| **BL1** códigos de departamento inestables | ✅ resuelto |
| **BL2** lista del AMBA corrida | ✅ resuelto |
| **BL7** tablas del paper desfasadas | ✅ resuelto, y ahora se generan |
| BL3 artefacto de maternidad | ❌ abierto — lote siguiente |
| BL4 tasa de error del `P19` | ❌ abierto |
| BL5 sesgo direccional del reparto (+17 %) | ❌ abierto, medido y declarado |
| BL6 H3 seleccionada por desenlace | ❌ abierto, declarado |

---

## 6. Cómo quedó armado (para revisar el código)

- `data/reference/crosswalk_departamentos.csv` — 15 componentes, con el criterio
  de cada equivalencia anotado fila por fila (hueco alfabético en el padrón 2022
  + continuidad poblacional contra el crecimiento provincial del decenio).
- `src/clean/padron_departamentos.py` — padrón oficial, resolución de nombres,
  crosswalk y las tres verificaciones (`verificar_geografia_2022`,
  `verificar_conservacion`, códigos nulos).
- `src/denominadores.py` — el join unidades ⋈ nacimientos, que estaba copiado en
  seis módulos, ahora en uno y verificado.
- `src/report/sync_tablas_paper.py` — genera las 10 tablas del paper desde
  `outputs/tables/`; `--check` falla si están desfasadas.
- `tests/test_padron_departamentos.py` (17 tests) y `tests/test_tablas_paper.py`.
  Suite completa: **61 pasan**.

La verificación clave es `verificar_conservacion`, y compara **grupo por grupo**,
no totales: los dos bugs de este lote conservaban el total nacional y rompían el
reparto interno, así que comparar totales no los habría detectado. Hay un test
que fija justamente eso
(`test_conservacion_compara_grupo_por_grupo_no_solo_el_total`).
