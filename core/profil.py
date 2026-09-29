"""Wczytywanie profilu Geoportalu i interpolacja rzędnej rury."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

import config


class ProfilTerenowy:
    def __init__(self, sciezka: str | Path = config.PLIK_PROFILU) -> None:
        path = Path(sciezka)
        if not path.is_absolute():
            path = config.KATALOG_PROJEKTU / path
        self.sciezka = path.resolve()
        self.metry, self.rzedne_terenu = self._wczytaj()
        self.rzedne_rury = self.rzedne_terenu - config.GLEBOKOSC_RURY

    def _wczytaj(self) -> tuple[np.ndarray, np.ndarray]:
        punkty: list[tuple[float, float, float]] = []
        liczby = re.compile(r"[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?")
        with self.sciezka.open(encoding="utf-8-sig") as plik:
            for linia in plik:
                wartosci = [float(x.replace(",", ".")) for x in liczby.findall(linia)]
                if len(wartosci) >= 3 and "x" not in linia.lower():
                    punkty.append(tuple(wartosci[:3]))
        if len(punkty) < 2:
            raise ValueError(f"Nie znaleziono co najmniej dwóch punktów profilu: {self.sciezka}")

        metry = [0.0]
        for poprzedni, punkt in zip(punkty, punkty[1:]):
            dx, dy = punkt[0] - poprzedni[0], punkt[1] - poprzedni[1]
            metry.append(metry[-1] + float(np.hypot(dx, dy)))
        metry_np = np.asarray(metry)
        rzedne = np.asarray([p[2] for p in punkty])
        unikalne, indeksy = np.unique(metry_np, return_index=True)
        maksymalny_metr = max(punkt["metr"] for punkt in config.PUNKTY_INFRASTRUKTURY)
        maska = unikalne <= maksymalny_metr
        unikalne, indeksy = unikalne[maska], indeksy[maska]
        return unikalne, rzedne[indeksy]

    def rzedna_rury(self, metr: float) -> float:
        return float(np.interp(metr, self.metry, self.rzedne_rury))

    def znajdz_metry_dla_rzednej(self, rzedna_cel: float, zakres_od: float, zakres_do: float) -> list[float]:
        maska = (self.metry >= zakres_od) & (self.metry <= zakres_do)
        metry, rzedne = self.metry[maska], self.rzedne_rury[maska]
        wyniki: list[float] = []
        for m1, m2, z1, z2 in zip(metry[:-1], metry[1:], rzedne[:-1], rzedne[1:]):
            if (z1 - rzedna_cel) * (z2 - rzedna_cel) <= 0 and z1 != z2:
                wyniki.append(float(m1 + (rzedna_cel - z1) * (m2 - m1) / (z2 - z1)))
        return wyniki