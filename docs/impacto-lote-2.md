# Impacto del lote 2 — el criterio del registro

**Rama:** `fix/artefacto-maternidad` · **Base:** `bc1d350` (lote 1)
**Fecha:** 2026-08-02 · **Alcance ejecutado:** BL3 (resuelto), BL4 (bloqueado, acotado por otra vía)

---

## 1. El resultado

**El artefacto de las maternidades no está operando.** Era la limitación central
declarada del paper, el bloqueante B3 del roast y el BL3 de mi diagnóstico: las
tres revisiones coincidían en que era el punto de falla del trabajo. Resulta que
la premisa que lo sostenía era falsa, y se puede demostrar con los datos.

### 1.1 El denominador cuenta residencias, no partos

El DEIS publica dos series de nacidos vivos por jurisdicción:

| Serie | Cómo se titula | Cobertura |
|---|---|---|
| La que usa el estudio | «nacimientos **ocurridos**» | 1914–2024 |
| La contrafáctica (nueva) | por **residencia de la madre** | 2005–2022 |

En las **432 celdas provincia×año** en que se solapan:

| | |
|---|---:|
| Celdas comparadas | 432 |
| Celdas con diferencia | **0** |
| Diferencia absoluta máxima | **0** |
| Total serie histórica | 12.420.066 |
| Total por residencia | 12.420.066 |

Son el mismo dato. El caso decisivo es CABA: sus maternidades atienden partos de
todo el conurbano, así que por ocurrencia debería mostrar un exceso grande sobre
la residencia. Coincide año por año al dígito, los 18 años.

**La afirmación de §2.1 del paper —que la serie cuenta partos y que por eso
comparte definición con el `P19`— era falsa.** Se apoyaba en el título del
recurso en el portal, no en el dato. El roast lo había sospechado y lo dejó como
«no verificado»; ahora está verificado y resuelto en contra de lo que el paper
afirmaba.

### 1.2 El numerador registra el pueblo, no el parto

Si el `P19` de Wikidata anotara el lugar del parto, las localidades sin maternidad
tendrían **cero** futbolistas, y la tasa por tamaño de localidad tendría forma de
**escalón** en el umbral en que una localidad puede sostener una maternidad.

| Habitantes de la localidad | Futbolistas | Localidades distintas | Tasa /100.000 |
|---|---:|---:|---:|
| <500 | 16 | 12 | 10,8 |
| 500–1k | 15 | 12 | 6,3 |
| 1–2k | 45 | 39 | 9,6 |
| 2–5k | 128 | 91 | 12,7 |
| 5–10k | 205 | 112 | 15,0 |
| 10–20k | 202 | 89 | 12,4 |
| 20–50k | 446 | 118 | 18,0 |
| >50k | 4.191 | 119 | 26,8 |

**76 futbolistas tienen su `P19` en localidades de menos de 2.000 habitantes,
repartidos en 63 localidades distintas.** Emiliano Sala figura nacido en Cululú,
Santa Fe, **106 habitantes**. José Basanta en Tres Sargentos, Buenos Aires, 456.
Ahí no hay ni puede haber maternidad: lo que Wikidata registra es de dónde es el
jugador, no dónde lo pariéron.

Y la serie no tiene forma de escalón: sube irregularmente desde el tramo más
chico, con el `<500` (10,8) por encima del `500–1k` (6,3) y del `1–2k` (9,6). Un
umbral de maternidad produciría ceros seguidos de un salto, no eso.

### 1.3 Lo que queda

La versión fuerte del artefacto queda refutada. Queda la débil: que **alguna**
fracción de los registros de Wikidata anote la ciudad cabecera.

**Cota superior: 44,5%.** Se calcula del peor modo posible —atribuyendo *todo* el
déficit de las localidades chicas a mala atribución y *nada* a un efecto real—,
así que es un techo, no una estimación. Que 63 localidades de menos de 2.000
habitantes aparezcan como lugar de nacimiento sugiere un valor bastante menor,
pero medirlo requiere BL4.

---

## 2. BL4 — bloqueado, y por qué

La validación del `P19` contra un padrón independiente **no se hizo**. La fuente
candidata era la Base de Datos del Fútbol Argentino (`bdfa.com.ar`). Su
`robots.txt`, actualizado el 2025-12-29, incluye:

```
# === BLOQUEO DE SCRAPERS DETECTADOS EN ATAQUE ===
User-agent: ClaudeBot
Disallow: /
```

Es una restricción explícita, reciente y dirigida. No la evadí cambiando el
`User-Agent`: eso sería justamente burlarla. **BL4 sigue abierto.**

Qué lo destrabaría, en orden de costo:

1. **Consulta manual** de 150–200 fichas, estratificada por tramo de tamaño. El
   `robots.txt` gobierna el acceso automatizado, no que una persona mire el sitio.
2. **Pedir autorización** al sitio: es un proyecto no comercial y el uso es
   académico.
