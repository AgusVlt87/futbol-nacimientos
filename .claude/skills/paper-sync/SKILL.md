---
name: paper-sync
description: Revisa el repo completo, verifica el paper contra los outputs generados y lo reescribe cuando divergen. Usala siempre que el usuario pida revisar, verificar, actualizar, sincronizar o reescribir el paper, o cuando mencione que cambiaron números del pipeline, que corrigió un bug, que reprocesó datos, o que el paper "quedó viejo" — incluso si no dice explícitamente la palabra "reescribir". También cuando pregunte si alguna afirmación del paper sigue siendo cierta.
---

# paper-sync

## Principio rector

El paper es un **output derivado** del repo, no un documento independiente. Cuando el texto y los datos generados divergen, ganan los datos. Toda la skill se sigue de eso.

Corolario incómodo: **el resultado válido más frecuente es "no hace falta reescribir nada"**. Si el paper está sincronizado, decilo y terminá. Reescribir un documento que ya está bien es una regresión disfrazada de trabajo — introducís deriva de prosa a cambio de nada.

## Precondición: no reescribas sobre números que están por cambiar

Antes de leer una sola línea del paper, verificá el estado del repo:

1. El working tree está commiteado. Si no, pedí que se commitee o stashee antes de seguir.
2. El pipeline corre limpio de punta a punta y las tablas de `outputs/` se regeneran sin diff.
3. La suite de tests pasa.
4. No hay bloqueantes abiertos que muevan números publicados. Revisá `docs/` en busca de diagnósticos o reportes de impacto sin resolver.

**Si alguna falla, parás y lo reportás.** Sincronizar el paper contra un pipeline roto produce un documento que hay que reescribir dos veces.

---

## Fase 1 — Inventario de afirmaciones

No leas el paper como texto. Desarmalo en afirmaciones verificables.

Extraé **todos** los numerales del documento —tasas, conteos, estadísticos de test, intervalos, porcentajes, tamaños de muestra— y buscá cada uno en las tablas generadas. Es mecánico y conviene scriptearlo: a ojo se escapan justo los que importan.

Armá una tabla con una fila por afirmación:

| Afirmación | Ubicación | Estado | Evidencia |
|---|---|---|---|

Estados posibles:

- **RESPALDADA** — el número o la afirmación aparece en una tabla generada.
- **DESACTUALIZADA** — existe respaldo pero con otro valor. Anotá los dos.
- **SIN RESPALDO** — no hay tabla que la sostenga. Puede ser prosa interpretativa legítima o un número tipeado a mano que nunca existió.
- **CONTRADICHA** — los datos actuales dicen lo contrario.
- **NO VERIFICABLE** — afirmación sobre literatura externa o interpretación. No la toques en esta fase.

El inventario es el insumo de todo lo demás. No pases a la Fase 2 sin él.

## Fase 2 — Declarar el alcance antes de escribir

Según lo que muestre el inventario, la reescritura cae en uno de estos niveles. **Declaralo explícitamente antes de tocar el documento**, porque cada nivel tiene un costo distinto y el usuario tiene derecho a frenarte en el primero:

- **Nivel 0 — Nada.** Todo respaldado. Reportá y terminá.
- **Nivel 1 — Números.** Solo hay valores desactualizados. Se actualizan y no se toca una palabra de la prosa.
- **Nivel 2 — Secciones.** Alguna afirmación cambió de signo o de magnitud lo suficiente como para que el párrafo que la interpreta ya no se sostenga. Se reescriben esas secciones.
- **Nivel 3 — Encuadre.** Un resultado central cambió y el argumento del paper depende de él. Esto **no lo ejecutás**: lo proponés y esperás.

## Fase 3 — Reescritura

### Reglas de preservación

Un paper reescrito por un modelo tiende a converger hacia prosa académica genérica: más fluida, más prudente en la forma, más vacía en el contenido. Eso es una regresión aunque se lea mejor. Contra eso:

- **Ninguna limitación desaparece en silencio.** Si sacás una porque quedó resuelta, decí en el reporte cuál y por qué. Si el paper reconocía un problema y el problema sigue, el reconocimiento se queda, aunque incomode.
- **No suavices las frases filosas.** Las declaraciones donde el paper admite que su propia defensa metodológica no alcanza son su mayor activo frente a un revisor. Sobreviven, con esas palabras o equivalentes igual de directas.
- **Cada número sale de una tabla generada.** Ninguno tipeado a mano. Si un número que querés poner no existe en `outputs/`, generalo primero o no lo pongas.
- **Cero citas inventadas.** Autor, año y título verificados, o no va. Si no podés verificar una referencia que ya estaba, marcala en el reporte en vez de arrastrarla.
- **El alcance de la prosa es el alcance del diseño.** Si el análisis es descriptivo, la redacción es descriptiva. Nada de verbos causales sobre correlaciones de área.
- **No agregues hallazgos.** Si algo interesante aparece en los datos y no está en el paper, va al reporte como propuesta, no al paper como texto nuevo.
- **Mantené la voz del documento.** Estás sincronizando, no reescribiendo el estilo de otro.

### Cómo dejar el trabajo

Rama nueva. El paper anterior queda accesible en el historial de git — no hagas copias `paper_old.md` que después nadie borra.

## Fase 4 — Verificación mecánica

Volvé a extraer todos los numerales del documento reescrito y verificá que cada uno exista en una tabla generada. Si el repo tiene un chequeo propio para esto, usá el del repo.

Reportá el resultado de la verificación con números concretos: cuántas afirmaciones se revisaron, cuántas quedaron respaldadas, cuántas quedaron pendientes y cuáles.

Una reescritura que no pasa su propia verificación no está terminada.

## Fase 5 — Reporte

Escribí `docs/paper-sync-<fecha>.md`:

- El inventario de la Fase 1 completo.
- Nivel de reescritura aplicado y por qué.
- Qué cambió, sección por sección.
- **Qué afirmaciones cambiaron de signo.** Sección aparte, arriba, no enterrada.
- Qué se eliminó y por qué.
- Qué quedó pendiente de decisión humana.
- Resultado de la verificación de la Fase 4.

---

## Lo que no decidís solo

Estas cosas se proponen y se esperan. No son cobardía procedimental: son las decisiones donde el criterio del autor no es sustituible.

- Un resultado central que se da vuelta y obliga a reencuadrar el argumento.
- Eliminar o degradar una hipótesis.
- Cambiar la posición del trabajo frente a la literatura.
- Sacar una sección entera.

En todos estos casos: escribí la propuesta con la evidencia, mostrá cómo quedaría, y parás.

## Chequeo final antes de entregar

Cinco preguntas, honestamente:

1. ¿Cada número del paper sale de una tabla generada?
2. ¿Alguna limitación desapareció sin que lo haya declarado?
3. ¿Algún párrafo quedó más fluido y menos preciso que antes?
4. ¿Agregué alguna afirmación que los datos no sostienen?
5. ¿Reescribí algo que en realidad no hacía falta reescribir?

Si la respuesta a la 5 es sí, revertí esa parte. Es el error más fácil de cometer y el más difícil de detectar después.