import os
import re
import numpy as np
import matplotlib.pyplot as plt

try:
    import config
except ImportError:
    raise ImportError("Upewnij sie, ze plik config.py znajduje sie w tym samym katalogu!")

# ==============================================================================
# 1. PARSOWANIE PROFILU GEODEZYJNEGO (X, Y, Z)
# ==============================================================================
def wczytaj_profil(sciezka):
    if not os.path.exists(sciezka):
        raise FileNotFoundError(f"Brak pliku profilu: {sciezka}")

    px, py, pz = [], [], []
    with open(sciezka, 'r', encoding='utf-8', errors='ignore') as f:
        for linia in f:
            liczby = [float(x) for x in re.findall(r'[-+]?\d*\.?\d+', linia.replace(',', '.'))]
            if len(liczby) == 3 and liczby[0] > 1000 and liczby[1] > 1000:
                px.append(liczby[0])
                py.append(liczby[1])
                pz.append(liczby[2])

    if not px:
        raise ValueError(f"Nie znaleziono danych geodezyjnych w: {sciezka}")

    px, py, pz = np.array(px), np.array(py), np.array(pz)
    odcinki = np.sqrt(np.diff(px)**2 + np.diff(py)**2)
    metry = np.insert(np.cumsum(odcinki), 0, 0.0)

    # Sortowanie i unikanie duplikatów
    m_unikalne, z_unikalne = [], []
    for m, z in zip(metry, pz):
        if not m_unikalne or m > m_unikalne[-1]:
            m_unikalne.append(m)
            z_unikalne.append(z)

    m_siatka = np.linspace(0.0, m_unikalne[-1], int(m_unikalne[-1] * 2))
    z_siatka = np.interp(m_siatka, m_unikalne, z_unikalne)
    return m_siatka, z_siatka

# ==============================================================================
# 2. OBLICZENIA HYDROSTATYKI
# ==============================================================================
def oblicz_hydrostatyke(m, z_teren):
    z_rura = z_teren - config.GLEBOKOSC_RURY
    
    punkt_dom = next(p for p in config.PUNKTY_INFRASTRUKTURY if p['typ'] == 'dom')
    h_dom = float(np.interp(punkt_dom['metr'], m, z_rura))
    
    P_stat = config.POMIAR_TEST_SZCZELNOSCI['cisnienie_ustabilizowane_bar']
    slup_wody = P_stat * 10.19716
    h_zwierciadlo = h_dom + slup_wody
    
    punkt_studnia = next(p for p in config.PUNKTY_INFRASTRUKTURY if p['typ'] == 'studnia')
    maska_odcinka = (m >= punkt_studnia['metr']) & (m <= punkt_dom['metr'])
    m_odc, h_odc = m[maska_odcinka], z_rura[maska_odcinka]
    
    m_wyciek = float(np.interp(h_zwierciadlo, h_odc[::-1], m_odc[::-1]))
    
    cisnienie = np.zeros_like(z_rura)
    for i in range(len(m)):
        if m[i] >= m_wyciek:
            cisnienie[i] = max(0.0, (h_zwierciadlo - z_rura[i]) / 10.19716)

    return {
        'z_rura': z_rura,
        'h_dom': h_dom,
        'slup_wody': slup_wody,
        'h_zwierciadlo': h_zwierciadlo,
        'm_wyciek': m_wyciek,
        'cisnienie': cisnienie
    }

