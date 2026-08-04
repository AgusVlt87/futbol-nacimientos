# Changelog de resultados

Qué afirmó cada versión del trabajo y por qué cambió. Vive fuera del paper a
propósito: el lector del paper no vio las versiones anteriores, y contarle que
«antes decíamos lo contrario» le agrega ruido en vez de información. La lección
metodológica sí queda en el paper (§4.2); el relato de cómo se llegó a ella, acá.

---

## 2026-08-03 · El club formador deja de estar seleccionado por el desenlace

**El problema.** H3 se apoyaba en el `primer_club`, que salía del vínculo `P54`
de Wikidata con fecha de inicio `P580`. Eso cubría el **40,9 %** de la muestra —y
no al azar: 99,2 % entre jugadores de selección, 12,7 % en el resto. La cobertura
seguía al nivel competitivo, que es el desenlace. H3 medía, literalmente, a los
que llegaron.

**Lo que se descartó primero.** Wikidata tiene club sin fecha para el 78 % de los
que no tenían `primer_club`, y 2.009 jugadores tienen exactamente uno, donde no
hay orden que resolver. Habría llevado la cobertura a 77 % gratis. Validado
contra los 106 clubes verificados a mano: **acierta el 52 %**, y falla
sistemáticamente hacia clubes posteriores y del exterior (Provincial Ovalle,
Sport Boys Warnes, Albacete B, Montréal). Wikidata anotó la etapa notable, no el
debut. **No se aplicó**: habría duplicado la cobertura empeorando el dato.

**Lo que se hizo.** El campo `equipo_debut` de la plantilla `{{Ficha de
deportista}}` de Wikipedia, que ningún bot volcó nunca al grafo. Bajado por la
API de acción de Wikimedia (CC BY-SA, publicada para uso programático): 5.511
jugadores en **218 pedidos HTTP**. El club se resuelve a QID por el destino del
enlace, nunca por el nombre. **No se usó Transfermarkt**, que tiene el dato con
mejor cobertura: sus términos de uso §11 prohíben la extracción automatizada, y
espaciar los pedidos no cambia eso.

**Por qué se puede mezclar con Wikidata**, medido contra los 106 clubes
verificados a mano:

| | cobertura (de 106) | precisión |
|---|---:|---:|
| Ficha de Wikipedia | 84 | 82,1 % (72,3–89,6) |
| Wikidata `P54`+`P580` | 51 | 88,2 % (76,1–95,6) |
| **cara a cara, n = 45** | — | **88,9 % las dos** |

McNemar exacto p = 1,00: empatan donde compiten. La diferencia aparente es que la
ficha cubre los casos difíciles que Wikidata no intenta. Y su error **no es
diferencial por estrato de nacimiento** (83,7 % metrópoli contra 80,5 % resto;
Fisher p = 0,78), que es la condición para que no sesgue el contraste de H3.

**Efecto en la cobertura.**

| | antes | después |
|---|---:|---:|
| muestra con `primer_club` | 2.254 (40,9 %) | **4.557 (82,7 %)** |
| T1 selección | 99,2 % | 100 % |
| T3 primera argentina | 59 % | 90,2 % |
| **T4 resto** | **12,7 %** | **72,1 %** |
| submuestra de H3 | 1.923 | **3.879** |

Por estrato de **nacimiento** la cobertura queda plana (81 a 88 % en los cinco
tramos), que es lo que hace falta para que el contraste geográfico no se sesgue.

**Efecto en los resultados. El sesgo existía y operaba en la dirección
esperada.**

| | antes (n = 1.923) | después (n = 3.879) |
|---|---:|---:|
| migra de provincia | 47,1 % | **44,5 %** |
| OR vs población general | 5,58 (5,10–6,10) | **5,03 (4,72–5,36)** |
| retención Pampeana | 48,9 % | 63,6 % |
| retención NOA | 28,9 % | 42,6 % |
| retención NEA | 8,6 % | 11,2 % |

El hallazgo sobrevive con el mismo signo y orden de magnitud; su magnitud estaba
inflada por medir solo a los que se habían mudado a un club grande. Las
retenciones suben en todas las regiones porque los jugadores que se incorporan
son, en proporción, los que se quedaron.

**Lo que no se movió**: H1, H2, el modelo con covariables (NBI sigue explicando
siete veces más que el tamaño; la distancia al club sigue colapsando a IRR 0,98
con p = 0,63), el ICC de 0,166 y el resultado de conversión juvenil → Mayor
(41,1 % contra 28,1 %, OR 1,78), que no dependen del club formador.

**Trampa nueva.** `wbgetentities` no sigue redirecciones, y en es.wikipedia los
enlaces a clubes usan casi siempre el nombre corto —«Rosario Central», «Boca
Juniors», «Newell's Old Boys»— que redirige a la razón social completa. Sin
resolverlas se perdían 608 jugadores, y **no al azar: los de los clubes más
grandes**, que son justamente los que tienen nombre corto de uso corriente. La
cobertura de QID pasó de 69,5 % a 79,5 % al agregar la segunda pasada.

Módulos: `src/ingest/wikipedia_fichas.py`, `src/clean/build_club_debut.py`,
`src/ingest/wikidata_clubs_wiki.py`, `src/analysis/validar_club_wiki.py`.

---

## 2026-08-02 · Sesgo del numerador y fragilidad del resultado condicional

**Qué se corrigió.**

