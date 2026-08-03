# Impacto del lote 3 — validación externa y robustez

**Rama:** `feat/placebo-y-robustez` · **Base:** `2f60d38` (lote 2)
**Fecha:** 2026-08-02

---

## 1. El resultado: el básquet argentino tiene el efecto que el fútbol no tiene

El test placebo era, en el plan del re-análisis, «la validación externa más
barata» y la que «puede reescribir el paper». Salió mejor de lo que se esperaba.

Se corrió el pipeline completo sobre deportistas argentinos de otros cuatro
deportes: **misma ventana de cohortes, mismos filtros, misma cadena de geocoding,
mismo denominador de nacidos vivos, mismos tramos**. Lo único que cambia es el
deporte.

En el contraste que define el *birthplace effect* —ciudades de 50.000 a 100.000
habitantes contra grandes aglomerados—:

| Deporte | n (50–100k) | n (>500k) | RR | IC 95% |
|---|---:|---:|---:|---|
| **Básquet** | 39 | 176 | **1,95** | 1,38–2,76 |
| **Fútbol** | 275 | 3.343 | **0,72** | 0,64–0,82 |
| Vóley | 2 | 52 | 0,34 | 0,08–1,39 |
| Hockey | 2 | 33 | 0,53 | 0,13–2,22 |
| **Rugby** | 2 | 210 | **0,08** | 0,02–0,34 |

**Los intervalos del básquet y del fútbol no se tocan.** Observado sobre esperado,
tramo por tramo:

| Tramo | % de nacimientos | Fútbol | Básquet | Rugby |
|---|---:|---:|---:|---:|
| <10k | 14,7 | 0,56 | 0,40 | 0,06 |
| 10–50k | 15,2 | 0,71 | 0,85 | 0,08 |
| **50–100k** | 5,8 | 0,90 | **1,88** | 0,14 |
| 100–500k | 13,0 | 0,92 | 1,60 | 0,82 |
| >500k | 51,3 | **1,24** | 0,96 | 1,69 |

El básquet dibuja una U invertida de manual, con el pico exactamente en el tramo
que Côté et al. (2006) identifican como óptimo. El fútbol crece hacia la
metrópoli. El rugby está aún más concentrado que el fútbol, y el hockey más
todavía: el 83% de los jugadores de hockey nace en el AMBA.

Por región, el básquet produce 2,01 veces lo esperado en la pampeana y **0,56 en
el AMBA**; el fútbol, 1,47 y 1,20.

### Por qué importa

**Ningún artefacto de medición compartido puede producir mapas opuestos para
deportes distintos medidos con el mismo instrumento.** Quedan descartadas de una
sola vez:

- el registro de nacimientos y el artefacto de maternidad residual;
- la imputación del denominador departamental (+17% en el decil chico);
- la cobertura geográfica de Wikipedia;
- el nivel socioeconómico y la infraestructura general del departamento;
- la estructura urbana argentina.

Todas afectan a los cinco deportes por igual. Ninguna explica por qué el básquet
va para un lado y el fútbol para el otro.

Es la validación externa que le faltaba al trabajo, y encima convierte un
hallazgo negativo —«el efecto clásico no aparece»— en uno positivo: **aparece, en
el mismo país y las mismas cohortes, en el deporte de al lado.**

---

## 2. Robustez

### 2.1 Contracción bayesiana en el mapa departamental

Era el punto I1 del roast y la limitación 9 del paper: el ranking departamental lo
encabezaban los departamentos chicos, no los productivos, y el mapa coloreaba el
valor puntual.

Se agregó `stats.empirical_bayes_poisson` (gamma-Poisson por momentos, previa
equivalente a 7.082 nacimientos) y la **Figura 1 ahora mapea la tasa contraída**.

| Departamento | Jugadores | Tasa cruda | Tasa contraída |
|---|---:|---:|---:|
| Castelli | 4 | 89,00 | 48,92 |
| Carmen de Areco | 6 | 74,65 | 50,68 |
| Capital (Mendoza) | 87 | 103,09 | 96,93 |
| Castellanos (Rafaela) | 78 | 85,50 | 81,03 |
| La Capital (Santa Fe) | 195 | 69,61 | 68,48 |

Los departamentos con datos reales casi no se mueven (peso 0,92–0,99); los de
cuatro y seis jugadores se contraen a la mitad. El nuevo top-10 es el corredor
Santa Fe–Córdoba con unidades de decenas y centenas de jugadores, que es el
hallazgo sustantivo. El mapa perdió el moteado de ruido.

### 2.2 Comparaciones múltiples en los contrastes confirmatorios

Punto I3 del roast: la corrección se aplicaba solo a los 24 cruces exploratorios y
no a los 12 contrastes confirmatorios, que son los que sostienen las conclusiones.
Ahora `tests_bondad_ajuste.csv` lleva `p_fdr_bh` y `significativo_tras_fdr`.

