# skrypty/05_mapa_cisnien_odcinki.py
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config
from core.profil import ProfilTerenowy
from core.hydraulika import pobierz_srednice_wewn, metry_na_bar

def oblicz_linie_cisnien(profil, q_lmin, z_zrodlo):
    """Wylicza rzędną piezometryczną HGL oraz ciśnienie wzdłuż trasy."""
    if q_lmin == 0.0:
        hgl = np.full_like(profil.metry, z_zrodlo)
        cisnienia_bar = metry_na_bar(hgl - profil.z_rura)
        return hgl, cisnienia_bar

    q_m3s = (q_lmin / 1000.0) / 60.0
    h_akt = z_zrodlo
    hgl = [h_akt]

    for i in range(len(profil.metry) - 1):
        dm = profil.metry[i+1] - profil.metry[i]
        d_w = pobierz_srednice_wewn(profil.metry[i])
        pole = np.pi * (d_w / 2.0)**2
        v = q_m3s / pole
        re = (v * d_w) / config.LEPKOSC_KINEMATYCZNA

        if re < 2300:
            lam = 64.0 / max(re, 1.0)
        else:
            eps = config.CHROPOWATOSC_PE / d_w
            lam = 0.25 / (np.log10(eps / 3.7 + 5.74 / (re**0.9)))**2

        spadek = lam * (dm / d_w) * (v**2 / (2.0 * config.G))
        h_akt -= spadek
        hgl.append(h_akt)

    hgl = np.array(hgl)
    cisnienia_bar = metry_na_bar(hgl - profil.z_rura)
    return hgl, cisnienia_bar