3. **Otra fuente**: habría que verificar términos antes de asumir nada. No probé
   ninguna.

Lo importante es que **§1.2 acota buena parte de lo que BL4 iba a contestar**. La
pregunta que BL4 sigue teniendo que responder ya no es «¿qué registra el `P19`?»
sino «¿con qué tasa de error lo registra?», que es una pregunta más chica.

---

## 3. Números que se movieron

**Ninguno.** Las 27 tablas del pipeline son idénticas a las del lote 1: este lote
no cambió ningún cálculo, cambió lo que se puede afirmar sobre ellos. Se agregaron
cinco tablas nuevas (`criterio_denominador_*`, `criterio_p19_*`) y una figura
(**fig27**).

Es la diferencia entre un lote de reparación y uno de identificación.

---

## 4. Qué cambió en el paper

Además de lo que el lote 1 dejó pendiente, que se aplicó acá.

### 4.1 Nuevo

- **§2.1.1**, sección nueva: las dos pruebas del criterio del registro.
- **Resumen**, punto segundo nuevo: el artefacto no está operando.
- **Figura 27**.
- **§4.3, limitación 3** nueva: el reparto de los partidos divididos es un
  segundo supuesto (venía de P5 de `hallazgos-pendientes.md`).

### 4.2 Corregido

| Dónde | Antes | Ahora |
|---|---|---|
| §2.1 | «no se puede verificar que ambas puntas usen la misma definición» | verificado: las dos usan residencia |
| §2.1 | «el reparto intraprovincial es el único supuesto» | es el principal; hay un segundo |
| §4.3 lim. 1 | «la limitación más seria y no está acotada» | acotada; queda la versión débil con techo de 44,5% |
| Resumen | AMBA 35,0 y Pampa 30,2 «cuadruplican al NOA» | Pampeana 34,5 y AMBA 28,3, **en ese orden** |
| §3.2 | «el interior no produce más que el AMBA» | el AMBA no encabeza: la pampeana produce 22% más |
| §4.2 | «el AMBA pasó de estar por debajo de la pampeana a estar por encima» | esa inversión era el bug; se documentan los dos errores de geografía |
| §3.1 | χ² 452,2 · RR 0,42 · IRR 1,181 · 3.459 ciudades | 382,1 · 0,45 · 1,175 · 3.477 |
| §3.4 | 15,3 vs 7,5 por millón; «17 en el AMBA» | 14,3 vs 7,4; 17,8 pampeana y 14,2 AMBA |
| §3.1 | el escalón «es la forma que produciría el registro del parto» | ese mecanismo queda descartado; la forma pide otra explicación |
| §4.3 lim. 2 | corregir el sesgo llevaría el RR de 0,42 a 0,49 | de 0,45 a 0,52 |
| §4.1 | los diez clubes están «en el AMBA, Rosario o La Plata» | La Plata ya no es AMBA en la definición corregida |
| Resumen | NEA retiene 8,3%, AMBA 91,6% | 8,6% y 90,8% |

Las 10 tablas del paper se generan desde `outputs/tables/` desde el lote 1, así
que se actualizaron solas y el test lo verifica.

---

## 5. Qué queda del diagnóstico

| Bloqueante | Estado |
|---|---|
| BL1 códigos de departamento inestables | ✅ lote 1 |
| BL2 lista del AMBA corrida | ✅ lote 1 |
| BL7 tablas del paper desfasadas | ✅ lote 1 |
| **BL3 artefacto de maternidad** | ✅ **resuelto: no opera; versión débil con techo de 44,5%** |
| **BL4 tasa de error del `P19`** | ⛔ **bloqueado por términos de uso**; alcance reducido por §1.2 |
| BL5 sesgo direccional del reparto (+17%) | ❌ abierto, medido y declarado |
| BL6 H3 seleccionada por desenlace | ❌ abierto, declarado |

De los siete, quedan dos y medio, y ninguno de los dos que quedaban abiertos por
falta de dato lo sigue estando por la misma razón.

---

## 6. Lectura

El trabajo entró a este lote con su limitación central sin acotar y sale con ella
resuelta en una dirección que nadie —ni el paper, ni el roast, ni mi propio
diagnóstico— había considerado: **las tres revisiones dieron por buena la premisa
de que el DEIS contaba partos, porque así se titula el recurso en el portal.**
Ninguna la probó. Bastaba comparar dos archivos del mismo organismo.

Vale registrar la asimetría del esfuerzo: el lote 1 fueron dos días de trabajo
mecánico que movieron 27 tablas; este lote fue una descarga de 68 MB y dos
`groupby`, y no movió ninguna, pero es el que decide si el trabajo mide algo.

Lo que sigue pendiente es de otra naturaleza. BL5 y BL6 están medidos y
declarados: son limitaciones honestas de un trabajo descriptivo, no defectos.
BL4 necesita una gestión con un sitio, no más código.
