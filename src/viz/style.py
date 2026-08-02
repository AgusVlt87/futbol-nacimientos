"""Plantilla visual del proyecto: paleta, tipografía y un layout que no se pisa.

## Por qué hay una clase de layout y no `plt.subplots` a secas

Los títulos se superponían con los gráficos, y la causa es concreta:
`ax.set_title(pad=...)` mide en puntos, `ax.text(y=1.02, transform=ax.transAxes)`
mide en fracción de ejes, y `savefig(bbox_inches="tight")` recorta después de
todo eso. Tres sistemas de coordenadas distintos decidiendo el mismo espacio:
el resultado depende del tamaño de la figura y de si el eje es un mapa con
`aspect="equal"`, donde la caja del eje no coincide con lo dibujado.

`Figura` resuelve eso reservando bandas fijas en coordenadas de FIGURA —
encabezado arriba, pie abajo, área de dibujo en el medio— y guardando **sin**
`bbox_inches="tight"`, para que el espacio reservado sea exactamente el que se
respeta. El texto nunca compite con el gráfico por el mismo lugar.

## Reglas de color

  · magnitud continua   → UNA rampa azul, claro→oscuro (nunca arcoíris)
  · polaridad           → azul↔rojo con gris neutro en el punto de quiebre
  · serie única         → el azul de la primera ranura categórica
  · el texto va con tinta, nunca con el color de la serie
"""

from __future__ import annotations

import textwrap
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
PRIMARY, ACCENT = SERIES[0], SERIES[1]

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

# Tamaños en puntos.
PT_TITULO = 11.5
PT_BAJADA = 8.5
PT_PIE = 6.8
PT_BASE = 9.0


def apply_style(cfg: dict | None = None) -> None:
    dpi_guardado = (cfg or {}).get("viz", {}).get("dpi", 300)
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": PT_BASE,
        "axes.labelcolor": INK_2,
        "axes.labelsize": PT_BASE - 0.5,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.6,
        "axes.grid": False,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "grid.linestyle": "-",       # nunca punteada: lee como umbral
        "xtick.color": AXIS,
        "ytick.color": AXIS,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "xtick.labelsize": PT_BASE - 1,
        "ytick.labelsize": PT_BASE - 1,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": dpi_guardado,
        "pdf.fonttype": 42,          # texto seleccionable en el PDF
        "svg.fonttype": "none",
    })


