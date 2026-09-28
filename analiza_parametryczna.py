import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import config
from generuj_raport_wykres import wczytaj_profil

G = 9.81
MI = 0.62

def pobierz_srednice(m_pos):
    for sekcja in config.SEKCJE_RUR:
        if sekcja['od_metra'] <= m_pos <= sekcja['do_metra']:
            return sekcja['srednica']
    return config.SEKCJE_RUR[-1]['srednica']

def wykonaj_analize_parametryczna():
    metry, z_teren = wczytaj_profil(config.PLIK_PROFILU)
    z_rura = z_teren - config.GLEBOKOSC_RURY

    punkt_dom = next(p for p in config.PUNKTY_INFRASTRUKTURY if p['typ'] == 'dom')
    punkt_studnia = next(p for p in config.PUNKTY_INFRASTRUKTURY if p['typ'] == 'studnia')
    
    h_dom = float(np.interp(punkt_dom['metr'], metry, z_rura))
    m_studnia = punkt_studnia['metr']
    z_studnia = float(np.interp(m_studnia, metry, z_rura))

    # Zakresy parametrów do badania wrażliwości
    zakres_cisnien_bar = [1.2, 1.4, 1.6, 1.8, 2.0]
    zakres_srednic_mm = [0.8, 1.5, 3.0, 5.0, 8.0, 12.0]

    macierz_czasow = np.zeros((len(zakres_cisnien_bar), len(zakres_srednic_mm)))
    macierz_objetosci = np.zeros(len(zakres_cisnien_bar))
    macierz_metrow = np.zeros(len(zakres_cisnien_bar))

    print("\n" + "═" * 86)
    print("        PARAMETRYCZNA ANALIZA SPŁYWU (WRAŻLIWOŚĆ NA CIŚNIENIE I ROZMIAR DZIURY)")
    print("═" * 86)

    # 1. Obliczenia dla każdego ciśnienia
    for i_p, p_stat in enumerate(zakres_cisnien_bar):
        slup_wody = p_stat * 10.19716
        z_wyciek = h_dom + slup_wody
        
        # Wyznaczenie metra wycieku dla danego ciśnienia
        maska_odcinka = (metry >= m_studnia) & (metry <= punkt_dom['metr'])
        m_odc, h_odc = metry[maska_odcinka], z_rura[maska_odcinka]
        m_wyciek = float(np.interp(z_wyciek, h_odc[::-1], m_odc[::-1]))
        macierz_metrow[i_p] = m_wyciek

        # Całkowanie objętości wody nad dziurą
        maska_splywu = (metry >= m_studnia) & (metry <= m_wyciek)
        m_splyw = metry[maska_splywu]
        z_splyw = z_rura[maska_splywu]

        v_litry = 0.0
        for i in range(len(m_splyw) - 1):
            dm = m_splyw[i+1] - m_splyw[i]
            d_r = pobierz_srednice(m_splyw[i])
            v_litry += (np.pi * (d_r / 2.0)**2) * dm * 1000.0
        macierz_objetosci[i_p] = v_litry

        # 2. Całkowanie ODE dla każdej średnicy szczeliny
        for j_d, d_mm in enumerate(zakres_srednic_mm):
            a_otw = np.pi * ((d_mm / 1000.0) / 2.0)**2

            def dh_dt(t, h):
                h_val = float(h[0]) if isinstance(h, (np.ndarray, list)) else float(h)
                if h_val <= z_wyciek + 0.002:
                    return [0.0]
                delta_h = max(0.0, h_val - z_wyciek)
                q_out = MI * a_otw * np.sqrt(2.0 * G * delta_h)

                m_curr = float(np.interp(h_val, z_splyw[::-1], m_splyw[::-1]))
                d_curr = pobierz_srednice(m_curr)
                a_r = np.pi * (d_curr / 2.0)**2

                idx = np.clip(np.searchsorted(m_splyw, m_curr), 1, len(m_splyw) - 1)
                dz = abs(z_splyw[idx] - z_splyw[idx - 1])
                ds = max(m_splyw[idx] - m_splyw[idx - 1], 0.01)
                sin_alfa = max(dz / ds, 0.01)

                return [- (q_out * sin_alfa) / a_r]

            sol = solve_ivp(dh_dt, (0, 14400), [z_studnia], method='RK45', rtol=1e-4)
            h_vals = sol.y[0]
            
            # Czas do osiągnięcia stabilizacji ciśnienia
            prog_h = z_wyciek + 0.05
            idx_koniec = np.where(h_vals <= prog_h)[0]
            czas_min = sol.t[idx_koniec[0]] / 60.0 if len(idx_koniec) > 0 else 240.0
            macierz_czasow[i_p, j_d] = czas_min

    # Druk tabeli tekstowej (usunięto 'km')
    naglowek_kolumn = " | ".join([f"{d:>6.1f}mm" for d in zakres_srednic_mm])
    print(f"{'Ciśn. [bar]':<11} | {'Lokalizacja':<12} | {'Zrzut [L]':<10} | Czas opróżniania do stanu stałego [min]:")
    print(f"{'':<11} | {'':<12} | {'':<10} | {naglowek_kolumn}")
    print("─" * 86)
    for i, p in enumerate(zakres_cisnien_bar):
        wiersz = " | ".join([f"{macierz_czasow[i, j]:>7.1f}m" for j in range(len(zakres_srednic_mm))])
        print(f"{p:<11.2f} | {macierz_metrow[i]:<10.1f}m | {macierz_objetosci[i]:<7.1f} L  | {wiersz}")
    print("═" * 86 + "\n")

    # Wizualizacja Heatmapy (usunięto 'km' z etykiet osi Y)
    fig, ax = plt.subplots(figsize=(11, 7))
    cax = ax.imshow(macierz_czasow, cmap='YlOrRd_r', aspect='auto', origin='lower')
    cbar = fig.colorbar(cax)
    cbar.set_label('Czas opróżniania do stabilizacji [minuty]', fontsize=10, fontweight='bold')

    ax.set_xticks(range(len(zakres_srednic_mm)))
    ax.set_xticklabels([f"Ø {d} mm" for d in zakres_srednic_mm], fontsize=10)
    ax.set_yticks(range(len(zakres_cisnien_bar)))
    ax.set_yticklabels([f"{p:.2f} bar\n({macierz_metrow[i]:.0f} m)" for i, p in enumerate(zakres_cisnien_bar)], fontsize=9.5)

    for i in range(len(zakres_cisnien_bar)):
        for j in range(len(zakres_srednic_mm)):
            wartosc = macierz_czasow[i, j]
            tekst = f"{wartosc:.1f} min" if wartosc < 120 else f"{wartosc/60:.1f} h"
            ax.text(j, i, tekst, ha="center", va="center", color="black", fontweight='bold', fontsize=9)

    ax.set_title("PARAMETRYCZNA MAPA CZASU SPŁYWU WODY DO POZIOMU NIESZCZELNOŚCI", fontsize=12, fontweight='bold', pad=14)
    ax.set_xlabel("Szacowany zastępczy rozmiar szczeliny / pęknięcia", fontsize=11, fontweight='bold')
    ax.set_ylabel("Odczytane ciśnienie statyczne w domu [bar]", fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig('analiza_parametryczna_macierz.png', dpi=300)
    print("[SUKCES] Macierz parametryczną zapisano do: analiza_parametryczna_macierz.png")
    plt.show()

if __name__ == '__main__':
    wykonaj_analize_parametryczna()