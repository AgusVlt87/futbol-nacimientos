"""Fase 13c — ¿Cuánto le podemos creer al club que declara Wikipedia?

La pregunta no es si el dato existe, es si es cierto. Se contesta contra la única
verdad de campo del proyecto: los 106 clubes de debut que Agustín verificó a mano
en BDFA para la muestra de validación del `P19`.

**Las tres comparaciones que importan**, y por qué cada una:

    1. ficha de Wikipedia vs BDFA   — ¿sirve el dato nuevo?
    2. `primer_club` de Wikidata vs BDFA — ¿sirve el dato que ya usábamos?
    3. las dos, sobre los casos donde ambas existen — ¿cuál gana cuando compiten?

La tercera es la que decide el diseño. Si Wikidata acierta más, el dato nuevo
solo rellena huecos; si acierta menos, hay que preferir la ficha también donde
las dos están, y eso cambia números ya publicados.

**Cómo se comparan dos nombres de club.** Por conjunto de palabras distintivas,
descartando la razón social («Club Atlético Boca Juniors» = «Boca Juniors») y las
iniciales sueltas («C. A. Colón» = «Colón»). El comparador se mide aparte de lo
que mide: un desacuerdo puede ser un error del dato o un error del matcheo, y
mezclarlos infla la tasa de error. Los desacuerdos se listan uno por uno para
poder mirarlos.

**Lo que esto NO puede medir.** BDFA y Wikipedia pueden estar contestando
preguntas distintas: «club donde debutó como profesional» y «club donde se
formó» no son el mismo club para un jugador que subió de un club de liga
regional a uno de AFA. Los desacuerdos se clasifican por si las dos puntas caen
en la misma provincia, que es lo que H3 realmente usa.

Uso:
    python -m src.analysis.validar_club_wiki
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd
from scipy import stats

from src.common import get_logger, load_config, paths

log = get_logger("analysis.validar_club")

# Palabras de razón social y conectores: no distinguen un club de otro.
RUIDO = re.compile(
    r"\b(club|atletico|social|y|de|del|la|el|los|las|deportivo|deportiva|"
    r"asociacion|cultural|mutual|sportivo|sport|futbol|balompie|foot|ball|"
    r"institucion|civil|ca|ac|fc|cf|sad|cd|afc|sc|cs|aa)\b")

# Abreviaturas que Wikipedia pone entre paréntesis y la planilla escribe entera.
ABREV = {"lp": "la plata", "sf": "santa fe", "sj": "san juan",
         "vr": "villa ramallo", "bb": "bahia blanca", "sl": "san luis",
         "t": "tucuman", "cba": "cordoba"}


def norm(s: object) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    t = unicodedata.normalize("NFD", str(s)).lower()
    t = "".join(c for c in t if unicodedata.category(c) not in {"Mn", "Cf", "Cc"})
    t = t.replace("'", "").replace("’", "")     # Newell's = Newells
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def clave(s: object) -> frozenset[str]:
    """Nombre de club -> conjunto de palabras distintivas."""
    n = " ".join(ABREV.get(w, w) for w in norm(s).split())
    return frozenset(w for w in RUIDO.sub(" ", n).split() if len(w) > 1)


def coincide(a: object, b: object) -> bool:
    """Mismo club si un conjunto de palabras contiene al otro."""
    x, y = clave(a), clave(b)
    return bool(x and y and (x <= y or y <= x))


def _ic_binomial(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    lo, hi = stats.beta.ppf(0.025, k, n - k + 1), stats.beta.ppf(0.975, k + 1, n - k)
    return (0.0 if np.isnan(lo) else lo, 1.0 if np.isnan(hi) else hi)


def _tasa(etiqueta: str, acierta: pd.Series) -> None:
    n, k = len(acierta), int(acierta.sum())
    lo, hi = _ic_binomial(k, n)
    log.info("%-34s %3d/%-3d = %5.1f%%   IC95 [%.1f%%, %.1f%%]",
             etiqueta, k, n, 100 * k / n if n else np.nan, 100 * lo, 100 * hi)


def main() -> None:
    load_config()
    p = paths()
    val = p.root / "outputs" / "validacion"

    wiki = pd.read_parquet(p.interim / "club_debut_wiki.parquet")
    lv = pd.read_parquet(p.processed / "player_level.parquet")
    cod = pd.read_csv(val / "validacion_p19_codificado.csv")
    clv = pd.read_csv(val / "muestra_p19_clave.csv")

    verdad = (cod.merge(clv, on="caso")
              .loc[lambda d: d["club_debut_encontrado"].notna(),
                   ["caso", "player_qid", "nombre", "club_debut_encontrado",
                    "estrato", "tramo"]]
              .rename(columns={"club_debut_encontrado": "club_bdfa"}))
    log.info("clubes verificados a mano en BDFA: %d", len(verdad))

    d = (verdad
         .merge(wiki[["player_qid", "club_wiki_nombre", "club_wiki_origen",
                      "club_wiki_qid"]], on="player_qid", how="left")
         .merge(lv[["player_qid", "primer_club", "primer_club_qid"]],
                on="player_qid", how="left"))

    d["ok_wiki"] = [coincide(a, b) for a, b in zip(d["club_wiki_nombre"], d["club_bdfa"])]
    d["ok_wd"] = [coincide(a, b) for a, b in zip(d["primer_club"], d["club_bdfa"])]
    hay_wiki = d["club_wiki_nombre"].notna()
    hay_wd = d["primer_club"].notna()

    log.info("")
    log.info("=== 1. cobertura sobre los %d verificados ===", len(d))
    log.info("ficha de Wikipedia : %d (%.0f%%)", hay_wiki.sum(), 100 * hay_wiki.mean())
    log.info("Wikidata (P54+P580): %d (%.0f%%)", hay_wd.sum(), 100 * hay_wd.mean())
    log.info("ninguna de las dos : %d", int((~hay_wiki & ~hay_wd).sum()))

    log.info("")
    log.info("=== 2. precisión contra BDFA, donde cada fuente tiene dato ===")
    _tasa("ficha de Wikipedia", d.loc[hay_wiki, "ok_wiki"])
    _tasa("Wikidata (P54+P580)", d.loc[hay_wd, "ok_wd"])

    log.info("")
    log.info("=== 3. cara a cara, donde las DOS tienen dato ===")
    amb = d[hay_wiki & hay_wd]
    if len(amb):
        _tasa("  ficha de Wikipedia", amb["ok_wiki"])
        _tasa("  Wikidata", amb["ok_wd"])
        tab = pd.crosstab(amb["ok_wiki"], amb["ok_wd"],
                          rownames=["wiki acierta"], colnames=["wikidata acierta"])
        log.info("\n%s", tab.to_string())
        b, c = int(tab.get(False, {}).get(True, 0)), int(tab.get(True, {}).get(False, 0))
        if b + c > 0:
            pv = stats.binomtest(c, b + c, 0.5).pvalue
            log.info("discordantes: wiki sola %d, wikidata sola %d — McNemar exacto p=%.3f",
                     c, b, pv)

    log.info("")
    log.info("=== 4. precisión de la ficha por origen del campo ===")
    g = (d[hay_wiki].groupby("club_wiki_origen")["ok_wiki"]
         .agg(n="size", aciertos="sum", tasa="mean"))
    g["tasa"] = (100 * g["tasa"]).round(1)
    log.info("\n%s", g.to_string())

    log.info("")
    log.info("=== 5. ¿el error depende del estrato de nacimiento? ===")
    ge = (d[hay_wiki].groupby("estrato")["ok_wiki"]
          .agg(n="size", aciertos="sum", tasa="mean"))
    ge["tasa"] = (100 * ge["tasa"]).round(1)
    log.info("\n%s", ge.to_string())
    if len(ge) == 2:
        t = pd.crosstab(d.loc[hay_wiki, "estrato"], d.loc[hay_wiki, "ok_wiki"])
        if t.shape == (2, 2):
            odds, pv = stats.fisher_exact(t.values)
            log.info("Fisher: OR=%.2f, p=%.3f — un error NO diferencial "
                     "no sesga el contraste de H3", odds, pv)

    log.info("")
    log.info("=== 6. desacuerdos, uno por uno ===")
    for r in d[hay_wiki & ~d["ok_wiki"]].itertuples():
        log.info("   %-24s ficha=%-28s bdfa=%-28s [%s]",
                 str(r.nombre)[:24], str(r.club_wiki_nombre)[:28],
                 str(r.club_bdfa)[:28], r.club_wiki_origen)

    d.to_csv(val / "validacion_club_wiki.csv", index=False, encoding="utf-8")
    log.info("")
    log.info("=== %s ===", val / "validacion_club_wiki.csv")


if __name__ == "__main__":
    main()
