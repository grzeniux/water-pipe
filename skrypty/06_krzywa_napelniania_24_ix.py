"""Dopasowanie krzywej napełniania z pomiarów z 24 IX.

Model jest diagnostyczny: asymptota reprezentuje równowagę między dopływem,
ściśliwością/poduszką powietrzną i równoległym wyciekiem. Nie jest to
identyfikacja wydatku wycieku bez dodatkowego pomiaru przepływu.
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config
from core.hydraulika import at_na_bar
from core.profil import ProfilTerenowy


def minuty_od_startu(godzina: str) -> float:
    godz, minuta = (int(czesc) for czesc in godzina.split(":"))
    return (godz - 16) * 60 + minuta - 22


def dopasuj_asymptote(czas: np.ndarray, cisnienie: np.ndarray) -> tuple[float, float, float]:
    """Dopasowuje p(t)=p_inf-(p_inf-p0)*exp(-t/tau) metodą siatki tau."""
    p0 = float(cisnienie[0])
    najlepsze = (float("inf"), float(cisnienie[-1]), 60.0)
    for tau in np.linspace(1.0, 500.0, 1000):
        e = np.exp(-czas / tau)
        mianownik = 1.0 - e
        p_inf = float(np.sum(mianownik * (cisnienie - p0 * e)) / np.sum(mianownik**2))
        model = p_inf - (p_inf - p0) * e
        blad = float(np.sum((model - cisnienie) ** 2))
        if blad < najlepsze[0]:
            najlepsze = (blad, p_inf, float(tau))
    blad, p_inf, tau = najlepsze
    return p_inf, tau, blad


def main() -> None:
    pomiary = config.POMIARY_WZROSTU_24_IX
    czas = np.asarray([minuty_od_startu(pomiar["godzina"]) for pomiar in pomiary], dtype=float)
    cisnienie_at = np.asarray([pomiar["cisnienie_at"] for pomiar in pomiary], dtype=float)
    p_inf, tau, blad = dopasuj_asymptote(czas, cisnienie_at)
    profil = ProfilTerenowy()
    dom = next(p for p in config.PUNKTY_INFRASTRUKTURY if p["typ"] == "dom")
    z_lustro = profil.rzedna_rury(dom["metr"]) + 10.0 * p_inf

    czas_model = np.linspace(0.0, max(czas) + 15.0, 250)
    model_at = p_inf - (p_inf - cisnienie_at[0]) * np.exp(-czas_model / tau)
    print("\nKRZYWA NAPEŁNIANIA RUROCIĄGU - TEST 24 IX")
    print("Model: P(t) = P_inf - (P_inf - P0) * exp(-t/tau)")
    print("Interpretacja P_inf: asymptotyczna równowaga dopływu, poduszki powietrznej i wycieku.")
    print(f"{'Czas od 16:22 [min]':>20} | {'Godzina':>8} | {'Pomiar [At]':>13} | {'Pomiar [bar]':>14} | {'Model [At]':>12}")
    print("-" * 82)
    for pomiar, t, p_at in zip(pomiary, czas, cisnienie_at):
        p_model = p_inf - (p_inf - cisnienie_at[0]) * np.exp(-t / tau)
        print(f"{t:>20.0f} | {pomiar['godzina']:>8} | {p_at:>13.2f} | {at_na_bar(p_at):>14.5f} | {p_model:>12.3f}")
    print("\nPARAMETRY DOPASOWANIA")
    print(f"P0 = {cisnienie_at[0]:.3f} At = {at_na_bar(cisnienie_at[0]):.5f} bar")
    print(f"P_inf = {p_inf:.3f} At = {at_na_bar(p_inf):.5f} bar")
    print(f"tau = {tau:.2f} min; RMSE = {np.sqrt(blad / len(czas)):.4f} At")
    print(f"Lustro odpowiadające P_inf przy domu: {z_lustro:.2f} m n.p.m.")
    print("WNIOSEK: dane rosną asymptotycznie; P_inf jest parametrem dopasowania, nie bezpośrednim pomiarem wydatku wycieku.")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(czas, cisnienie_at, color="black", zorder=4, label="Pomiary 24 IX")
    ax.plot(czas_model, model_at, color="darkorange", linewidth=2.2, label=f"Dopasowanie asymptotyczne P_inf={p_inf:.2f} At")
    ax.axhline(p_inf, color="darkorange", linestyle=":", label=f"Asymptota {p_inf:.2f} At")
    ax.axvline(0.0, color="gray", linestyle="--", linewidth=0.8)
    ax.set(xlabel="Czas od 16:22 [min]", ylabel="Ciśnienie [At]", title="Napełnianie rurociągu - pomiary 24 IX")
    ax.grid(True, linestyle=":")
    ax.legend()
    katalog = ROOT / "wykresy"
    katalog.mkdir(exist_ok=True)
    plik = katalog / "06_krzywa_napelniania_24_ix.png"
    fig.savefig(plik, dpi=300, bbox_inches="tight")
    print(f"DANE WYKRESU: punkty = {len(czas)}; zakres czasu = 0-{czas[-1]:.0f} min; seria pomiarowa At = {cisnienie_at.tolist()}.")
    print(f"[OK] Wykres zapisano do: {plik}")
    plt.close(fig)


if __name__ == "__main__":
    main()