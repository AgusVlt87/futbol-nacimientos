"""Genera las tablas de `reports/paper.md` desde `outputs/tables/`.

**Por qué existe.** Las tablas del paper estaban escritas a mano. Cuando se
arregló el bug de granularidad `provincia` —110 jugadores fantasma— las tablas de
`outputs/` se regeneraron y la tabla regional del §3.2 quedó vieja: cinco de sus
seis filas dejaron de coincidir con `h2_regiones.csv`, y el paper siguió
publicando 2.659 futbolistas para la región pampeana cuando el pipeline decía
2.600. Nadie lo notó porque nada comparaba las dos cosas.

Arreglar la instancia era reescribir seis números. Arreglar la clase es esto: el
paper deja de tener números propios y pasa a tener bloques generados.

**Cómo funciona.** En `paper.md` cada tabla vive entre dos marcas:

    <!-- TABLA:h1_tramos INICIO -->
    ... contenido generado, no editar a mano ...
    <!-- TABLA:h1_tramos FIN -->

Uso:
    python -m src.report.sync_tablas_paper            # reescribe las tablas
    python -m src.report.sync_tablas_paper --check    # falla si están desfasadas

El modo `--check` es el que hace cumplir la regla: devuelve código 1 si alguna
tabla del paper no coincide con lo que sale de `outputs/tables/`.
"""

from __future__ import annotations

import argparse
import re
import sys

import pandas as pd

from src.common import get_logger, paths

log = get_logger("report.tablas")

MARCA = re.compile(r"(<!-- TABLA:(?P<id>[\w-]+) INICIO -->\n)(?P<cuerpo>.*?)(<!-- TABLA:(?P=id) FIN -->)",
                   re.DOTALL)

AVISO = "<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->"


# --------------------------------------------------------------------------- #
# Utilidades de formato
# --------------------------------------------------------------------------- #
def _mil(x: float, dec: int = 0) -> str:
    """Formato argentino: punto para miles, coma para decimales."""
    if pd.isna(x):
        return "—"
    s = f"{x:,.{dec}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _tabla(encabezados: list[str], alineacion: list[str], filas: list[list[str]]) -> str:
    sep = {"i": "---", "d": "---:", "c": ":---:"}
    out = ["| " + " | ".join(encabezados) + " |",
           "|" + "|".join(sep[a] for a in alineacion) + "|"]
    out += ["| " + " | ".join(f) + " |" for f in filas]
    return "\n".join(out)


def _leer(p, nombre: str) -> pd.DataFrame:
    return pd.read_csv(p.tables / f"{nombre}.csv")


def _ic(lo: float, hi: float, dec: int = 2) -> str:
    return f"{_mil(lo, dec)}–{_mil(hi, dec)}"


# --------------------------------------------------------------------------- #
# Constructores, uno por tabla del paper
# --------------------------------------------------------------------------- #
def t_muestra(p) -> str:
    a, b = _leer(p, "qa_players_filtros"), _leer(p, "qa_muestra_analisis")
    filas = [[r["paso"].capitalize(), _mil(r["n"])] for _, r in a.iterrows()]
    filas += [[r["paso"].capitalize(), _mil(r["n"])] for _, r in b.iterrows()][1:]
    filas[-1] = [f"**{filas[-1][0]}**", f"**{filas[-1][1]}**"]
    return _tabla(["Paso", "n"], ["i", "d"], filas)


def t_h1_tramos(p) -> str:
    d = _leer(p, "h1_tramos_principal")
    filas = []
    for _, r in d.iterrows():
        neg = r["unidad"] == ">500k"
        f = [r["unidad"], _mil(r["jugadores"]), _mil(r["nacimientos"]),
             _mil(r["tasa"], 1), _ic(r["tasa_ic_lo"], r["tasa_ic_hi"], 1),
             "1,00" if neg else f"{_mil(r['RR'], 2)} ({_ic(r['RR_ic_lo'], r['RR_ic_hi'], 2)})"]
        filas.append([f"**{x}**" for x in f] if neg else f)
    return _tabla(["Tamaño de la ciudad", "Futbolistas", "Nacidos", "Tasa /100.000",
                   "IC 95%", "RR vs >500k"], ["i", "d", "d", "d", "i", "i"], filas)


def t_h1_robustez(p) -> str:
    fuentes = [("Principal (aglomerado urbano)", "h1_tramos_principal"),
               ("Unidad = localidad censal aislada", "h1_robustez_localidad_sola"),
               ("Solo cohortes ≤ 2002", "h1_robustez_carrera_completa")]
    filas = []
    for etiqueta, tabla in fuentes:
        r = _leer(p, tabla).set_index("unidad").loc["<10k"]
        filas.append([etiqueta, _mil(r["RR"], 2), _ic(r["RR_ic_lo"], r["RR_ic_hi"], 2)])
    return _tabla(["Variante", "RR <10k vs >500k", "IC 95%"], ["i", "d", "i"], filas)


def t_h2_regiones(p) -> str:
    d = _leer(p, "h2_regiones").sort_values("tasa", ascending=False)
    filas = [[r["region"] if "region" in d.columns else r["unidad"],
              _mil(r["jugadores"]), _mil(r["tasa"], 1),
              _ic(r["tasa_ic_lo"], r["tasa_ic_hi"], 1), _mil(r["RR"], 2)]
             for _, r in d.iterrows()]
    return _tabla(["Región", "Futbolistas", "Tasa /100.000", "IC 95%", "RR vs AMBA"],
                  ["i", "d", "d", "i", "d"], filas)


