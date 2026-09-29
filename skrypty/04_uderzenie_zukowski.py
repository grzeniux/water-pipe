from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config
from core.hydraulika import predkosc_fali_zukowskiego


def main() -> None:
    fala = {s["nazwa"]: predkosc_fali_zukowskiego(s["srednica"], s["grubosc_scianki"]) for s in config.SEKCJE_RUR}
    q_values = np.array([5, 10, 15, 20, 25, 30, 40], dtype=float)
    sekcja = next(s for s in config.SEKCJE_RUR if s["srednica"] == config.D_PE20)
    pole = np.pi * sekcja["srednica"] ** 2 / 4
    predkosci = q_values / 1000 / 60 / pole
    skok = config.RO_WODY * fala[sekcja["nazwa"]] * predkosci / 1e5
    statyka_zlaczka = 4.40
    statyka_dom = 3.00
    print("\nUDERZENIE HYDRAULICZNE ŻUKOWSKIEGO")
    print("\nPRĘDKOŚĆ FALI W KAŻDEJ SEKCJI")
    print(f"{'Sekcja':<38} | {'Średnica [mm]':>14} | {'c [m/s]':>10}")
    print("-" * 70)
    for s in config.SEKCJE_RUR:
        print(f"{s['nazwa']:<38} | {s['srednica'] * 1000:>14.1f} | {fala[s['nazwa']]:>10.1f}")
    print("\nSZCZYT CIŚNIENIA NA ZŁĄCZCE 1 (BAZA 4.40 bar, RURA PE20)")
    print(f"{'Q [l/min]':>10} | {'v PE20 [m/s]':>14} | {'ΔP [bar]':>12} | {'P szczyt [bar]':>16} | Ocena PN10 / PN16")
    print("-" * 90)
    for q, v, dp in zip(q_values, predkosci, skok):
        szczyt = statyka_zlaczka + dp
        ocena = "PRZEKROCZONO PN16" if szczyt > 16 else "przekroczono PN10" if szczyt > 10 else "poniżej PN10"
        print(f"{q:>10.0f} | {v:>14.3f} | {dp:>12.2f} | {szczyt:>16.2f} | {ocena}")
    print(f"\nDla domu (baza {statyka_dom:.2f} bar) zakres szczytów wynosi: {statyka_dom + skok.min():.2f}-{statyka_dom + skok.max():.2f} bar.")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(q_values, statyka_zlaczka + skok, "o-", color="darkorange", label="Złączka 1, baza 4.40 bar")
    ax.plot(q_values, statyka_dom + skok, "s--", color="steelblue", label="Dom, baza 3.00 bar")
    ax.axhline(10, color="gray", linestyle=":", label="PN10")
    ax.axhline(16, color="firebrick", linestyle=":", label="PN16")
    ax.set(xlabel="Pobór przed zamknięciem [l/min]", ylabel="Szczytowe ciśnienie [bar]", title="Skok ciśnienia Żukowskiego")
    ax.grid(True, linestyle=":")
    ax.legend()
    Path(ROOT / "wykresy").mkdir(exist_ok=True)
    fig.savefig(ROOT / "wykresy/04_uderzenie_zukowski.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()