from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config


def main() -> None:
    start = config.POMIAR_TEST_SZCZELNOSCI["cisnienie_poczatkowe_bar"]
    koniec = config.POMIAR_TEST_SZCZELNOSCI["cisnienie_ustabilizowane_bar"]
    czas = config.POMIAR_TEST_SZCZELNOSCI["czas_spadku_min"]
    chwile = np.arange(0, czas + 1, 15.0)
    ubytek = np.maximum(1 - chwile / czas, 0) ** 2
    cisnienie = koniec + (start - koniec) * ubytek
    print("\nREKONSTRUKCJA TESTU MANOMETRU: PRAWO TORRICELLEGO")
    print(f"{'Czas [min]':>12} | {'Ciśnienie [bar]':>17} | {'Spadek od startu [bar]':>23}")
    print("-" * 60)
    for t, p in zip(chwile, cisnienie):
        print(f"{t:>12.0f} | {p:>17.3f} | {start - p:>23.3f}")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(chwile, cisnienie, "o-", color="crimson")
    ax.set(xlabel="Czas [min]", ylabel="Ciśnienie [bar]", title="Nieliniowy spadek ciśnienia w teście 105 min")
    ax.grid(True, linestyle=":")
    Path(ROOT / "wykresy").mkdir(exist_ok=True)
    plik_wykresu = ROOT / "wykresy/03_rekonstrukcja_testu.png"
    fig.savefig(plik_wykresu, dpi=300, bbox_inches="tight")
    print(f"DANE WYKRESU: seria ciśnienia zawiera {len(chwile)} punktów od {cisnienie[0]:.3f} do {cisnienie[-1]:.3f} bar.")
    print(f"WNIOSEK: spadek wynosi {start - koniec:.3f} bar w czasie {czas:.0f} min; model kończy się na {koniec:.3f} bar.")
    print(f"[OK] Wykres zapisano do: {plik_wykresu}")
    plt.close(fig)


if __name__ == "__main__":
    main()