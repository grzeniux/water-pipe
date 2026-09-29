from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config
from core.hydraulika import at_na_bar


def main() -> None:
    pomiar = config.POMIAR_TEST_SZCZELNOSCI
    start_at = pomiar["cisnienie_poczatkowe_at"]
    koniec_at = pomiar["cisnienie_ustabilizowane_at"]
    czas = pomiar["czas_spadku_min"]
    chwile = np.arange(0, czas, 5.0)
    chwile = np.append(chwile, czas)
    ubytek = np.maximum(1 - chwile / czas, 0) ** 2
    cisnienie_at = koniec_at + (start_at - koniec_at) * ubytek
    cisnienie_bar = np.asarray([at_na_bar(value) for value in cisnienie_at])
    print(f"\nREKONSTRUKCJA TESTU {pomiar['data']}: PRAWO TORRICELLEGO")
    print(f"Warunki: studzienka zamknięta, dom bez rozbioru, czas {czas:.0f} min")
    print(f"{'Czas [min]':>12} | {'Ciśnienie [At]':>17} | {'Ciśnienie [bar]':>17} | {'Spadek [At]':>13}")
    print("-" * 60)
    for t, p_at, p_bar in zip(chwile, cisnienie_at, cisnienie_bar):
        print(f"{t:>12.0f} | {p_at:>17.3f} | {p_bar:>17.5f} | {start_at - p_at:>13.3f}")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(chwile, cisnienie_at, "o-", color="crimson", label="Model [At]")
    ax2 = ax.twinx()
    ax2.plot(chwile, cisnienie_bar, "s--", color="steelblue", label="Model [bar]")
    ax.set(xlabel="Czas [min]", ylabel="Ciśnienie [At]", title="Nieliniowy spadek ciśnienia: test 22 IX")
    ax2.set_ylabel("Ciśnienie [bar]")
    ax.grid(True, linestyle=":")
    Path(ROOT / "wykresy").mkdir(exist_ok=True)
    plik_wykresu = ROOT / "wykresy/03_rekonstrukcja_testu.png"
    fig.savefig(plik_wykresu, dpi=300, bbox_inches="tight")
    print(f"DANE WYKRESU: {len(chwile)} punktów; At od {cisnienie_at[0]:.3f} do {cisnienie_at[-1]:.3f}; bar od {cisnienie_bar[0]:.5f} do {cisnienie_bar[-1]:.5f}.")
    print(f"WNIOSEK: spadek wynosi {start_at - koniec_at:.3f} At = {at_na_bar(start_at - koniec_at):.5f} bar w czasie {czas:.0f} min.")
    print(f"[OK] Wykres zapisano do: {plik_wykresu}")
    plt.close(fig)


if __name__ == "__main__":
    main()