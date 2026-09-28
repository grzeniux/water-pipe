import os
import re
import numpy as np
import pandas as pd
import config

def wczytaj_profil(sciezka_pliku):
    if not os.path.exists(sciezka_pliku):
        raise FileNotFoundError(f"Nie znaleziono pliku: {sciezka_pliku}. Sprawdź nazwę w config.py.")
    
    punkty = []
    regex = re.compile(r'^\s*([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)')
    
    with open(sciezka_pliku, 'r', encoding='utf-8') as f:
        for linia in f:
            m = regex.match(linia.strip())
            if m:
                punkty.append(tuple(map(float, m.groups())))
                
    if not punkty:
        raise ValueError(f"Plik {sciezka_pliku} nie zawiera poprawnych współrzędnych X, Y, Z.")
        
    df = pd.DataFrame(punkty, columns=['X', 'Y', 'Z']).drop_duplicates().reset_index(drop=True)
    
    dx = df['X'].diff().fillna(0)
    dy = df['Y'].diff().fillna(0)
    dz = df['Z'].diff().fillna(0)
    df['dist'] = np.sqrt(dx**2 + dy**2 + dz**2).cumsum()
    
    return df

def main():
    print("\n" + "=" * 75)
    print("           LOKALIZACJA WYCIEKU NA PODSTAWIE STATYKI CIŚNIENIA")
    print("=" * 75)
    
    df = wczytaj_profil(config.PLIK_PROFILU)
    
    Z_dom = df['Z'].iloc[-1]
    cisnienie_bar = config.POMIAR_TEST_SZCZELNOSCI['cisnienie_ustabilizowane_bar']
    slup_wody_m = cisnienie_bar * 10.197  # 1 bar = 10.197 m słupa wody
    Z_wyciek = Z_dom + slup_wody_m
    
    idx_dziura = (np.abs(df['Z'] - Z_wyciek)).argmin()
    trafiony = df.iloc[idx_dziura]
    metr_dziury = trafiony['dist']
    calkowita_dlugosc = df['dist'].iloc[-1]
    
    print(f"Plik profilu:                     {config.PLIK_PROFILU}")
    print(f"Całkowita długość profilu:        {calkowita_dlugosc:.2f} m")
    print(f"Rzędna terenu przy domu:          {Z_dom:.2f} m n.p.m.")
    print(f"Ciśnienie ustabilizowane:         {cisnienie_bar:.2f} bar")
    print(f"Wysokość słupa wody:              {slup_wody_m:.2f} m")
    print(f"Wyliczona rzędna wycieku:         {Z_wyciek:.2f} m n.p.m.")
    print("-" * 75)
    print("WYNIK LOKALIZACJI PUNKTU WYCIEKU:")
    print(f" -> Dystans od zbiornika:         {metr_dziury:.2f} m")
    print(f" -> Odległość od domu w górę:     {calkowita_dlugosc - metr_dziury:.2f} m")
    print(f" -> Współrzędne PL-1992:          X = {trafiony['X']:.2f}, Y = {trafiony['Y']:.2f}")
    print("-" * 75)
    
    sekcja_trafiona = None
    for s in config.SEKCJE_RUR:
        if s['od_metra'] <= metr_dziury <= s['do_metra']:
            sekcja_trafiona = s
            break
            
    if sekcja_trafiona:
        print(f"Podejrzany odcinek rury:          {sekcja_trafiona['nazwa']}")
    
    print("\nODLEGŁOŚĆ OD ZDEFINIOWANYCH ELEMENTÓW:")
    for pkt in config.PUNKTY_INFRASTRUKTURY:
        delta = metr_dziury - pkt['metr']
        if delta > 0:
            relacja = f"{abs(delta):6.1f} m w dół (w stronę domu)"
        else:
            relacja = f"{abs(delta):6.1f} m w górę (w stronę zbiornika)"
        print(f" * {pkt['nazwa']:<32} [km {pkt['metr']:6.1f} m] -> {relacja}")
        
    print("=" * 75 + "\n")

if __name__ == '__main__':
    main()