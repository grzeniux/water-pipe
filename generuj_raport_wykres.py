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
# 2. OBLICZENIA HYDROSTATYKI I POJEMNOŚCI WODNEJ
# ==============================================================================
def oblicz_parametry_odcinkow():
    """
    Wylicza długość i pojemność wodną dla każdej sekcji rur.
    """
    dane_sekcji = []
    laczna_pojemnosc = 0.0

    for s in config.SEKCJE_RUR:
        dlugosc = s['do_metra'] - s['od_metra']
        d = s['srednica']
        pole = np.pi * (d / 2.0)**2
        
        pojemnosc_l = pole * dlugosc * 1000.0
        laczna_pojemnosc += pojemnosc_l

        dane_sekcji.append({
            'nazwa': s['nazwa'],
            'od_metra': s['od_metra'],
            'do_metra': s['do_metra'],
            'srednica': d,
            'dlugosc': dlugosc,
            'pojemnosc_l': pojemnosc_l
        })

    return dane_sekcji, laczna_pojemnosc

def oblicz_hydrostatyke(m, z_teren):
    z_rura = z_teren - config.GLEBOKOSC_RURY
    
    punkt_dom = next(p for p in config.PUNKTY_INFRASTRUKTURY if p['typ'] == 'dom')
    h_dom = float(np.interp(punkt_dom['metr'], m, z_rura))
    h_start = float(np.interp(0.0, m, z_rura))
    
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

    dane_sekcji, poj_calkowita = oblicz_parametry_odcinkow()

    # Obliczenie objętości zrzutu wody (od studzienki do punktu wycieku)
    v_zrzut = 0.0
    for s in dane_sekcji:
        start_odc = max(punkt_studnia['metr'], s['od_metra'])
        end_odc = min(m_wyciek, s['do_metra'])
        if end_odc > start_odc:
            dl = end_odc - start_odc
            v_zrzut += np.pi * (s['srednica'] / 2.0)**2 * dl * 1000.0

    return {
        'z_rura': z_rura,
        'h_dom': h_dom,
        'slup_wody': slup_wody,
        'h_zwierciadlo': h_zwierciadlo,
        'm_wyciek': m_wyciek,
        'cisnienie': cisnienie,
        'dane_sekcji': dane_sekcji,
        'pojemnosc_calkowita': poj_calkowita,
        'v_zrzut': v_zrzut,
        'spadek_pion': h_start - h_dom
    }

