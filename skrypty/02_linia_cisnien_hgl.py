from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config
from core.hydraulika import metry_na_bar, strata_lokalna_darcy
from core.profil import ProfilTerenowy


def hgl_dla_q(profil: ProfilTerenowy, q_lmin: float) -> np.ndarray:
    zbiornik = profil.rzedna_rury(0.0)
    hgl = [zbiornik]
    q = q_lmin / 1000 / 60
    for m1, m2 in zip(profil.metry[:-1], profil.metry[1:]):
        strata = strata_lokalna_darcy(q, m2 - m1, next(s["srednica"] for s in config.SEKCJE_RUR if s["od_metra"] <= m1 <= s["do_metra"]))
        hgl.append(hgl[-1] - strata)
    return np.asarray(hgl)


def main() -> None:
    profil = ProfilTerenowy()
    print("\nLINIA CIŚNIEŃ HGL I STREFY PODCIŚNIENIA")
    print(f"{'Q [l/min]':>10} | {'P Złączka 2 [bar]':>18} | {'P Złączka 3 [bar]':>18} | {'P dom [bar]':>12} | Strefa")
    print("-" * 86)
    wyniki: list[tuple[float, np.ndarray, list[float], str]] = []
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(profil.metry, profil.rzedne_rury, "k", label="Oś rury")
    for q in [0, 10, 20, 25, 30]:
        hgl = np.full_like(profil.metry, profil.rzedna_rury(0.0)) if q == 0 else hgl_dla_q(profil, q)
        cisnienia = [metry_na_bar(float(np.interp(m, profil.metry, hgl) - profil.rzedna_rury(m))) for m in (401.0, 425.87, 601.0)]
        podcisnienie = np.asarray(hgl) < profil.rzedne_rury
        strefa = "TAK: podciśnienie" if podcisnienie.any() else "brak"
        print(f"{q:>10.0f} | {cisnienia[0]:>18.2f} | {cisnienia[1]:>18.2f} | {cisnienia[2]:>12.2f} | {strefa}")
        wyniki.append((q, hgl, cisnienia, strefa))
        ax.plot(profil.metry, hgl, label=f"HGL Q={q} l/min")
        if podcisnienie.any():
            ax.fill_between(profil.metry, hgl, profil.rzedne_rury, where=podcisnienie, color="red", alpha=0.15)
    ax.set(xlabel="Kilometraż [m]", ylabel="Rzędna [m n.p.m.]", title="Linia ciśnień HGL")
    ax.grid(True, linestyle=":")
    ax.legend(fontsize=8)
    Path(ROOT / "wykresy").mkdir(exist_ok=True)
    plik_wykresu = ROOT / "wykresy/02_linia_hgl.png"
    fig.savefig(plik_wykresu, dpi=300, bbox_inches="tight")
    print("\nDANE WYKRESU HGL")
    print(f"Liczba punktów profilu: {len(profil.metry)}; serie Q: {[int(w[0]) for w in wyniki]} l/min")
    for q, hgl, _, strefa in wyniki:
        roznica = hgl - profil.rzedne_rury
        indeks_min = int(np.argmin(roznica))
        print(f"Q={q:.0f} l/min: HGL start={hgl[0]:.2f}, HGL koniec={hgl[-1]:.2f} m n.p.m.; min. ciśnienie={metry_na_bar(roznica[indeks_min]):.2f} bar na km {profil.metry[indeks_min]:.2f}; {strefa}")
    print(f"WNIOSEK: strefa podciśnienia występuje dla Q={next((q for q, _, _, s in wyniki if s.startswith('TAK')), 'żadnego')} l/min lub większego w badanym zakresie.")
    print(f"[OK] Wykres zapisano do: {plik_wykresu}")
    plt.close(fig)


if __name__ == "__main__":
    main()