# ==============================================================================
# 3. GENEROWANIE CZYTELNEGO WYKRESU TECHNICZNEGO
# ==============================================================================
def rysuj_raport(m, z_teren, res):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 11), sharex=True, 
                                   gridspec_kw={'height_ratios': [2.7, 1.3]})
    plt.subplots_adjust(hspace=0.08)

    # --- PANEL GÓRNY: PROFIL TERENU I RUROCIĄG ---
    ax1.plot(m, z_teren, color='#7f8c8d', linestyle='--', linewidth=1.2, label='Powierzchnia terenu', alpha=0.7)
    ax1.fill_between(m, z_teren, min(res['z_rura']) - 10, color='#f8f9fa', alpha=0.6)

    # Rurociąg z sekcjami
    kolory_rur = {'PE40': '#2980b9', 'PE20': '#d35400', 'PE32': '#27ae60', 'PE25': '#8e44ad'}
    for sekcja in config.SEKCJE_RUR:
        mask = (m >= sekcja['od_metra']) & (m <= sekcja['do_metra'])
        klucz = [k for k in kolory_rur if k in sekcja['nazwa']][0]
        ax1.plot(m[mask], res['z_rura'][mask], color=kolory_rur[klucz], linewidth=3.5,
                 label=f"{sekcja['nazwa']} (śr. wewn. {sekcja['srednica']*1000:.1f} mm)")

    # Słup uwięzionej wody
    maska_woda = m >= res['m_wyciek']
    ax1.fill_between(m[maska_woda], res['z_rura'][maska_woda], res['h_zwierciadlo'], 
                     color='#3498db', alpha=0.25, label='Uwięziona woda (naporowe 1.6 bar)')
    ax1.axhline(res['h_zwierciadlo'], color='#2980b9', linestyle=':', linewidth=1.8)

    # Wyróżnienie punktu wycieku
    ax1.scatter([res['m_wyciek']], [res['h_zwierciadlo']], color='#c0392b', s=200, zorder=6, edgecolors='black', lw=2)

    # RAMKA WYNIKU WYCIEKU WYNIESIONA WYSOKO NAD WYKRES (brak kolizji z punktem [2])
    ax1.annotate(
        f"WYLICZONY PUNKT NIESZCZELNOŚCI\n"
        f"Odległość: km {res['m_wyciek']:.1f} m  |  Rzędna: {res['h_zwierciadlo']:.2f} m n.p.m.",
        xy=(res['m_wyciek'], res['h_zwierciadlo']),
        xytext=(res['m_wyciek'] - 30, 606.0),
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="angle,angleA=0,angleB=90,rad=10",
            color='#c0392b',
            lw=2.0
        ),
        fontsize=10, fontweight='bold', color='#c0392b', ha='center',
        bbox=dict(boxstyle="round,pad=0.5", fc="#fdf2e9", ec="#c0392b", lw=1.5)
    )

    # Etykietowanie punktów infrastruktury (kółka z numerami)
    legenda_punktow = []
    for i, pkt in enumerate(config.PUNKTY_INFRASTRUKTURY, start=1):
        m_pkt = pkt['metr']
        if m_pkt <= max(m):
            h_pkt = float(np.interp(m_pkt, m, z_teren))
            ax1.scatter([m_pkt], [h_pkt], color='#2c3e50', s=70, zorder=5)
            
            offset_y = 3.5 if i % 2 == 1 else 6.5
            ax1.annotate(
                f"{i}", xy=(m_pkt, h_pkt), xytext=(m_pkt, h_pkt + offset_y),
                ha='center', va='center', fontsize=9, fontweight='bold', color='white',
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.0),
                bbox=dict(boxstyle="circle,pad=0.25", fc="#2c3e50", ec="black", lw=1)
            )
            legenda_punktow.append(f"[{i}] {pkt['nazwa']} ({m_pkt:.1f} m)")

    # Legenda punktów trasy w prawym górnym rogu
    tekst_legendy = "PUNKTY TRASY:\n" + "\n".join(legenda_punktow)
    ax1.text(0.985, 0.96, tekst_legendy, transform=ax1.transAxes,
             fontsize=8.5, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#bdc3c7', alpha=0.95))

    ax1.set_ylabel('Wysokość [m n.p.m.]', fontsize=11, fontweight='bold')
    ax1.set_title('PROFIL PIONOWY TRASY RUROCIĄGU I POŁOŻENIE WYCIEKU', fontsize=13, fontweight='bold', pad=12)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # Podniesiony limit Y, aby zmieścić ramkę na wysokości 606 m bez ucinania
    ax1.set_ylim(min(res['z_rura']) - 8, max(z_teren) + 18)
    ax1.legend(loc='lower left', fontsize=8.5, framealpha=0.95)

    # --- PANEL DOLNY: ROZKŁAD CIŚNIENIA ---
    ax2.plot(m, res['cisnienie'], color='#c0392b', linewidth=2.5, label='Ciśnienie statyczne po teście [bar]')
    ax2.fill_between(m, res['cisnienie'], 0, color='#e74c3c', alpha=0.15)
    ax2.axvline(res['m_wyciek'], color='#c0392b', linestyle='--', alpha=0.7)

    # Etykieta manometru w domu
    p_dom = config.POMIAR_TEST_SZCZELNOSCI['cisnienie_ustabilizowane_bar']
    ax2.scatter([601.0], [p_dom], color='#2980b9', s=90, zorder=5)
    ax2.annotate(f"Manometr w domu: {p_dom:.2f} bar\n(Słup w pionie: {res['slup_wody']:.1f} m)",
                 xy=(601.0, p_dom), xytext=(450, p_dom + 0.35),
                 arrowprops=dict(arrowstyle='->', color='#2980b9', lw=1.5),
                 fontsize=9, fontweight='bold', color='#1f618d',
                 bbox=dict(boxstyle="round,pad=0.3", fc="#ebf5fb", ec="#2980b9", lw=1))

    ax2.set_xlabel('Odległość wzdłuż trasy od zbiornika [metry]', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Ciśnienie [bar]', fontsize=11, fontweight='bold')
    ax2.set_ylim(-0.1, max(res['cisnienie']) + 0.7)
    ax2.grid(True, linestyle=':', alpha=0.5)
    ax2.legend(loc='upper left', fontsize=8.5)

    plik_wykresu = 'wykres_wycieku_raport.png'
    plt.savefig(plik_wykresu, dpi=300, bbox_inches='tight')
    print(f"\n[SUKCES] Wykres zapisano do: {plik_wykresu}")
    plt.show()

# ==============================================================================
# 4. TABELA ZBIORCZA W TERMINALU
# ==============================================================================
def drukuj_raport(m, z_teren, res):
    print("\n" + "═" * 78)
    print("           WYNIKI WERYFIKACJI LOKALIZACJI NIESZCZELNOŚCI")
    print("═" * 78)
    print(f" • Odczyt manometru w domu:          {config.POMIAR_TEST_SZCZELNOSCI['cisnienie_ustabilizowane_bar']:.2f} bar")
    print(f" • Rzeczywisty słup wody nad domem:   {res['slup_wody']:.2f} m w pionie")
    print(f" • Poziom uwięzionej wody w rurze:    {res['h_zwierciadlo']:.2f} m n.p.m.")
    print("─" * 78)
    print(f" >>> PUNKT WYCIEKU Z OBLICZEŃ:        km {res['m_wyciek']:.2f} m trasy <<<")
    print("═" * 78)
    print(f"{'Nr':<4} | {'Infrastruktura':<30} | {'Metr':<8} | {'Rzędna':<10} | {'Położenie':<16}")
    print("─" * 78)
    for i, pkt in enumerate(config.PUNKTY_INFRASTRUKTURY, start=1):
        if pkt['metr'] <= max(m):
            h_pkt = float(np.interp(pkt['metr'], m, z_teren))
            diff = res['m_wyciek'] - pkt['metr']
            if abs(diff) < 1.0:
                relacja = "TUTAJ (±1 m)"
            elif diff > 0:
                relacja = f"{abs(diff):.1f} m poniżej"
            else:
                relacja = f"{abs(diff):.1f} m powyżej"
            print(f"[{i}]  | {pkt['nazwa']:<30} | {pkt['metr']:<8.1f} | {h_pkt:<8.2f} m | {relacja:<16}")
    print("═" * 78 + "\n")

# ==============================================================================
# URUCHOMIENIE
# ==============================================================================
if __name__ == '__main__':
    metry, z_teren = wczytaj_profil(config.PLIK_PROFILU)
    wyniki = oblicz_hydrostatyke(metry, z_teren)
    drukuj_raport(metry, z_teren, wyniki)
    rysuj_raport(metry, z_teren, wyniki)