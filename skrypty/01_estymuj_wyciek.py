from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config
from core.profil import ProfilTerenowy
from core.hydraulika import bar_na_metry


def znajdz_przeciecia(profil: ProfilTerenowy, rzedna_cel: float) -> list[float]:
    """Zwraca kilometraże przecięć poziomu z liniowo interpolowanym profilem."""
    roznica = profil.rzedne_rury - rzedna_cel
    przeciecia: list[float] = []
    for m1, m2, z1, z2, d1, d2 in zip(
        profil.metry[:-1], profil.metry[1:], profil.rzedne_rury[:-1], profil.rzedne_rury[1:], roznica[:-1], roznica[1:]
    ):
        if d1 == 0:
            przeciecia.append(float(m1))
        elif d1 * d2 < 0 and z1 != z2:
            metr = m1 + (rzedna_cel - z1) * (m2 - m1) / (z2 - z1)
            przeciecia.append(float(metr))
    if roznica[-1] == 0:
        przeciecia.append(float(profil.metry[-1]))
    return sorted(set(round(metr, 6) for metr in przeciecia))


def sekcja_dla_metra(metr: float) -> str:
    for sekcja in config.SEKCJE_RUR:
        if sekcja["od_metra"] <= metr <= sekcja["do_metra"]:
            return sekcja["nazwa"]
    return "poza zdefiniowanymi sekcjami"


def main() -> None:
    profil = ProfilTerenowy()
    dom = next(p for p in config.PUNKTY_INFRASTRUKTURY if p["typ"] == "dom")
    poziom = profil.rzedna_rury(dom["metr"]) + bar_na_metry(config.POMIAR_TEST_SZCZELNOSCI["cisnienie_ustabilizowane_bar"])
    miejsca = znajdz_przeciecia(profil, poziom)
    print("\nESTYMACJA MIEJSCA NIESZCZELNOŚCI")
    print(f"Poziom rury w domu: {profil.rzedna_rury(dom['metr']):.2f} m n.p.m.")
    print(f"Rzędna odpowiadająca 1.60 bar: {poziom:.2f} m n.p.m.")
    print("\nRZĘDNE PUNKTÓW INFRASTRUKTURY")
    print(f"{'Punkt':<45} | {'Kilometraż':>10} | {'Rzędna rury':>14}")
    print("-" * 78)
    for punkt in config.PUNKTY_INFRASTRUKTURY:
        print(f"{punkt['nazwa']:<45} | {punkt['metr']:>10.2f} m | {profil.rzedna_rury(punkt['metr']):>11.2f} m n.p.m.")
    print("\nPRZECIĘCIA POZIOMU CIŚNIENIA")
    print(f"{'Kilometraż':>12} | {'Od Złączki 1':>15} | {'Od domu':>12} | Sekcja")
    print("-" * 86)
    if miejsca:
        for metr in miejsca:
            print(f"{metr:>10.2f} m | {metr - 309.46:>12.2f} m | {601.0 - metr:>9.2f} m | {sekcja_dla_metra(metr)}")
        print(f"WNIOSEK: poziom 1.60 bar przecina profil {len(miejsca)} raz(y); główny punkt: km {miejsca[0]:.2f}.")
    else:
        print("Brak przecięcia poziomu z profilem w zakresie 0.0-601.0 m.")

    x = np.linspace(0.0, 601.0, 800)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(x, [profil.rzedna_rury(v) for v in x], label="Oś rury")
    ax.axhline(poziom, color="crimson", linestyle="--", label="Poziom 1.60 bar")
    if miejsca:
        ax.scatter(miejsca, [poziom] * len(miejsca), color="red", zorder=5, label="Wyestymowany punkt")
    for punkt in config.PUNKTY_INFRASTRUKTURY:
        if punkt["typ"] == "zlaczka":
            ax.axvline(punkt["metr"], color="gray", linestyle=":")
    ax.set(xlabel="Kilometraż [m]", ylabel="Rzędna [m n.p.m.]", title="Estymacja poziomu odpowiadającego 1.60 bar")
    ax.grid(True, linestyle=":")
    ax.legend()
    Path(ROOT / "wykresy").mkdir(exist_ok=True)
    plik_wykresu = ROOT / "wykresy/01_estymacja_wycieku.png"
    fig.savefig(plik_wykresu, dpi=300, bbox_inches="tight")
    print(f"DANE WYKRESU: profil rury = {len(x)} punktów; poziom celu = {poziom:.3f} m n.p.m.; zaznaczone przecięcia = {miejsca or 'brak'}")
    print(f"[OK] Wykres zapisano do: {plik_wykresu}")
    plt.close(fig)


if __name__ == "__main__":
    main()