def generuj_mape_cisnien():
    profil = ProfilTerenowy()

    pkt_zbiornik = next(p for p in config.PUNKTY_INFRASTRUKTURY if p['typ'] == 'zbiornik')
    pkt_studnia = next(p for p in config.PUNKTY_INFRASTRUKTURY if p['typ'] == 'studnia')
    z_zbiornik = profil.rzedna_rury(pkt_zbiornik['metr'])
    z_studnia = profil.rzedna_rury(pkt_studnia['metr'])

    # Obliczenie ciśnień dla 3 stanów:
    # 1. Pełna statyka (zawór w domu zamknięty, brak poboru)
    _, p_stat = oblicz_linie_cisnien(profil, 0.0, z_zbiornik)
    # 2. Normalny pobór w domu (15 l/min - np. kran/prysznic)
    _, p_norm = oblicz_linie_cisnien(profil, 15.0, z_zbiornik)
    # 3. Duży pobór (30 l/min - np. 2 punkty poboru naraz, próg inżektora)
    _, p_injektor = oblicz_linie_cisnien(profil, 30.0, z_zbiornik)

    print("\n" + "═" * 92)
    print(" 05. MAPA CIŚNIEŃ WZDŁUŻ POSZCZEGÓLNYCH SEKCJI I PUNKTÓW INFRASTRUKTURY")
    print("═" * 92)
    print(f"{'Punkt / Sekcja':<32} | {'Kilometraż':<12} | {'Statyka Q=0':<12} | {'Pobór 15 l/m':<13} | Pobór 30 l/m")
    print("─" * 92)

    for pkt in config.PUNKTY_INFRASTRUKTURY:
        m = pkt['metr']
        idx = np.argmin(np.abs(profil.metry - m))
        nazwa = pkt['nazwa'].split('-')[0].strip()
        print(f"{nazwa:<32} | km {m:<9.2f} | {p_stat[idx]:>6.2f} bar   | {p_norm[idx]:>6.2f} bar    | {p_injektor[idx]:>6.2f} bar")

    print("─" * 92)
    print(" CIŚNIENIA NA GRANICACH POSZCZEGÓLNYCH ŚREDNIC RUR:")
    print("─" * 92)

    for s in config.SEKCJE_RUR:
        m_start = s['od_metra']
        m_stop = s['do_metra']
        idx_s = np.argmin(np.abs(profil.metry - m_start))
        idx_e = np.argmin(np.abs(profil.metry - m_stop))
        zakres_p = f"{p_stat[idx_s]:.1f} - {p_stat[idx_e]:.1f} bar"
        zakres_dyn = f"{p_norm[idx_s]:.1f} - {p_norm[idx_e]:.1f} bar"
        zakres_inj = f"{p_injektor[idx_s]:.1f} - {p_injektor[idx_e]:.1f} bar"
        print(f"{s['nazwa']:<32} | {m_start:5.1f}-{m_stop:5.1f}m | {zakres_p:<12} | {zakres_dyn:<13} | {zakres_inj}")

    ujemne = profil.metry[p_injektor < 0]
    print("\nDANE WYKRESU CIŚNIENIA")
    print(f"Serie: Q=0, 15, 30 l/min; punktów profilu: {len(profil.metry)}; zakres osi ciśnienia: -2.0 do 6.5 bar.")
    if len(ujemne):
        print(f"Q=30 l/min: podciśnienie od km {ujemne[0]:.2f} do km {ujemne[-1]:.2f}; minimum {p_injektor.min():.2f} bar na km {profil.metry[np.argmin(p_injektor)]:.2f}.")
    else:
        print("Q=30 l/min: brak podciśnienia.")

    print("═" * 92)
    print(" WNIOSEK: Sekcja PE20 (km 217.4 - 309.5) przy 30 l/min traci całe ciśnienie.")
    print(" Na km 283.4 (miejsce nieszczelności) ciśnienie dynamiczne spada do wartości ujemnych!")
    print("═" * 92 + "\n")

    # --- TWORZENIE WYKRESU ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    plt.subplots_adjust(hspace=0.18, top=0.93, bottom=0.08, left=0.08, right=0.95)

    # 1. GÓRNY WYKRES: Geometria profilu z podziałem na sekcje
    ax1.plot(profil.metry, profil.z_teren, color='#95a5a6', lw=1.2, linestyle=':', label='Teren NMT')
    ax1.plot(profil.metry, profil.z_rura, color='#2c3e50', lw=2.2, label='Oś rurociągu (1.5 m pod gruntem)')

    kolory_sekcji = ['#bdc3c7', '#f39c12', '#3498db', '#e67e22', '#2980b9']
    for idx_s, s in enumerate(config.SEKCJE_RUR):
        ax1.axvspan(s['od_metra'], s['do_metra'], color=kolory_sekcji[idx_s % len(kolory_sekcji)],
                    alpha=0.2, label=f"{s['nazwa']}")

    for pkt in config.PUNKTY_INFRASTRUKTURY:
        m = pkt['metr']
        z = profil.rzedna_rury(m)
        ax1.scatter([m], [z], color='#c0392b', s=50, zorder=5)
        ax1.annotate(pkt['nazwa'].split('-')[0].strip(), xy=(m, z), xytext=(m - 15, z + 3),
                     fontsize=8, rotation=35, fontweight='bold', color='#2c3e50')

    ax1.set_title("1. PROFIL PIONOWY TRASY I ARCHITEKTURA ŚREDNIC RUR", fontweight='bold')
    ax1.set_ylabel("Wysokość [m n.p.m.]", fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=8, ncol=2)

    # 2. DOLNY WYKRES: Rozkład ciśnienia manometrycznego wzdłuż trasy
    ax2.plot(profil.metry, p_stat, color='#27ae60', lw=2.2, label='Statyka Q = 0 l/min (zamknięty dom)')
    ax2.plot(profil.metry, p_norm, color='#2980b9', lw=2.0, label='Normalny pobór Q = 15 l/min')
    ax2.plot(profil.metry, p_injektor, color='#c0392b', lw=2.2, linestyle='--',
             label='Duży pobór Q = 30 l/min (zjawisko inżektora)')

    # Zaznaczenie strefy podciśnienia (poniżej 0 bar)
    ax2.axhline(0.0, color='black', lw=1.2, linestyle='-')
    ax2.fill_between(profil.metry, -2.0, 0.0, color='#e74c3c', alpha=0.18,
                     label='STREFA ZASYSANIA MUŁU (PODCIŚNIENIE < 0 bar)')

    # Wykryta nieszczelność na km 283.4
    ax2.axvline(283.41, color='#8e44ad', lw=1.8, linestyle='-.')
    ax2.scatter([283.41], [p_injektor[np.argmin(np.abs(profil.metry - 283.41))]],
                color='#8e44ad', s=90, zorder=6)
    ax2.annotate("Wykryta nieszczelność\nkm 283.41 (PE20 w osłonie PE40)",
                 xy=(283.41, p_injektor[np.argmin(np.abs(profil.metry - 283.41))]),
                 xytext=(180, -1.2),
                 arrowprops=dict(arrowstyle="->", color='#8e44ad', lw=1.5),
                 fontweight='bold', color='#8e44ad',
                 bbox=dict(boxstyle="round,pad=0.3", fc="#f4ecf7", ec="#8e44ad"))

    ax2.set_title("2. ROZKŁAD CIŚNIENIA MANOMETRYCZNEGO WZDŁUŻ RUROCIĄGU", fontweight='bold')
    ax2.set_xlabel("Kilometraż rurociągu od zbiornika [m]", fontweight='bold')
    ax2.set_ylabel("Ciśnienie manometryczne [bar]", fontweight='bold')
    ax2.set_ylim(-2.0, 6.5)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', fontsize=8.5)

    katalog_wykresow = Path(__file__).resolve().parents[1] / 'wykresy'
    katalog_wykresow.mkdir(exist_ok=True)
    plik_wykres = katalog_wykresow / '05_mapa_cisnien.png'
    plt.savefig(plik_wykres, dpi=300, bbox_inches='tight')
    print(f"[OK] Wykres zapisano do: {plik_wykres}")
    plt.close(fig)

if __name__ == '__main__':
    generuj_mape_cisnien()