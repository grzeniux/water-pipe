# config.py

# ==============================================================================
# 0. PLIK ŹRÓDŁOWY PROFILU TERENU (z Geoportalu)
# ==============================================================================
# PLIK_PROFILU = 'profil_terenu_woda.txt'
PLIK_PROFILU = 'geoportal/poprawny_profil.txt'

# ==============================================================================
# 1. PARAMETRY ŚREDNIC RUR (metry) - SDR 11
# ==============================================================================
D_PE40 = 0.0326   # wewn. 32.6 mm
D_PE32 = 0.0260   # wewn. 26.0 mm
D_PE25 = 0.0204   # wewn. 20.4 mm
D_PE20 = 0.0160   # wewn. 16.0 mm

GLEBOKOSC_RURY = 1.5   # metry pod powierzchnią gruntu

# ==============================================================================
# 2. PUNKTY CHARAKTERYSTYCZNE WZDŁUŻ PROFILU (odczytane z Geoportalu)
# Wpisz 'metr' dokładnie taki, jaki wyświetla się w dymku na wykresie Geoportalu
# ==============================================================================
PUNKTY_INFRASTRUKTURY = [
    {
        'nazwa': 'Zbiornik górny',
        'typ': 'zbiornik',
        'metr': 0.0,
        'opis': 'Początek trasy rurociągu'
    },
    {
        'nazwa': 'Studzienka z reduktorem',
        'typ': 'studnia',
        'metr': 217.4,       # Odczytane z Geoportalu
        'opis': 'Zawór odcinający i reduktor'
    },
    {
        'nazwa': 'Zlaczka1 - lewa strona pola Marka',  # Zlaczka tam gdzie wchodzilo 110m rury, lewa strona pola Marka
        'typ': 'zlaczka',
        'metr': 309.46, 
        'opis': 'Przejście PE40 / PE20'
    },
    # {
    #     'nazwa': 'Trójnik do sąsiada',
    #     'typ': 'trojnik',
    #     'metr': 369.11,
    #     'opis': 'Odejście do sąsiada'
    # },
    {
        'nazwa': 'Zlaczka2 - prawa strona pola Marka', # prawa strona pola Marka
        'typ': 'zlaczka',
        'metr': 401.0, 
        'opis': 'Początek odcinka PE32 / PE25'
    },
    {
        'nazwa': 'Zlaczka3 - podwórko u Satrow', # podworko u Satrow
        'typ': 'zlaczka',
        'metr': 425.87,
        'opis': 'Początek odcinka PE32 / PE25'
    },
    {
        'nazwa': 'Dom (zawór + manometr)',
        'typ': 'dom',
        'metr': 601.0,
        'opis': 'Manometr'
    }
]

# ==============================================================================
# 3. ODCINKI RUR (kolejność od zbiornika do domu)
# Podaj metry początkowe i końcowe dla każdego typu rury:
# PE40 -> PE20 -> PE32 -> PE25 -> PE32
# ==============================================================================
SEKCJE_RUR = [
    {
        'nazwa': 'Odcinek 1 - PE40',
        'srednica': D_PE40,
        'od_metra': 0.0,
        'do_metra': 217.4,
    },
    {
        'nazwa': 'Odcinek 2 - PE20',
        'srednica': D_PE20,
        'od_metra': 217.4,
        'do_metra': 309.46,
    },
    {
        'nazwa': 'Odcinek 3 - PE32',
        'srednica': D_PE32,
        'od_metra': 309.46,
        'do_metra': 401.0,
    },
    {
        'nazwa': 'Odcinek 4 - PE25',
        'srednica': D_PE25,
        'od_metra': 401.0,
        'do_metra': 425.87,
    },
    {
        'nazwa': 'Odcinek 5 - PE32',
        'srednica': D_PE32,
        'od_metra': 425.87,
        'do_metra': 601.0,
    },
]

# ==============================================================================
# 4. POMIARY Z TESTU TATY
# ==============================================================================
POMIAR_TEST_SZCZELNOSCI = {
    'cisnienie_ustabilizowane_bar': 1.6,   # Wartość, na której stanęła wskazówka
    'czas_spadku_min': 105,                # Średnio ~1.5h - 2h
    'zamkniety_punkt': 'Studzienka z reduktorem'
}