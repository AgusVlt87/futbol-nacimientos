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

### P5 — El reparto de los partidos divididos es un supuesto nuevo, sin declarar en el paper

Para bajar de un partido que ya no existe (General Sarmiento, Morón viejo,
Esteban Echeverría viejo) a los partidos actuales, el crosswalk reparte su
población según la proporción que tienen los sucesores en el primer censo en que
aparecen separados. **Supone que esa proporción describe la que tenían antes de
dividirse.**

Es más débil que el resto de la cadena y hay que declararlo en §4.3 del paper,
junto con el reparto intraprovincial. Detalle y criterio por componente en
`data/reference/crosswalk_departamentos.csv`.