# --------------------------------------------------------------------------- #
class Figura:
    """Figura con bandas reservadas para título, bajada y pie.

    El área de dibujo se calcula restando esas bandas: nada puede invadirla y
    nada puede invadir el texto. Todo en coordenadas de figura.
    """

    MARGEN_IZQ = 0.055
    MARGEN_DER = 0.030
    MARGEN_SUP = 0.030
    MARGEN_INF = 0.028
    ESPACIO_TRAS_ENCABEZADO = 0.030
    ESPACIO_ANTES_DEL_PIE = 0.024

    def __init__(self, ancho: float, alto: float, titulo: str, bajada: str = "",
                 pie: str = "", cfg: dict | None = None):
        self.cfg = cfg or {}
        self.fig = plt.figure(figsize=(ancho, alto))
        self.ancho, self.alto = ancho, alto

        pts_por_fraccion = 72.0 * alto
        alto_titulo = PT_TITULO * 1.35 / pts_por_fraccion if titulo else 0.0
        lineas_bajada = bajada.count("\n") + 1 if bajada else 0
        alto_bajada = PT_BAJADA * 1.45 * lineas_bajada / pts_por_fraccion

        self.pie_lineas = self._envolver(pie) if pie else []
        alto_pie = PT_PIE * 1.5 * len(self.pie_lineas) / pts_por_fraccion

        y = 1 - self.MARGEN_SUP
        if titulo:
            y -= alto_titulo
            self.fig.text(self.MARGEN_IZQ, y, titulo, ha="left", va="baseline",
                          fontsize=PT_TITULO, fontweight="bold", color=INK)
        if bajada:
            y -= alto_bajada
            self.fig.text(self.MARGEN_IZQ, y, bajada, ha="left", va="baseline",
                          fontsize=PT_BAJADA, color=INK_2, linespacing=1.45)

        self.tope = y - self.ESPACIO_TRAS_ENCABEZADO
        self.piso = self.MARGEN_INF + alto_pie + \
            (self.ESPACIO_ANTES_DEL_PIE if self.pie_lineas else 0.0)

        if self.pie_lineas:
            self.fig.text(self.MARGEN_IZQ, self.MARGEN_INF, "\n".join(self.pie_lineas),
                          ha="left", va="bottom", fontsize=PT_PIE, color=MUTED,
                          linespacing=1.5)

    def _envolver(self, texto: str) -> list[str]:
        """Envuelve el pie al ancho que realmente entra en la figura.

        El ancho medio de un carácter en una sans es ~0,5 em, así que a `PT_PIE`
        puntos entran `ancho_en_puntos / (PT_PIE * 0,5)` caracteres por línea.
        La estimación anterior daba un tercio de eso y el pie se comía media
        figura.
        """
        ancho_pt = self.ancho * 72 * (1 - self.MARGEN_IZQ - self.MARGEN_DER)
        caracteres = max(60, int(ancho_pt / (PT_PIE * 0.5)))
        lineas: list[str] = []
        for parrafo in texto.split("\n"):
            lineas.extend(textwrap.wrap(parrafo, caracteres) or [""])
        return lineas

    def eje(self, izq: float = 0.0, der: float = 0.0,
            arriba: float = 0.0, abajo: float = 0.0) -> plt.Axes:
        """Eje que ocupa el área disponible, con recortes opcionales en fracción."""
        x0 = self.MARGEN_IZQ + izq
        x1 = 1 - self.MARGEN_DER - der
        y0 = self.piso + abajo
        y1 = self.tope - arriba
        return self.fig.add_axes([x0, y0, x1 - x0, y1 - y0])

    def ejes_lado_a_lado(self, n: int = 2, separacion: float = 0.03,
                         sangria_izq: float = 0.0, abajo: float = 0.0,
                         arriba: float = 0.0,
                         titulos: list[str] | None = None) -> list[plt.Axes]:
        """Paneles lado a lado.

        `sangria_izq` reserva lugar para los rótulos del eje y, que se dibujan
        POR FUERA de la caja del eje y si no quedarían cortados contra el borde.

        `titulos` dibuja el título de cada panel **en coordenadas de figura**,
        reservando su banda. Usar `ax.set_title` acá era justamente lo que hacía
        que el título del panel se montara sobre la bajada de la figura: vive en
        coordenadas de ejes y no sabe nada del encabezado.
        """
        x0 = self.MARGEN_IZQ + sangria_izq
        total = 1 - self.MARGEN_IZQ - self.MARGEN_DER - sangria_izq
        ancho = (total - separacion * (n - 1)) / n
        y0, y1 = self.piso + abajo, self.tope - arriba

        if titulos:
            alto_t = PT_BAJADA * 1.9 / (72.0 * self.alto)
            y1 -= alto_t
            for i, texto in enumerate(titulos[:n]):
                self.fig.text(x0 + i * (ancho + separacion) - sangria_izq,
                              y1 + alto_t * 0.35, texto, ha="left", va="baseline",
                              fontsize=PT_BAJADA, color=INK_2, fontweight="bold")

        return [self.fig.add_axes([x0 + i * (ancho + separacion), y0, ancho, y1 - y0])
                for i in range(n)]

    def banda_leyenda(self, alto_pt: float = 24.0) -> plt.Axes:
        """Reserva una franja propia para la leyenda, arriba del área de dibujo.

        Una leyenda dibujada *dentro* del eje compite con los datos por el mismo
        espacio, y en un mapa no hay forma de saber de antemano dónde va a haber
        lugar: en el mapa de flujos las curvas que salen de la Patagonia le
        pasaban por encima al recuadro. Acá la leyenda tiene su propia banda y el
        gráfico arranca abajo de ella, con la misma lógica de bandas reservadas
        que el título y el pie.

        Devuelve un eje invisible; hay que llamarla **antes** de `eje()`.
        """
        alto = alto_pt / (72.0 * self.alto)
        ax = self.fig.add_axes([self.MARGEN_IZQ, self.tope - alto,
                                1 - self.MARGEN_IZQ - self.MARGEN_DER, alto])
        ax.set_axis_off()
        self.tope -= alto + 0.008
        return ax

    def nota(self, ax, texto: str, x: float, y: float, **kw) -> None:
        kw.setdefault("fontsize", PT_BASE - 1.5)
        kw.setdefault("color", INK_2)
        ax.text(x, y, texto, transform=ax.transAxes, **kw)

    def guardar(self, nombre: str, carpeta: Path) -> list[Path]:
        """Exporta en todos los formatos. **Sin `bbox_inches='tight'`**: el
        recorte automático es justamente lo que rompía el espacio reservado."""
        carpeta.mkdir(parents=True, exist_ok=True)
        formatos = self.cfg.get("viz", {}).get("formats", ["pdf", "svg", "png"])
        salidas = []
        for fmt in formatos:
            destino = carpeta / f"{nombre}.{fmt}"
            self.fig.savefig(destino, format=fmt)
            salidas.append(destino)
        plt.close(self.fig)
        return salidas


# --------------------------------------------------------------------------- #
def despine(ax, izquierda: bool = False, abajo: bool = False) -> None:
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    if izquierda:
        ax.spines["left"].set_visible(False)
    if abajo:
        ax.spines["bottom"].set_visible(False)


def norma_divergente(valores, centro: float = 1.0) -> TwoSlopeNorm:
    lo, hi = float(min(valores)), float(max(valores))
    return TwoSlopeNorm(vmin=min(lo, centro - 1e-6), vcenter=centro,
                        vmax=max(hi, centro + 1e-6))


def miles(n: float) -> str:
    """Formato argentino: punto para los miles."""
    return f"{n:,.0f}".replace(",", ".")
