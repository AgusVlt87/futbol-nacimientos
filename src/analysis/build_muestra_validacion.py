"""Fase 12 — Muestra para validar el `P19`, y la herramienta para codificarla.

Genera dos cosas:

    outputs/validacion/codificar.html   la herramienta: se abre con doble clic
    outputs/validacion/muestra_p19_clave.csv   la clave, que no se mira hasta el final

El diseño estadístico está en `docs/plan-validacion-p19.md`; acá va lo operativo.

**Qué hace el muestreo y por qué.**

1. Estratifica por tamaño de ciudad, colapsado al contraste que tiene potencia:
   metrópoli (>500k) contra todo lo demás. Los cinco tramos por separado no dan
   casos suficientes para estimar una tasa de error en cada uno.
2. Sortea con semilla fija, así la muestra es reproducible.
3. **Mezcla las filas y no muestra el estrato.** Si el que codifica sabe que está
   mirando un caso «de pueblo», busca distinto — y lo que se mide es justamente
   si el error depende del tamaño del lugar. Es el sesgo que hay que evitar por
   encima de cualquier otro.
4. **No muestra ni el `P19` ni el club cargado.** Se anota primero lo que dice
   la fuente; la comparación la hace después `run_correccion_p19`. Si uno ve el
   valor cargado, lo confirma en vez de verificarlo.
5. **Valida dos variables, no una.** El club de debut resultó tan poco confiable
   como el lugar de nacimiento: en el 24 % de los casos Wikidata registra el
   primer vínculo a los 21 años o más —imposible que sea el club formador— y esa
   proporción es mayor entre los nacidos en localidades chicas (31 % contra 21 %
   en las metrópolis). Como H3 se apoya entero en esa variable, entra a la
   validación con el mismo diseño y sin costo marginal: el dato está en la misma
   página que el otro.

**Una sola persona codifica.** El manual de investigación pediría dos, para poder
reportar el acuerdo entre ambas. Con una sola no hay acuerdo que medir, y eso hay
que declararlo como limitación. A cambio, cada caso queda con su URL de respaldo,
que es verificable por cualquiera: es peor que dos codificadores y muchísimo mejor
que ningún dato.

Uso:
    python -m src.analysis.build_muestra_validacion [--n 300] [--semilla 20260802]
"""

from __future__ import annotations

import argparse
import json
from urllib.parse import quote_plus

import numpy as np
import pandas as pd

from src.common import get_logger, load_config, paths
from src.viz import style

log = get_logger("analysis.validacion")


def _buscar(texto: str) -> str:
    return "https://duckduckgo.com/?q=" + quote_plus(texto)


PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Validación de lugar de nacimiento y club de debut</title>
<style>
  :root {{
    --surface: {surface}; --ink: {ink}; --ink2: {ink2}; --muted: {muted};
    --grid: {grid}; --primary: {primary}; --accent: {accent}; --ok: #0ca30c;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--surface); color: var(--ink);
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 16px; line-height: 1.5;
  }}
  .wrap {{ max-width: 760px; margin: 0 auto; padding: 24px 20px 80px; }}

  header {{ display: flex; align-items: baseline; gap: 16px; margin-bottom: 4px; }}
  h1 {{ font-size: 19px; margin: 0; letter-spacing: -0.01em; }}
  .sub {{ color: var(--ink2); font-size: 13.5px; margin: 2px 0 20px; }}

  .barra {{ height: 6px; background: var(--grid); border-radius: 3px; overflow: hidden; }}
  .barra > div {{ height: 100%; background: var(--primary); width: 0%; transition: width .2s; }}
  .cuenta {{ font-size: 13px; color: var(--ink2); margin: 8px 0 22px;
             display: flex; justify-content: space-between; }}
  .cuenta b {{ color: var(--ink); font-variant-numeric: tabular-nums; }}

  .tarjeta {{ background: #fff; border: 1px solid var(--grid); border-radius: 10px;
              padding: 22px 24px; box-shadow: 0 1px 2px rgba(11,11,11,.04); }}
  .nombre {{ font-size: 27px; font-weight: 650; letter-spacing: -0.02em; margin: 0; }}
  .meta {{ color: var(--ink2); font-size: 14px; margin: 6px 0 18px; }}
  .meta span {{ margin-right: 18px; }}

  .buscar {{ display: flex; gap: 10px; margin-bottom: 22px; flex-wrap: wrap; }}
  .buscar a {{
    flex: 1 1 200px; text-align: center; text-decoration: none;
    background: var(--primary); color: #fff; padding: 11px 14px;
    border-radius: 7px; font-size: 14.5px; font-weight: 550;
  }}
  .buscar a.alt {{ background: #fff; color: var(--primary);
                   border: 1.5px solid var(--primary); }}
  .buscar a:hover {{ filter: brightness(1.08); }}

  label {{ display: block; font-size: 13px; color: var(--ink2);
           margin: 0 0 5px; font-weight: 550; }}
  .campo {{ margin-bottom: 15px; }}
  .fila {{ display: flex; gap: 14px; }}
  .fila > .campo {{ flex: 1; }}
  input {{
    width: 100%; padding: 10px 12px; font-size: 15.5px; font-family: inherit;
    border: 1.5px solid var(--grid); border-radius: 7px; background: #fff;
    color: var(--ink);
  }}
  input:focus {{ outline: none; border-color: var(--primary); }}
  .pista {{ font-size: 12.5px; color: var(--muted); margin-top: 4px; }}

  .acciones {{ display: flex; gap: 10px; margin-top: 22px; align-items: center; }}
  button {{
    font-family: inherit; font-size: 15px; font-weight: 600; cursor: pointer;
    padding: 11px 20px; border-radius: 7px; border: none;
  }}
  .guardar {{ background: var(--ok); color: #fff; }}
  .saltear {{ background: #fff; color: var(--ink2); border: 1.5px solid var(--grid); }}
  .nav {{ background: none; color: var(--ink2); border: none; padding: 11px 8px; }}
  button:disabled {{ opacity: .4; cursor: default; }}
  .crece {{ flex: 1; }}

  .pie {{ margin-top: 26px; display: flex; gap: 10px; align-items: center;
          flex-wrap: wrap; }}
  .exportar {{ background: var(--ink); color: #fff; }}
  .aviso {{ font-size: 12.5px; color: var(--muted); margin-top: 14px; }}

  details {{ margin-top: 26px; font-size: 13.5px; color: var(--ink2); }}
  summary {{ cursor: pointer; font-weight: 600; color: var(--ink); }}
  details ul {{ padding-left: 20px; }}
  details li {{ margin: 6px 0; }}
  .listo {{ text-align: center; padding: 50px 20px; }}
  .listo h2 {{ font-size: 22px; }}
  kbd {{ background: var(--grid); border-radius: 4px; padding: 1px 6px;
         font-size: 12.5px; font-family: inherit; }}
</style>
</head>
<body>
<div class="wrap">
  <header><h1>¿Dónde nació y dónde debutó?</h1></header>
  <p class="sub">Dos datos por jugador, de una fuente pública. No hace falta que
  sepas de fútbol: alcanza con leer y pegar el link.</p>

  <div class="barra"><div id="progreso"></div></div>
  <div class="cuenta">
    <span>Caso <b id="pos">1</b> de <b>{total}</b></span>
    <span><b id="hechos">0</b> completados · <b id="restantes">{total}</b> por hacer</span>
  </div>

  <div id="app"></div>

  <div class="pie">
    <button class="exportar" onclick="exportar()">Descargar lo hecho (CSV)</button>
    <button class="saltear" onclick="borrar()">Empezar de cero</button>
  </div>
  <p class="aviso">Se guarda solo en este navegador a medida que anotás. Podés
  cerrar y seguir después. Cuando termines —o cuando quieras cortar— descargá el
  CSV y guardalo en <code>outputs/validacion/</code>.</p>

  <details>
    <summary>Qué anotar, y qué no</summary>
    <ul>
      <li><b>No uses Wikipedia ni Wikidata.</b> De ahí salió el dato que estamos
      verificando: de 400 casos, 363 vienen de una Wikipedia. Mirarla no verifica
      nada.</li>
      <li><b>Tampoco Transfermarkt ni BDFA</b>, que no permiten este uso.</li>
      <li><b>Sí sirven:</b> el sitio del club, notas de prensa, entrevistas,
      archivos de diarios, el propio jugador en redes.</li>
      <li><b>Si la fuente solo dice la provincia</b>, poné la provincia y dejá la
      localidad vacía. Es un dato válido.</li>
      <li><b>Si no encontrás nada, tocá «No lo encontré».</b> Eso también es un
      resultado. Inventar uno arruina la medición; dejarlo vacío no.</li>
      <li><b>El club de debut también lo estamos verificando</b>, así que tampoco
      te lo mostramos. El dato que tenemos cargado está mal seguido: en 1 de cada 4
      casos Wikidata registra el primer club recién a los 21 años o más, cuando el
      jugador ya había debutado en otro lado.</li>
      <li>Podés anotar uno de los dos datos y dejar el otro vacío. Media respuesta
      sirve; una inventada no.</li>
    </ul>
  </details>

  <details>
    <summary>Por qué la ficha no muestra el lugar que ya tenemos cargado</summary>
    <p>Porque si lo ves, lo confirmás en vez de verificarlo. Vale igual para el
    club. Y por eso tampoco dice de qué tamaño es la ciudad: lo que se está
    midiendo es si el error depende del tamaño del lugar, así que saberlo
    cambiaría cómo buscás.</p>
  </details>
</div>

<script>
const CASOS = {datos};
const CLAVE = "validacion_p19_v1";
let datos = JSON.parse(localStorage.getItem(CLAVE) || "{{}}");
let i = 0;

const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c =>
  ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));

function primerPendiente() {{
  const k = CASOS.findIndex(c => !datos[c.caso]);
  return k === -1 ? CASOS.length - 1 : k;
}}

function guardar() {{
  localStorage.setItem(CLAVE, JSON.stringify(datos));
  const n = Object.keys(datos).length;
  $("hechos").textContent = n;
  $("restantes").textContent = CASOS.length - n;
  $("progreso").style.width = (100 * n / CASOS.length) + "%";
}}

function pintar() {{
  if (i >= CASOS.length) {{
    $("app").innerHTML = `<div class="tarjeta listo"><h2>Terminaste los ${{CASOS.length}}</h2>
      <p class="sub">Descargá el CSV y guardalo en <code>outputs/validacion/</code>.</p></div>`;
    $("pos").textContent = CASOS.length;
    return;
  }}
  const c = CASOS[i], y = datos[c.caso] || {{}};
  $("pos").textContent = i + 1;
  $("app").innerHTML = `
    <div class="tarjeta">
      <p class="nombre">${{esc(c.nombre)}}</p>
      <p class="meta"><span>Nacido en <b>${{c.anio}}</b></span></p>

      <div class="buscar">
        <a href="${{c.b1}}" target="_blank" rel="noopener">Buscar «nació en»</a>
        <a class="alt" href="${{c.b2}}" target="_blank" rel="noopener">Buscar «debutó en»</a>
      </div>

      <div class="fila">
        <div class="campo">
          <label for="loc">1 · Localidad o ciudad donde nació</label>
          <input id="loc" value="${{esc(y.localidad)}}" autocomplete="off"
                 placeholder="ej. Rafaela">
          <div class="pista">Vacío si la fuente solo dice la provincia</div>
        </div>
        <div class="campo">
          <label for="prov">Provincia</label>
          <input id="prov" value="${{esc(y.provincia)}}" autocomplete="off"
                 placeholder="ej. Santa Fe">
        </div>
      </div>
      <div class="campo">
        <label for="club">2 · Club donde debutó en primera</label>
        <input id="club" value="${{esc(y.club)}}" autocomplete="off"
               placeholder="ej. Instituto">
        <div class="pista">El primer club profesional, no el de inferiores ni el
        actual. Vacío si no lo encontrás.</div>
      </div>
      <div class="campo">
        <label for="url">3 · Link de dónde lo sacaste</label>
        <input id="url" value="${{esc(y.fuente)}}" autocomplete="off"
               placeholder="pegá la dirección de la página">
        <div class="pista">Sin esto el caso no cuenta: es lo que lo hace verificable</div>
      </div>

      <div class="acciones">
        <button class="guardar" onclick="ok()">Guardar y seguir</button>
        <button class="saltear" onclick="noEncontrado()">No lo encontré</button>
        <span class="crece"></span>
        <button class="nav" onclick="mover(-1)" ${{i === 0 ? "disabled" : ""}}>‹ Anterior</button>
        <button class="nav" onclick="mover(1)">Siguiente ›</button>
      </div>
      <p class="pista" style="margin-top:12px">
        <kbd>Enter</kbd> guarda y pasa al siguiente</p>
    </div>`;
  $("loc").focus();
  ["loc", "prov", "club", "url"].forEach(id =>
    $(id).addEventListener("keydown", e => {{ if (e.key === "Enter") ok(); }}));
}}

function ok() {{
  const c = CASOS[i];
  const loc = $("loc").value.trim(), prov = $("prov").value.trim();
  if (!loc && !prov) {{ $("loc").focus(); return; }}
  datos[c.caso] = {{ localidad: loc, provincia: prov,
                    club: $("club").value.trim(),
                    fuente: $("url").value.trim(), encontrado: 1 }};
  guardar(); i++; pintar();
}}

function noEncontrado() {{
  datos[CASOS[i].caso] = {{ localidad: "", provincia: "", club: "",
                            fuente: "", encontrado: 0 }};
  guardar(); i++; pintar();
}}

function mover(d) {{ i = Math.max(0, Math.min(CASOS.length, i + d)); pintar(); }}

function exportar() {{
  const filas = [["caso", "localidad_encontrada", "provincia_encontrada",
                  "club_debut_encontrado", "fuente_url", "encontrado"]];
  CASOS.forEach(c => {{
    const y = datos[c.caso];
    if (y) filas.push([c.caso, y.localidad, y.provincia, y.club || "",
                       y.fuente, y.encontrado]);
  }});
  if (filas.length === 1) {{ alert("Todavía no hay nada anotado."); return; }}
  const csv = filas.map(f => f.map(v =>
    `"${{String(v).replace(/"/g, '""')}}"`).join(",")).join("\\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["\\ufeff" + csv], {{type: "text/csv"}}));
  a.download = "validacion_p19_codificado.csv";
  a.click();
}}

function borrar() {{
  if (!confirm("Se borra todo lo anotado en este navegador. ¿Seguro?")) return;
  datos = {{}}; localStorage.removeItem(CLAVE); i = 0; guardar(); pintar();
}}

guardar();
i = primerPendiente();
pintar();
</script>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Muestra para validar el P19")
    ap.add_argument("--n", type=int, default=300,
                    help="tamaño total de la muestra (default 300: 150 por brazo)")
    ap.add_argument("--semilla", type=int, default=20260802)
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    salida = p.root / "outputs" / "validacion"
    salida.mkdir(parents=True, exist_ok=True)

    pl = pd.read_parquet(p.processed / "analysis_players.parquet")
    places = pd.read_parquet(p.interim / "places_resolved.parquet")
    pl = pl.merge(places[["place_qid", "label"]].rename(columns={"label": "p19_label"}),
                  left_on="birthplace_qid", right_on="place_qid", how="left")

    marco = pl[pl["tramo"].notna()].copy()
    ref = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"]
    marco["estrato"] = np.where(marco["tramo"].eq(ref), "metropoli", "resto")

    por_brazo = args.n // 2
    partes = []
    for estrato, grupo in marco.groupby("estrato"):
        if len(grupo) < por_brazo:
            log.warning("estrato %s tiene %d casos, menos que los %d pedidos",
                        estrato, len(grupo), por_brazo)
        partes.append(grupo.sample(min(por_brazo, len(grupo)), random_state=args.semilla))
    muestra = pd.concat(partes, ignore_index=True)

    # Se mezcla ANTES de numerar: el orden no puede correlacionar con el estrato,
    # o a mitad de la planilla se deduce cuál es cuál.
    muestra = muestra.sample(frac=1.0, random_state=args.semilla + 1).reset_index(drop=True)
    muestra["caso"] = np.arange(1, len(muestra) + 1)

    # --- la clave: aparte, y no se mira hasta terminar -----------------------
    muestra[["caso", "player_qid", "nombre", "p19_label", "prov_nombre",
             "localidad_nombre", "tramo", "estrato", "birth_year"]].to_csv(
        salida / "muestra_p19_clave.csv", index=False, encoding="utf-8")

    # --- la herramienta -----------------------------------------------------
    casos = [
        {"caso": int(r.caso), "nombre": r.nombre, "anio": int(r.birth_year),
         "b1": _buscar(f'"{r.nombre}" futbolista "nació en"'),
         "b2": _buscar(f'"{r.nombre}" futbolista "debutó en" primera')}
        for r in muestra.itertuples()
    ]

    html = PAGINA.format(
        total=len(casos),
        datos=json.dumps(casos, ensure_ascii=False),
        surface=style.SURFACE, ink=style.INK, ink2=style.INK_2,
        muted=style.MUTED, grid=style.GRID,
        primary=style.PRIMARY, accent=style.ACCENT)
    destino = salida / "codificar.html"
    destino.write_text(html, encoding="utf-8")

    log.info("muestra de %d casos, semilla %d", len(casos), args.semilla)
    log.info("\n%s", muestra.groupby("estrato").size().to_string())
    log.info("herramienta lista: %s", destino)
    log.info("abrila con doble clic; al terminar descargá el CSV a %s", salida)


if __name__ == "__main__":
    main()
