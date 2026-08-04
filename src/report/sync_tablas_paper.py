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

MARCA_TEX = re.compile(r"(% TABLA:(?P<id>[\w-]+) INICIO\n)(?P<cuerpo>.*?)(% TABLA:(?P=id) FIN)",
                       re.DOTALL)

AVISO = "<!-- generado por `python -m src.report.sync_tablas_paper`; no editar a mano -->"
AVISO_TEX = "% generado por `python -m src.report.sync_tablas_paper`; no editar a mano"


# --------------------------------------------------------------------------- #
# Utilidades de formato
# --------------------------------------------------------------------------- #
def _mil(x: float, dec: int = 0) -> str:
    """Formato argentino: punto para miles, coma para decimales."""
    if pd.isna(x):
        return "—"
    s = f"{x:,.{dec}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# Formato de salida del bloque que se está generando. Los constructores no saben
# en qué formato escriben: arman filas y `_tabla` las renderiza según el destino.
_FORMATO = "md"


def _tabla(encabezados: list[str], alineacion: list[str], filas: list[list[str]]) -> str:
    if _FORMATO == "tex":
        return _tabla_tex(encabezados, alineacion, filas)
    sep = {"i": "---", "d": "---:", "c": ":---:"}
    out = ["| " + " | ".join(encabezados) + " |",
           "|" + "|".join(sep[a] for a in alineacion) + "|"]
    out += ["| " + " | ".join(f) + " |" for f in filas]
    return "\n".join(out)


# Reemplazos de celda -> LaTeX. El orden importa: primero los que escapan
# caracteres reservados, después los que introducen backslashes propios.
# `inputenc` en modo utf8 no conoce ≥, ≤, ×, →, ‰ ni las flechas; sin esta tabla
# la compilación falla con «Unicode character not set up for use with LaTeX».
_TEX_ESCAPES = (
    ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), ("$", r"\$"),
    ("≥", r"$\geq$"), ("≤", r"$\leq$"), ("×", r"$\times$"), ("÷", r"$\div$"),
    ("→", r"$\rightarrow$"), ("≈", r"$\approx$"), ("±", r"$\pm$"),
    ("–", "--"), ("—", "---"), ("…", r"\dots"), ("‰", r"\textperthousand"),
    ("<", r"$<$"), (">", r"$>$"),
)


def _a_tex(celda: str) -> str:
    """Markdown de celda -> LaTeX. Cubre lo que los constructores producen."""
    negrita = celda.startswith("**") and celda.endswith("**")
    s = celda.strip("*")
    for a, b in _TEX_ESCAPES:
        s = s.replace(a, b)
    return rf"\textbf{{{s}}}" if negrita else s


def _tabla_tex(encabezados: list[str], alineacion: list[str],
               filas: list[list[str]]) -> str:
    cols = "".join({"i": "l", "d": "r", "c": "c"}[a] for a in alineacion)
    out = [rf"\begin{{tabular}}{{@{{}}{cols}@{{}}}}", r"\toprule",
           " & ".join(rf"\textbf{{{_a_tex(h)}}}" if h else "" for h in encabezados) + r"\\",
           r"\midrule"]
    out += [" & ".join(_a_tex(c) for c in f) + r"\\" for f in filas]
    out += [r"\bottomrule", r"\end{tabular}"]
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
# Auditoría de la prosa
# --------------------------------------------------------------------------- #
# Sincronizar las tablas no alcanza. El abstract decía «12,9 futbolistas cada
# 100.000» mientras la tabla generada decía 12,7, y nada lo detectaba porque la
# cifra vivía en una oración, no en un bloque marcado. Un referee lo encontró en
# veinte minutos.
#
# Cada entrada define una cifra que aparece en la prosa: de dónde sale y con qué
# tolerancia se compara. `--check` extrae del documento los números que rodean a
# `contexto` y falla si ninguno coincide. No reescribe la prosa —eso pediría
# entender la oración— pero impide que se desfase en silencio.
def _valor(p, tabla: str, columna: str, filtro=None, escala: float = 1.0) -> float:
    d = _leer(p, tabla)
    if filtro is not None:
        d = d[filtro(d)]
    return float(d[columna].iloc[0]) * escala


def _frase(texto: str) -> str:
    """Frase literal -> regex que tolera saltos de línea.

    El `.tex` y el `.md` van envueltos a 80 columnas, así que cualquier frase de
    más de unas pocas palabras tiene un salto de línea adentro en algún lugar
    impredecible. Buscar la frase con espacios literales encuentra unas
    apariciones y se pierde otras — que fue lo que pasó con la del abstract.
    """
    return r"\s+".join(re.escape(w) for w in texto.split())


CIFRAS = {
    "tasa_menos_10k": dict(
        contexto=_frase("nacidos en localidades de menos de"),
        valor=lambda p: _valor(p, "h1_tramos_principal", "tasa",
                               lambda d: d["unidad"] == "<10k"),
        dec=1),
    "tasa_mas_500k": dict(
        contexto=_frase("en aglomerados de más de"),
        valor=lambda p: _valor(p, "h1_tramos_principal", "tasa",
                               lambda d: d["unidad"] == ">500k"),
        dec=1),
    "conversion_fuera": dict(
        contexto=_frase("fuera de un gran aglomerado llegan a la Mayor"),
        valor=lambda p: _valor(p, "seleccion_conversion_tests", "fuera_metro_pct"),
        dec=1),
    "conversion_or": dict(
        contexto=_frase("OR cae a"),
        valor=lambda p: _valor(p, "seleccion_conversion_loso", "OR",
                               lambda d: d["tramo_excluido"] == "10–50k"),
        dec=2),
    # H3. Estas tres se movieron al sumar el club de las fichas de Wikipedia y
    # el paper las repetía viejas sin que nada avisara: no estaban registradas.
    "h3_migracion_pct": dict(
        contexto=_frase("se forma fuera de su provincia de nacimiento contra"),
        valor=lambda p: _valor(p, "h3_migracion_vs_poblacion",
                               "pct_fuera_de_su_provincia",
                               lambda d: d["grupo"].str.startswith("Futbolistas")),
        dec=1),
    "h3_or": dict(
        contexto=_frase("general que reside fuera de su provincia de nacimiento"),
        valor=lambda p: _valor(p, "h3_migracion_vs_poblacion", "OR",
                               lambda d: d["OR"].notna()),
        dec=2),
    "h3_n": dict(
        contexto=_frase("jugadores con origen y club formador ubicados"),
        valor=lambda p: _valor(p, "h3_migracion_vs_poblacion", "n",
                               lambda d: d["grupo"].str.startswith("Futbolistas")),
        dec=0),
}


