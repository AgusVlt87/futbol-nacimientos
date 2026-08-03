# Baseline congelado — antes del lote 1

Las 50 tablas de `outputs/tables/` tal como estaban en el commit `c138fca`
(sobre `3f07dba`), **antes** de reparar la geografía departamental.

Se versionan —a diferencia del resto de `outputs/`, que está en `.gitignore` por
ser regenerable— porque este baseline **ya no es regenerable con el código
actual**: es el estado con los dos bugs de geografía adentro. Sin él, verificar
las cifras de `docs/impacto-lote-1.md` obliga a volver a `c138fca` y re-correr
todo el pipeline.

Se verificó que el pipeline era determinista antes de congelarlo: dos corridas
completas dan estas 50 tablas byte a byte idénticas.

**No consumir estas tablas para nada.** Los números vigentes están en
`outputs/tables/`. Estos están mal: el denominador por ciudad pierde 1.049.301
nacimientos y la definición del AMBA incluye La Plata y excluye Quilmes.
