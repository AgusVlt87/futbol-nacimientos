# Hallazgos pendientes

Cosas encontradas mientras se ejecutaba un lote, fuera de su alcance. No se
tocaron. Van acá para no perderlas y para no ensanchar el lote en curso.

---

## Del lote 1 (`fix/geografia-departamental`, 2026-08-02)

### P1 — `outputs/` está en `.gitignore`, así que «el pipeline reproduce» no se puede verificar con git

`.gitignore` tiene `outputs/tables/*` y `outputs/figures/*` (solo se versiona
`.gitkeep`). En la tercera revisión afirmé que el pipeline reproducía porque
`git diff outputs/tables/` salía vacío. **Esa verificación era vacua**: git no
podía mostrar diferencias sobre archivos que no trackea.

El determinismo sí se verificó bien en este lote, congelando
`outputs/_baseline_3f07dba/` y comparando byte a byte (50 tablas idénticas entre
dos corridas). Pero no hay nada permanente que lo haga.

*Qué haría falta:* o versionar las tablas, o un `_run.json` por corrida con
hash del config, commit y checksums de las salidas —que es lo que ya proponía el
roast en su punto I6.

### P2 — La variante «localidad censal aislada» de H1 se movió al revés que la principal

Al arreglar el denominador, el χ² de H1 bajó en las dos variantes principales
(452,2 → 382,1 con aglomerado; 486,5 → 412,0 con los cortes de Côté) pero
**subió** en la variante de localidad aislada (633,7 → 692,5), y su RR se separó
más de la principal que antes (0,36 contra 0,45).

No es necesariamente un error: las dos variantes reparten el mismo denominador
departamental de forma distinta. Pero la variante de robustez ahora discrepa más
de la principal que antes de la corrección, y eso merece mirarse antes de seguir
usándola como control.

### P3 — CABA sigue afuera de la validación del denominador

`validar_contra_renaper` hace `dropna(subset=["departamento_id"])` y las filas de
CABA en RENAPER tienen ese campo nulo: la validación cubre 511 departamentos de
23 provincias, **cero de CABA**. Es la jurisdicción que encabeza H2 con
obs/esp = 2,63 y 962 jugadores. Ya estaba en `docs/roast.md` §1 y sigue abierto.

### P4 — Títulos de figura escritos a mano que la corrección dejó desalineados

`fig05` se titula «El AMBA y la Pampa producen tres veces más que el norte» y
ahora la barra de arriba es la Pampeana, no el AMBA. La afirmación sigue siendo
cierta (las dos son ~3× el norte) pero el orden del título ya no es el del
gráfico. Los títulos viven hardcodeados en `src/viz/make_figures.py`.

Es decisión de narrativa, no de código: queda para quien decida el encuadre.

### P5 — ~~El reparto de los partidos divididos es un supuesto nuevo, sin declarar~~ ✅ cerrado en el lote 2

Quedó declarado como limitación 3 de §4.3 del paper. Detalle y criterio por
componente en `data/reference/crosswalk_departamentos.csv`.

---

## Del lote 2 (`fix/artefacto-maternidad`, 2026-08-02)

### P6 — BDFA bloquea el acceso automatizado; BL4 necesita gestión, no código

El `robots.txt` de `bdfa.com.ar` (actualizado 2025-12-29) tiene
`User-agent: ClaudeBot` / `Disallow: /`, bajo un encabezado de «bloqueo de
scrapers detectados en ataque». No se scrapeó ni se evadió cambiando el
`User-Agent`.

La validación del `P19` contra un padrón independiente sigue pendiente y ahora
depende de una de estas tres: consulta manual de 150–200 fichas, autorización del
sitio, u otra fuente cuyos términos habría que verificar antes de asumir nada.

### P7 — El título de un recurso oficial no es su metodología

La serie del DEIS se publica como «nacimientos **ocurridos** por jurisdicción» y
es, dato por dato, la tabulación por **residencia de la madre**. Tres revisiones
del proyecto —el paper, `roast.md` y `re-analisis.md`— dieron por buena la
etiqueta del portal y construyeron argumentos encima.

Vale como regla general para este repo: **de una fuente oficial se verifica el
criterio contra el dato, no contra el título.** Barato de hacer cuando existe una
serie contrafáctica; caro de no hacer.

### P8 — La forma de escalón de H1 quedó sin explicación

El paper explicaba el escalón —tasa plana por debajo de ~10.000 habitantes y
salto en el decil superior— como la firma esperada del artefacto de maternidad.
Descartado ese mecanismo (§2.1.1), la forma sigue ahí y ya no tiene explicación
propuesta.

Es una pregunta abierta y probablemente interesante: un escalón único sugiere un
umbral (¿existencia de un club afiliado? ¿de una liga local?) más que un gradiente
de entorno. La expansión B5 de `re-analisis.md` —distancia al club afiliado más
cercano— es la que lo atacaría.
