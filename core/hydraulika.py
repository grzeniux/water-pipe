"""Podstawowe obliczenia hydrauliczne dla rurociągu."""

from __future__ import annotations

import math

import config


def bar_na_metry(bar: float) -> float:
    return bar * config.PRZELICZNIK_M_NA_BAR


def metry_na_bar(metry: float) -> float:
    return metry / config.PRZELICZNIK_M_NA_BAR


def liczba_reynoldsa(predkosc: float, srednica: float) -> float:
    return abs(predkosc) * srednica / config.LEPKOSC_KINEMATYCZNA


def wspolczynnik_tarcia(re: float, srednica: float) -> float:
    if re <= 0:
        return 0.0
    if re < 2300:
        return 64.0 / re
    eps = config.CHROPOWATOSC_PE / srednica
    return 0.25 / math.log10(eps / 3.7 + 5.74 / re**0.9) ** 2


def strata_lokalna_darcy(q_m3s: float, dlugosc: float, srednica: float) -> float:
    pole = math.pi * srednica**2 / 4
    predkosc = q_m3s / pole
    re = liczba_reynoldsa(predkosc, srednica)
    return wspolczynnik_tarcia(re, srednica) * dlugosc / srednica * predkosc**2 / (2 * config.G)


def predkosc_fali_zukowskiego(srednica: float, grubosc_scianki: float) -> float:
    k = config.MODUL_SCISLIWOSCI_WODY
    return math.sqrt((k / config.RO_WODY) / (1 + (k / config.MODUL_YOUNGA_DYN) * (srednica / grubosc_scianki)))


def srednica_dla_metra(metr: float) -> float:
    for sekcja in config.SEKCJE_RUR:
        if sekcja["od_metra"] <= metr <= sekcja["do_metra"]:
            return sekcja["srednica"]
    raise ValueError(f"Kilometraż poza rurociągiem: {metr}")

def pobierz_srednice_wewn(m_pozycja):
    """Zwraca średnicę wewnętrzną rury [m] dla danego kilometraża z config.SEKCJE_RUR."""
    for sekcja in config.SEKCJE_RUR:
        if sekcja['od_metra'] <= m_pozycja <= sekcja['do_metra']:
            return sekcja['srednica']
    return config.D_PE32