def t_h2_provincias(p) -> str:
    d = _leer(p, "h2_provincias").sort_values("tasa", ascending=False).reset_index(drop=True)
    col = "provincia" if "provincia" in d.columns else "unidad"
    filas = []
    for i in list(range(5)) + [None] + list(range(len(d) - 3, len(d))):
        if i is None:
            filas.append(["…", "", "", "", ""])
            continue
        r = d.loc[i]
        filas.append([str(i + 1), str(r[col]), _mil(r["jugadores"]),
                      _mil(r["tasa"], 1), _mil(r["obs_sobre_esp"], 2)])
    return _tabla(["", "Provincia", "Futbolistas", "Tasa /100.000", "Obs./Esp."],
                  ["d", "i", "d", "d", "d"], filas)


def t_h3_poblacion(p) -> str:
    d = _leer(p, "h3_migracion_vs_poblacion")
    filas = [[r["grupo"], _mil(r["n"]), f"**{_mil(r['pct_fuera_de_su_provincia'], 1)}%**"
              if "Futbolistas" in r["grupo"] else f"{_mil(r['pct_fuera_de_su_provincia'], 1)}%"]
             for _, r in d[d["n"].notna()].iterrows()]
    return _tabla(["Grupo", "n", "Fuera de su provincia"], ["i", "d", "d"], filas)


def t_h3_tamano(p) -> str:
    d = _leer(p, "h3_migracion_por_tamano_origen")
    filas = [[r["tramo"], _mil(r["jugadores"]), f"{_mil(r['pct_cambia_departamento'], 1)}%",
              f"{_mil(r['pct_cambia_provincia'], 1)}%", f"{_mil(r['km_mediana'], 0)} km"]
             for _, r in d.iterrows()]
    return _tabla(["Ciudad de nacimiento", "n", "Cambia de departamento",
                   "Cambia de provincia", "Distancia mediana"],
                  ["i", "d", "d", "d", "d"], filas)


def t_h3_regiones(p) -> str:
    d = _leer(p, "h3_saldo_por_region").sort_values("saldo_neto", ascending=False)
    filas = [[r["region"], _mil(r["nacidos"]), _mil(r["formados"]),
              f"{'+' if r['saldo_neto'] > 0 else ''}{_mil(r['saldo_neto'])}",
              f"{_mil(r['pct_retencion'], 1)}%"] for _, r in d.iterrows()]
    return _tabla(["Región", "Nacidos", "Formados allí", "Saldo neto", "Retención"],
                  ["i", "d", "d", "d", "d"], filas)


def t_clubes(p) -> str:
    d = _leer(p, "futbol_clubes_formadores").head(6)
    filas = [[r["primer_club"], _mil(r["formados"]), f"{_mil(r['km_mediana'], 0)} km",
              f"{_mil(r['pct_de_otra_provincia'], 0)}%"] for _, r in d.iterrows()]
    return _tabla(["Club", "Formados", "Distancia mediana", "De otra provincia"],
                  ["i", "d", "d", "d"], filas)


def t_conversion(p) -> str:
    d = _leer(p, "seleccion_conversion_por_tramo")
    filas = []
    for _, r in d.iterrows():
        neg = r["tramo"] == ">500k"
        f = [r["tramo"], _mil(r["juveniles"]), _mil(r["llegan_a_mayor"]),
             _mil(r["pct_conversion"], 1), _ic(r["ic_lo"], r["ic_hi"], 1)]
        filas.append([f"**{x}**" for x in f] if neg else f)
    return _tabla(["Ciudad de nacimiento", "Juveniles", "Llegan a la Mayor", "%", "IC 95%"],
                  ["i", "d", "d", "d", "i"], filas)


CONSTRUCTORES = {
    "muestra": t_muestra,
    "h1_tramos": t_h1_tramos,
    "h1_robustez": t_h1_robustez,
    "h2_regiones": t_h2_regiones,
    "h2_provincias": t_h2_provincias,
    "h3_poblacion": t_h3_poblacion,
    "h3_tamano": t_h3_tamano,
    "h3_regiones": t_h3_regiones,
    "clubes": t_clubes,
    "conversion": t_conversion,
}


# --------------------------------------------------------------------------- #
def sincronizar(texto: str, p) -> tuple[str, list[str]]:
    vistos: list[str] = []

    def reemplazo(m: re.Match) -> str:
        tid = m.group("id")
        vistos.append(tid)
        if tid not in CONSTRUCTORES:
            raise KeyError(f"no hay constructor para la tabla {tid!r}. "
                           f"Conocidos: {sorted(CONSTRUCTORES)}")
        return m.group(1) + AVISO + "\n" + CONSTRUCTORES[tid](p) + "\n" + m.group(4)

    return MARCA.sub(reemplazo, texto), vistos


def main() -> int:
    ap = argparse.ArgumentParser(description="Sincroniza las tablas del paper")
    ap.add_argument("--check", action="store_true",
                    help="no escribe; falla si el paper está desfasado")
    args = ap.parse_args()

    p = paths()
    destino = p.reports / "paper.md"
    original = destino.read_text(encoding="utf-8")
    nuevo, vistos = sincronizar(original, p)

    faltan = sorted(set(CONSTRUCTORES) - set(vistos))
    if faltan:
        log.warning("constructores sin marca en el paper: %s", faltan)

    if args.check:
        if nuevo != original:
            log.error("las tablas del paper NO coinciden con outputs/tables/. "
                      "Correr `python -m src.report.sync_tablas_paper`.")
            return 1
        log.info("las %d tablas del paper coinciden con outputs/tables/", len(vistos))
        return 0

    if nuevo == original:
        log.info("sin cambios: las %d tablas ya estaban al día", len(vistos))
    else:
        destino.write_text(nuevo, encoding="utf-8")
        log.info("actualizadas %d tablas en %s", len(vistos), destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