1. **La granularidad del `P19` no es aleatoria** y nadie la había mirado. Entre
   los jugadores cuyo lugar de nacimiento es una provincia entera, el NOA, Cuyo y
   el NEA están sobrerrepresentados entre 2,7 y 2,9 veces respecto de los que
   tienen localidad (χ²(5) = 72,9; p < 10⁻¹³). Esos casos se excluyen del
   análisis de tamaño de ciudad, así que la exclusión le saca futbolistas al
   interior. La cota —atribuir los 486 excluidos al tramo menor— lleva el RR de
   0,45 a **0,96**. Módulo: `src/analysis/run_sesgo_granularidad.py`.

2. **La conversión juvenil → Mayor estaba inflada por un bug de tipos.**
   `metro = tramo.eq(">500k")` devuelve `False` —no `NaN`— cuando `tramo` es
   nulo, de modo que el `dropna(subset=["metro"])` posterior no descartaba nada
   y los diez juveniles sin ciudad asignada entraban al contraste como si
   hubieran nacido fuera de un gran aglomerado. Eran exactamente los que §2.4
   excluye del análisis de tamaño: el contraste usaba un criterio distinto del
   resto del trabajo.

   | | antes | después |
   |---|---|---|
   | fuera de gran aglomerado | 44 de 105 (41,9 %) | **39 de 95 (41,1 %)** |
   | OR | 1,85 (1,14–2,98) | **1,78 (1,09–2,93)** |
   | p (Fisher) | 0,013 | **0,027** |

3. **El resultado condicional depende de un solo estrato.** El *leave-one-stratum-out*
   que faltaba: excluyendo el tramo de 10.000 a 50.000 habitantes —25 casos— el
   OR cae a 1,42 y el intervalo cruza el 1. Dejó de presentarse como «el
   resultado más robusto del trabajo».

4. **Se agregó el problema del *collider*.** Condicionar en «llegó a un juvenil»
   es condicionar en un nodo al que apuntan tanto el origen como el talento; el
   OR es consistente con la historia del filtro de acceso pero también con
   cualquier otra selección diferencial.

**Qué se agregó.**

- **Control positivo** (`run_edad_relativa.py`): el efecto de la edad relativa,
  el hallazgo más replicado del área. El corpus lo recupera limpio (Q1/Q4 = 2,09;
  χ²(3) = 443,5) y con la intensificación por nivel que predice la literatura.
  Complementa al placebo: aquel muestra que el instrumento no inventa señal,
  éste que sabe encontrarla.
- **Auditoría de prosa** en `sync_tablas_paper --check`. Sincronizar las tablas
  no alcanzaba: el abstract decía 12,9 donde la tabla generada decía 12,7 y nada
  lo detectaba, porque la cifra vivía en una oración y no en un bloque marcado.

**Cifras de la prosa que estaban desfasadas:** tasa del tramo `<10k` (12,9 →
12,7), muestra departamental (5.389 → 5.401), valores de los deciles de §3.1, y
la etiqueta del último grupo de cohortes (2005–2009 → 2005–2008, que es donde
termina la ventana).

---

## 2026-08-01 · Geografía departamental

Dos errores de códigos de departamento, ninguno de los cuales fallaba
ruidosamente porque los dos conservaban los totales provinciales y rompían el
reparto interno.

1. **Los códigos del INDEC no son estables entre censos**: 44 de 532 cambiaron
   entre 1991 y 2022, casi todos por las divisiones de partidos bonaerenses de
   1994. Se perdían **1.049.301 nacimientos** (4,6 % del total, 70 % de ellos del
   Gran Buenos Aires) del denominador por ciudad. Magdalena encabezaba el ranking
   departamental con 163 futbolistas por 100.000 y era enteramente un artefacto:
   su valor real es 65.

2. **La lista de los 24 partidos del GBA estaba corrida un lugar**: doce de
   veinticuatro apuntaban a otro partido. El «AMBA» del estudio excluía Quilmes,
   Merlo, San Miguel, Tres de Febrero y Vicente López, e incluía La Plata, Marcos
   Paz, Pilar y Presidente Perón.

**Efecto:** la región pampeana pasa a producir más que el AMBA (34,5 contra
28,3) y la razón interior/AMBA pasa de 0,59 a 0,79. **Versiones anteriores
afirmaban lo contrario**, y presentaban además como lección metodológica que el
cambio de denominador había puesto al AMBA por encima de la pampeana. Esa
inversión era el error, no un hallazgo.

---

## 2026-07-31 · Denominador de nacidos vivos

Se reemplazó la población censada en 2022 por los nacidos vivos de cada cohorte
(DEIS, 1914–2024). El RR de las localidades de menos de 10.000 habitantes contra
los grandes aglomerados pasó de 0,57 a 0,45: los pueblos son exportadores netos
de población, así que contar a sus residentes de 2022 subestimaba cuánta gente
había nacido ahí e inflaba su tasa.

---

## 2026-07-30 · Bug de granularidad `provincia`

110 jugadores cuyo `P19` es una provincia entera quedaban clavados en el
departamento donde cae el centroide provincial. Ullum (San Juan) y Tumbaya
(Jujuy) llegaban al top-12 nacional de tasa con la totalidad de su cuenta
fabricada; Azul quedaba inflado un 222 %. Es la misma trampa que «Argentina» →
General Levalle, un nivel más arriba.