def _numeros(texto: str) -> set[float]:
    """Todos los números con coma decimal o enteros que aparecen en un fragmento."""
    out = set()
    for m in re.finditer(r"\d[\d.]*(?:,\d+)?", texto):
        s = m.group(0).replace(".", "").replace(",", ".")
        try:
            out.add(float(s))
        except ValueError:
            pass
    return out


def auditar_prosa(texto: str, p, ventana: int = 220) -> list[str]:
    """Cifras de la prosa que no coinciden con `outputs/tables/`.

    Basta con que **una** de las apariciones del contexto tenga el valor al lado.
    Exigirlo en todas daba falsos positivos legítimos: la discusión cita el OR de
    la conversión sin repetir el porcentaje, y eso no es un desfasaje. Lo que
    importa es que el documento diga el número correcto en alguna parte y que no
    haya quedado uno viejo cuando el pipeline cambió: si la cifra se mueve,
    ninguna aparición coincide y el chequeo falla igual.
    """
    problemas = []
    for nombre, spec in CIFRAS.items():
        try:
            esperado = round(spec["valor"](p), spec["dec"])
        except (FileNotFoundError, IndexError, KeyError):
            continue
        apariciones = list(re.finditer(spec["contexto"], texto))
        if not apariciones:
            continue
        vistos_total: set[float] = set()
        for m in apariciones:
            frag = texto[max(0, m.start() - ventana): m.end() + ventana]
            vistos_total |= {round(v, spec["dec"]) for v in _numeros(frag)}
        if esperado not in vistos_total:
            problemas.append(
                f"{nombre}: outputs/tables dice {esperado} y la prosa no lo "
                f"menciona en ninguna de las {len(apariciones)} apariciones de "
                f"«{apariciones[0].group(0)[:45].strip()}…» "
                f"(encontrados: {sorted(v for v in vistos_total if v < 1e4)[:10]})")
    return problemas


# --------------------------------------------------------------------------- #
def sincronizar(texto: str, p, formato: str = "md") -> tuple[str, list[str]]:
    """Reescribe los bloques marcados con la tabla que sale de `outputs/tables/`.

    El mismo constructor sirve para el markdown y para el LaTeX: lo único que
    cambia es cómo se renderizan las filas. Así el `.md` y el `.tex` no pueden
    divergir entre sí ni del pipeline, que es exactamente como el `.tex` quedó
    cuatro lotes atrasado respecto del `.md`.
    """
    global _FORMATO
    vistos: list[str] = []
    marca, aviso = (MARCA_TEX, AVISO_TEX) if formato == "tex" else (MARCA, AVISO)

    def reemplazo(m: re.Match) -> str:
        tid = m.group("id")
        vistos.append(tid)
        if tid not in CONSTRUCTORES:
            raise KeyError(f"no hay constructor para la tabla {tid!r}. "
                           f"Conocidos: {sorted(CONSTRUCTORES)}")
        return m.group(1) + aviso + "\n" + CONSTRUCTORES[tid](p) + "\n" + m.group(4)

    anterior, _FORMATO = _FORMATO, formato
    try:
        return marca.sub(reemplazo, texto), vistos
    finally:
        _FORMATO = anterior


def main() -> int:
    ap = argparse.ArgumentParser(description="Sincroniza las tablas del paper")
    ap.add_argument("--check", action="store_true",
                    help="no escribe; falla si el paper está desfasado")
    args = ap.parse_args()

    p = paths()
    destinos = [(p.reports / "paper.md", "md"),
                (p.root / "paper" / "paper.tex", "tex")]
    codigo = 0
    for destino, formato in destinos:
        if not destino.exists():
            log.warning("no existe %s; se omite", destino)
            continue
        original = destino.read_text(encoding="utf-8")
        nuevo, vistos = sincronizar(original, p, formato)
        if not vistos:
            log.warning("%s no tiene ninguna marca de tabla", destino.name)
            continue
        if args.check:
            if nuevo != original:
                log.error("%s NO coincide con outputs/tables/. "
                          "Correr `python -m src.report.sync_tablas_paper`.", destino.name)
                codigo = 1
            else:
                log.info("%s: las %d tablas coinciden con outputs/tables/",
                         destino.name, len(vistos))
            # Las tablas pueden estar al día y la prosa desfasada: son dos
            # mecanismos distintos y el segundo no tiene marcas que sincronizar.
            for problema in auditar_prosa(original, p):
                log.error("%s [prosa] %s", destino.name, problema)
                codigo = 1
            continue
        if nuevo == original:
            log.info("%s: las %d tablas ya estaban al día", destino.name, len(vistos))
        else:
            destino.write_text(nuevo, encoding="utf-8")
            log.info("%s: actualizadas %d tablas", destino.name, len(vistos))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