# ==============================================================================
# 3. GENEROWANIE WYKRESU TECHNICZNEGO
# ==============================================================================
def rysuj_raport(m, z_teren, res):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 11), sharex=True, 
                                   gridspec_kw={'height_ratios': [2.7, 1.3]})
    plt.subplots_adjust(hspace=0.08)

    # --- PANEL GÓRNY: PROFIL TERENU I RUROCIĄG ---
    ax1.plot(m, z_teren, color='#7f8c8d', linestyle='--', linewidth=1.2, label='Powierzchnia terenu', alpha=0.7)
    ax1.fill_between(m, z_teren, min(res['z_rura']) - 15, color='#f8f9fa', alpha=0.6)

    kolory_sekcji = ['#2980b9', '#d35400', '#27ae60', '#8e44ad', '#16a085']
    for numer_sekcji, sekcja in enumerate(res['dane_sekcji']):
        mask = (m >= sekcja['od_metra']) & (m <= sekcja['do_metra'])
        kolor = kolory_sekcji[numer_sekcji % len(kolory_sekcji)]
        
        etykieta = (
            f"{sekcja['nazwa']} (L = {sekcja['dlugosc']:.1f} m | "
            f"Ø {sekcja['srednica']*1000:.1f} mm | "
            f"V = {sekcja['pojemnosc_l']:.1f} L)"
        )
        
        ax1.plot(m[mask], res['z_rura'][mask], color=kolor, linewidth=3.5, label=etykieta)

    # Słup uwięzionej wody
    maska_woda = m >= res['m_wyciek']
    ax1.fill_between(m[maska_woda], res['z_rura'][maska_woda], res['h_zwierciadlo'], 
                     color='#3498db', alpha=0.25, label=f"Uwięziona woda (naporowe {config.POMIAR_TEST_SZCZELNOSCI['cisnienie_ustabilizowane_bar']:.1f} bar)")
    ax1.axhline(res['h_zwierciadlo'], color='#2980b9', linestyle=':', linewidth=1.8)

    # Wyróżnienie punktu wycieku
    ax1.scatter([res['m_wyciek']], [res['h_zwierciadlo']], color='#c0392b', s=200, zorder=6, edgecolors='black', lw=2)

    # Usunięto 'km' - czysty zapis w metrach
    ax1.annotate(
        f"WYLICZONY PUNKT NIESZCZELNOŚCI\n"
        f"Odległość od zbiornika: {res['m_wyciek']:.1f} m  |  Rzędna: {res['h_zwierciadlo']:.2f} m n.p.m.",
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

    # Etykietowanie punktów trasy
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

    tekst_legendy = "PUNKTY TRASY:\n" + "\n".join(legenda_punktow)
    ax1.text(0.985, 0.96, tekst_legendy, transform=ax1.transAxes,
             fontsize=8.5, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#bdc3c7', alpha=0.95))

    # Ramka bilansu pojemnościowego w lewym górnym rogu
    tekst_bilansu = (
        f"BILANS POJEMNOŚCIOWY RUROCIĄGU:\n"
        f"• Długość całkowita: {max(m):.1f} m\n"
        f"• Całkowita pojemność rurociągu: {res['pojemnosc_calkowita']:.1f} L\n"
        f"• Woda wylana do gruntu przy teście: ~{res['v_zrzut']:.1f} L"
    )
    ax1.text(0.015, 0.96, tekst_bilansu, transform=ax1.transAxes,
             fontsize=9, fontweight='bold', color='#1a5276', verticalalignment='top',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#ebf5fb', edgecolor='#2980b9', alpha=0.95))

    ax1.set_ylabel('Wysokość [m n.p.m.]', fontsize=11, fontweight='bold')
    ax1.set_title('PROFIL PIONOWY TRASY RUROCIĄGU I POŁOŻENIE WYCIEKU', fontsize=13, fontweight='bold', pad=12)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    ax1.set_ylim(min(res['z_rura']) - 14, max(z_teren) + 18)
    
    # Legenda odcinków
    ax1.legend(loc='lower left', bbox_to_anchor=(0.015, 0.04), fontsize=8.0, framealpha=0.95)

    # Objaśnienie oznaczeń
    objasnienia = (
        "OBJAŚNIENIE OZNACZEŃ:\n"
        "• L = Długość fizyczna odcinka w metrach\n"
        "• Ø = Średnica wewnętrzna rury (SDR 11)\n"
        "• V = Pojemność wodna odcinka w litrach"
    )
    ax1.text(0.015, 0.33, objasnienia, transform=ax1.transAxes,
             fontsize=8.0, verticalalignment='bottom', horizontalalignment='left',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffffff', edgecolor='#bdc3c7', alpha=0.95))

    # --- PANEL DOLNY: ROZKŁAD CIŚNIENIA ---
    ax2.plot(m, res['cisnienie'], color='#c0392b', linewidth=2.5, label='Ciśnienie statyczne po teście [bar]')
    ax2.fill_between(m, res['cisnienie'], 0, color='#e74c3c', alpha=0.15)
    ax2.axvline(res['m_wyciek'], color='#c0392b', linestyle='--', alpha=0.7)

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
    print("\n" + "═" * 86)
    print("           WYNIKI WERYFIKACJI LOKALIZACJI NIESZCZELNOŚCI")
    print("═" * 86)
    print(f" • Odczyt manometru w domu:          {config.POMIAR_TEST_SZCZELNOSCI['cisnienie_ustabilizowane_bar']:.2f} bar")
    print(f" • Rzeczywisty słup wody nad domem:   {res['slup_wody']:.2f} m w pionie")
    print(f" • Poziom uwięzionej wody w rurze:    {res['h_zwierciadlo']:.2f} m n.p.m.")
    print("─" * 86)
    print(f" >>> PUNKT WYCIEKU Z OBLICZEŃ:        {res['m_wyciek']:.2f} m trasy od zbiornika <<<")
    print("═" * 86)
    print(f" PARAMETRY ODCINKÓW RUR:")
    print(f"{'Nazwa sekcji':<20} | {'Długość (L)':<12} | {'Śr. wewn. (Ø)':<14} | {'Pojemność (V)':<14}")
    print("─" * 86)
    for s in res['dane_sekcji']:
        print(f"{s['nazwa']:<20} | {s['dlugosc']:<6.1f} m     | {s['srednica']*1000:<8.1f} mm     | {s['pojemnosc_l']:<8.1f} L")
    print("─" * 86)
    print(f" RAZEM W CAŁYM RUROCIĄGU:     L = {max(m):.1f} m | V = {res['pojemnosc_calkowita']:.1f} L (zrzut w teście: ~{res['v_zrzut']:.1f} L)")
    print("═" * 86)
    print(f"{'Nr':<4} | {'Infrastruktura':<30} | {'Metr':<8} | {'Rzędna':<10} | {'Położenie':<16}")
    print("─" * 86)
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
    print("═" * 86 + "\n")

if __name__ == '__main__':
    metry, z_teren = wczytaj_profil(config.PLIK_PROFILU)
    wyniki = oblicz_hydrostatyke(metry, z_teren)
    drukuj_raport(metry, z_teren, wyniki)
    rysuj_raport(metry, z_teren, wyniki)