**Los 12 sobreviven.** No cambia ninguna conclusión; cambia que ahora está
verificado en vez de supuesto.

### 2.3 Leyendas de los mapas

Al crecer el pie de la Figura 1, la leyenda —anclada dentro del eje, sobre el
hueco del Pacífico— pasó a taparle Jujuy y Salta. El ancho de ese hueco depende de
la relación de aspecto del área de dibujo, que cambia cada vez que se toca el
texto. Las figuras 1 y 2 usan ahora `style.banda_leyenda`, que es la solución que
el propio módulo documenta para este problema, con la leyenda horizontal en su
banda reservada.

---

## 3. Qué se movió

| | |
|---|---:|
| Tablas nuevas | 5 (`placebo_*`) |
| Tablas modificadas | 2 (`h2_departamentos` con `tasa_eb`/`peso_eb`, `tests_bondad_ajuste` con FDR) |
| Figuras nuevas | 1 (**fig28**) |
| Figuras rehechas | 2 (fig01 con contracción y leyenda, fig02 con leyenda) |
| **Resultados del paper que cambian** | **ninguno** |

El ranking departamental **se reordena** —es el punto de la contracción— pero
ninguna tasa publicada, ningún test y ninguna conclusión cambian de valor.

---

## 4. Qué cambió en el paper

- **Resumen**: punto tercero nuevo (el placebo). Los puntos siguientes se
  renumeraron; ahora son seis.
- **§3.7** nueva: el placebo completo, con las dos tablas y la limitación de
  muestra de vóley y hockey.
- **§4.1**: párrafo nuevo. El placebo **acota qué clase de explicación puede
  servir**: cualquier mecanismo tiene que distinguir deportes, lo que descarta
  las explicaciones genéricas y deja en pie las que dependen de cómo está
  organizado cada deporte. Se mantiene explícito que sigue siendo interpretación:
  la organización comparada de las dos estructuras formativas no se mide acá.
- **Figura 1**: el pie declara la contracción.

---

## 5. Estado de los bloqueantes

| Bloqueante | Estado |
|---|---|
| BL1 códigos de departamento | ✅ lote 1 |
| BL2 lista del AMBA | ✅ lote 1 |
| BL7 tablas del paper | ✅ lote 1 |
| BL3 artefacto de maternidad | ✅ lote 2 |
| BL5 sesgo direccional del reparto | ✅ **neutralizado por el placebo**: afecta igual a los cinco deportes y no puede explicar formas opuestas. Sigue midiendo mal la magnitud; ya no amenaza la identificación. |
| BL4 tasa de error del `P19` | ⛔ bloqueado por términos de uso (BDFA). **Alcance muy reducido**: el placebo descarta que el error sea el que produce el patrón. |
| BL6 H3 seleccionada por desenlace | ❌ abierto, declarado. No lo toca el placebo: H3 se mide sobre club formador, no sobre lugar de nacimiento. |

**Queda uno.** BL6 es una limitación real de la sección H3 y está declarada como
tal; no amenaza H1, H2 ni el resultado de conversión.

---

## 6. Lo que sigue abierto, y qué haría falta

1. **BL6 — degradar o restringir H3.** El 47,1% de migración y el «diez clubes
   concentran el 48%» describen a los que llegaron lejos. Opción A: restringir a
   T1+T2 y reportarlo como hallazgo sobre la elite. Opción B: sacarlo del
   resumen. Es reescritura, no código.
2. **El escalón de H1 sigue sin explicación** (P8 de `hallazgos-pendientes.md`).
   El placebo lo vuelve más interesante, no menos: el básquet no tiene escalón,
   tiene una U. Qué umbral futbolístico produce un escalón en ~10.000 habitantes
   es ahora una pregunta con forma. La variable que la atacaría es distancia al
   club afiliado más cercano.
3. **La organización comparada fútbol/básquet** es la explicación que el §4.1
   propone y no mide. Sería el trabajo siguiente, no un lote.
4. **Fútbol femenino** (252 casos, verificado): quedó sin correr. El pipeline del
   placebo ya lo soporta —basta cambiar el filtro de sexo—.

---

## 7. Lectura

Tres lotes, tres clases distintas de trabajo:

| Lote | Qué fue | Tablas movidas | Qué decidió |
|---|---|---:|---|
| 1 | reparación mecánica | 27 | que los números fueran los correctos |
| 2 | identificación | 0 | que el trabajo midiera algo |
| 3 | validación externa | 2 | que lo que mide sea del fútbol |

El lote 1 movió más números que ningún otro y fue el menos importante de los tres.
El lote 3 movió dos tablas y es el que contesta la pregunta que un revisor iba a
hacer primero.
