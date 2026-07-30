"""Plantilla visual única del proyecto: paleta, tipografía y cromo de las figuras.

Una sola paleta y una sola plantilla para todo, como pide el diseño. Las
figuras son para papel (vectorial), así que no hay modo oscuro ni interacción:
la accesibilidad se resuelve con etiquetas directas, escalas rotuladas y las
tablas de `outputs/tables/` como versión textual de cada figura.

Reglas de color que se respetan en todas las figuras:
  · magnitud continua  -> UNA sola rampa azul, claro→oscuro (nunca arcoíris)
  · polaridad (obs/esp) -> azul↔rojo con gris neutro en el punto de quiebre
  · serie única         -> el azul de la primera ranura categórica
  · el texto va con tinta, nunca con el color de la serie
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

# --- cromo ------------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# --- categóricos (orden fijo, nunca ciclado) --------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
PRIMARY = SERIES[0]
ACCENT = SERIES[1]

# --- secuencial: una sola rampa azul ----------------------------------------
BLUE_STEPS = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
              "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
              "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("azul_seq", BLUE_STEPS)

# --- divergente: azul ↔ rojo con gris neutro --------------------------------
DIV = LinearSegmentedColormap.from_list(
    "azul_rojo", ["#104281", "#3987e5", "#9ec5f4", "#f0efec",
                  "#f2a6a5", "#e34948", "#a02423"])

SIN_DATO = "#f0efec"


def apply_style(cfg: dict) -> None:
    """Fija los rcParams para figuras de paper."""
    v = cfg["viz"]
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": v["base_font_size"],
        "axes.titlesize": v["base_font_size"] + 1,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.labelcolor": INK_2,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.6,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "grid.linestyle": "-",          # nunca punteada: la línea de puntos lee como umbral
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": v["dpi"],
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,             # texto seleccionable en el PDF
        "svg.fonttype": "none",
    })


def despine(ax, left: bool = False, bottom: bool = False) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if left:
        ax.spines["left"].set_visible(False)
    if bottom:
        ax.spines["bottom"].set_visible(False)


def titulo_y_bajada(ax, titulo: str, bajada: str = "", pad: float = 6.0) -> None:
    """Título y bajada sin pisarse.

    matplotlib mide el `pad` del título en puntos y la bajada en fracción de
    ejes: si se fijan por separado terminan superpuestos según el tamaño de la
    figura. Acá se reserva primero el lugar de la bajada y el título se empuja
    por encima.
    """
    alto_linea = mpl.rcParams["font.size"] * 1.6
    ax.set_title(titulo, loc="left", pad=(alto_linea + pad) if bajada else pad)
    if bajada:
        ax.text(0, 1.0, bajada, transform=ax.transAxes, ha="left", va="bottom",
                fontsize=mpl.rcParams["font.size"] - 0.5, color=INK_2)


def fuente(ax, texto: str) -> None:
    """Pie de figura con la fuente y el n. Toda figura lo lleva."""
    ax.figure.text(0.005, -0.02, texto, ha="left", va="top",
                   fontsize=mpl.rcParams["font.size"] - 1.5, color=MUTED)


def guardar(fig, nombre: str, cfg: dict, carpeta: Path) -> list[Path]:
    """Exporta en todos los formatos configurados. Vectorial primero."""
    carpeta.mkdir(parents=True, exist_ok=True)
    salidas = []
    for fmt in cfg["viz"]["formats"]:
        destino = carpeta / f"{nombre}.{fmt}"
        fig.savefig(destino, format=fmt)
        salidas.append(destino)
    plt.close(fig)
    return salidas


def norma_divergente(valores, centro: float = 1.0) -> TwoSlopeNorm:
    """Escala divergente centrada donde observado = esperado."""
    lo, hi = float(min(valores)), float(max(valores))
    return TwoSlopeNorm(vmin=min(lo, centro - 1e-6), vcenter=centro,
                        vmax=max(hi, centro + 1e-6))
