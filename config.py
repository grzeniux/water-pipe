# config.py
# ==============================================================================
# CENTRALNY PLIK KONFIGURACYJNY SYSTEMU WODOCIĄGOWEGO
# ==============================================================================

# 0. PLIK PROFILU I PARAMETRY GEOMETRYCZNE
from pathlib import Path

KATALOG_PROJEKTU = Path(__file__).resolve().parent
PLIK_PROFILU = 'dane/poprawny_profil.txt'
GLEBOKOSC_RURY = 1.5  # [m]

# 1. PARAMETRY FIZYCZNE WODY I PRZELICZNIKI
G = 9.81                          # [m/s^2]
RO_WODY = 1000.0                  # [kg/m^3]
LEPKOSC_KINEMATYCZNA = 1.31e-6    # [m^2/s] (~10°C)
MODUL_SCISLIWOSCI_WODY = 2.15e9   # [Pa] (2.15 GPa)
PRZELICZNIK_M_NA_BAR = 10.19716   # 1 bar = 10.19716 m H2O

# 2. PARAMETRY MATERIAŁOWE RUR PE-HD (PE100 SDR 11)
CHROPOWATOSC_PE = 0.007e-3        # [m] k = 0.007 mm
MODUL_YOUNGA_DYN = 900e6           # [Pa] do Żukowskiego
MODUL_YOUNGA_STAT = 800e6          # [Pa] do sił poosiowych
MODUL_YOUNGA_DYNAMICZNY = MODUL_YOUNGA_DYN
MODUL_YOUNGA_STATYCZNY = MODUL_YOUNGA_STAT
WSP_ROZSZERZALNOSCI = 1.8e-4      # [1/K]

# Średnice wewnętrzne rur [m]
D_PE40 = 0.0326
D_PE32 = 0.0260
D_PE25 = 0.0204
D_PE20 = 0.0160

# 3. PUNKTY INFRASTRUKTURY
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
        'metr': 217.4,
        'opis': 'Zawór odcinający i reduktor'
    },
    {
        'nazwa': 'Zlaczka1 - lewa strona pola Marka',
        'typ': 'zlaczka',
        'metr': 309.46,
        'opis': 'Przejście PE40 / PE20 na PE32 (punkt awarii i nowego zaworu)'
    },
    {
        'nazwa': 'Zlaczka2 - prawa strona pola Marka',
        'typ': 'zlaczka',
        'metr': 401.0,
        'opis': 'Początek odcinka PE32 / PE25'
    },
    {
        'nazwa': 'Zlaczka3 - podwórko u Satrow',
        'typ': 'zlaczka',
        'metr': 425.87,
        'opis': 'Początek odcinka PE32 / PE25'
    },
    {
        'nazwa': 'Dom (zawór + manometr)',
        'typ': 'dom',
        'metr': 601.0,
        'opis': 'Punkt odbioru i manometr'
    }
]

# 4. SEKCJE RUROCIĄGU
SEKCJE_RUR = [
    {
        'nazwa': 'Odcinek 1 - PE40',
        'srednica': D_PE40,
        'grubosc_scianki': 0.0037,
        'od_metra': 0.0,
        'do_metra': 217.4,
    },
    {
        'nazwa': 'Odcinek 2 - PE20 (w osłonie PE40)',
        'srednica': D_PE20,
        'grubosc_scianki': 0.0020,
        'od_metra': 217.4,
        'do_metra': 309.46,
    },
    {
        'nazwa': 'Odcinek 3 - PE32',
        'srednica': D_PE32,
        'grubosc_scianki': 0.0030,
        'od_metra': 309.46,
        'do_metra': 401.0,
    },
    {
        'nazwa': 'Odcinek 4 - PE25',
        'srednica': D_PE25,
        'grubosc_scianki': 0.0023,
        'od_metra': 401.0,
        'do_metra': 425.87,
    },
    {
        'nazwa': 'Odcinek 5 - PE32',
        'srednica': D_PE32,
        'grubosc_scianki': 0.0030,
        'od_metra': 425.87,
        'do_metra': 601.0,
    },
]

# 5. DANE Z TESTU TATY
POMIAR_TEST_SZCZELNOSCI = {
    'cisnienie_poczatkowe_bar': 3.0,
    'cisnienie_ustabilizowane_bar': 1.6,
    'czas_spadku_min': 105.0,
    'punkt_zamkniety': 'Studzienka z reduktorem'
}