# config.py
# ==============================================================================
# CENTRALNY PLIK KONFIGURACYJNY SYSTEMU WODOCIĄGOWEGO
# ==============================================================================

# 0. PLIK PROFILU I PARAMETRY GEOMETRYCZNE
from pathlib import Path

KATALOG_PROJEKTU = Path(__file__).resolve().parent
PLIK_PROFILU = 'dane/profil_terenu2.txt'
GLEBOKOSC_RURY = 1.5  # [m]

# 1. PARAMETRY FIZYCZNE WODY I PRZELICZNIKI
G = 9.81                          # [m/s^2]
RO_WODY = 1000.0                  # [kg/m^3]
LEPKOSC_KINEMATYCZNA = 1.31e-6    # [m^2/s] (~10°C)
MODUL_SCISLIWOSCI_WODY = 2.15e9   # [Pa] (2.15 GPa)
METRY_NA_AT = 10.0                # 1 At = 10.0 m H2O
AT_NA_BAR = 0.980665              # 1 At = 0.980665 bar
PRZELICZNIK_M_NA_BAR = METRY_NA_AT / AT_NA_BAR

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
        'metr': 225.38,
        'opis': 'Zawór odcinający i reduktor'
    },
    {
        'nazwa': 'Zlaczka1 - lewa strona pola Marka',
        'typ': 'zlaczka',
        'metr': 320.73,
        'opis': 'Przybliżona lokalizacja ze zrzutu profilu; granica PE20/PE32 jest na km 322.73'
    },
    {
        'nazwa': 'Zlaczka2 - prawa strona pola Marka',
        'typ': 'zlaczka',
        'metr': 414.0,
        'opis': 'Początek odcinka PE32 / PE25'
    },
    {
        'nazwa': 'Zlaczka3 - podwórko u Satrow',
        'typ': 'zlaczka',
        'metr': 438.0,
        'opis': 'Początek odcinka PE32 / PE25'
    },
    {
        'nazwa': 'Dom (zawór + manometr)',
        'typ': 'dom',
        'metr': 619.0,
        'opis': 'Punkt odbioru i manometr'
    }
]

# 4. DEFINICJA RUR I SEKCJI RUROCIĄGU
#
# Edycja geometrii odbywa się tutaj:
# - rura_wewnetrzna.srednica: średnica hydrauliczna przewodu,
# - osłona.srednica: opcjonalna rura, w której prowadzony jest przewód,
# - podzialy_m: dodatkowe granice odcinka, np. dla końcowego odcinka.
# Każda sekcja może mieć własną rurę w rurze; osłona nie bierze udziału
# w obliczaniu strat przepływu.
# Punkt zmiany technologii. Zastąp rzeczywistym metrażem po wytyczeniu trasy.
GRANICA_PE20_WCISKANEJ_M = 518.0  # ok. 80 m od Złączki nr 3 na km 438.0

DEFINICJE_SEKCJI_RUR = [
    {
        'nazwa': 'Odcinek 1 - PE40',
        'od_metra': 0.0,
        'do_metra': 225.38,
        'rura_wewnetrzna': {'nazwa': 'PE40', 'srednica': D_PE40, 'grubosc_scianki': 0.0037},
        'osłona': None,
    },
    {
        'nazwa': 'Odcinek 2 - PE20 w osłonie PE40',
        'od_metra': 225.38,
        'do_metra': 322.73,
        'rura_wewnetrzna': {'nazwa': 'PE20', 'srednica': D_PE20, 'grubosc_scianki': 0.0020},
        'osłona': {'nazwa': 'PE40', 'srednica': D_PE40},
    },
    {
        'nazwa': 'Odcinek 3 - PE32',
        'od_metra': 322.73,
        'do_metra': 414.0,
        'rura_wewnetrzna': {'nazwa': 'PE32', 'srednica': D_PE32, 'grubosc_scianki': 0.0030},
        'osłona': None,
    },
    {
        'nazwa': 'Odcinek 4 - PE25 w osłonie PE32',
        'od_metra': 414.0,
        'do_metra': 438.0,
        'rura_wewnetrzna': {'nazwa': 'PE25', 'srednica': D_PE25, 'grubosc_scianki': 0.0023},
        'osłona': {'nazwa': 'PE32', 'srednica': D_PE32},
    },
    {
        'nazwa': 'Odcinek 5 - nowa PE32 kopana',
        'od_metra': 438.0,
        'do_metra': GRANICA_PE20_WCISKANEJ_M,
        'rura_wewnetrzna': {'nazwa': 'PE32', 'srednica': D_PE32, 'grubosc_scianki': 0.0030},
        'osłona': None,
        'technologia': 'wykopana',
    },
    {
        'nazwa': 'Odcinek 6 - PE20 wciskana pod nawierzchnią',
        'od_metra': GRANICA_PE20_WCISKANEJ_M,
        'do_metra': 619.0,
        'rura_wewnetrzna': {'nazwa': 'PE20', 'srednica': D_PE20, 'grubosc_scianki': 0.0020},
        # Jeśli PE20 będzie wciskana w większą rurę/osłonę, wpisz ją tutaj.
        'osłona': None,
        'technologia': 'wciskana',
    },
]


def _rozwin_sekcje(definicje):
    sekcje = []
    for definicja in definicje:
        granice = [definicja['od_metra'], *definicja.get('podzialy_m', []), definicja['do_metra']]
        granice = sorted(set(granice))
        if granice[0] != definicja['od_metra'] or granice[-1] != definicja['do_metra']:
            raise ValueError(f"Podziały poza zakresem sekcji: {definicja['nazwa']}")
        for numer, (od_metra, do_metra) in enumerate(zip(granice[:-1], granice[1:]), start=1):
            if do_metra <= od_metra:
                raise ValueError(f"Nieprawidłowy zakres sekcji: {definicja['nazwa']}")
            rura = definicja['rura_wewnetrzna']
            osłona = definicja.get('osłona')
            nazwa = definicja['nazwa']
            if len(granice) > 2:
                nazwa = f"{nazwa} / część {numer}"
            sekcja = {
                'nazwa': nazwa,
                'od_metra': od_metra,
                'do_metra': do_metra,
                'rura_wewnetrzna': dict(rura),
                'osłona': dict(osłona) if osłona else None,
                'technologia': definicja.get('technologia', 'nieokreślona'),
                # Pola płaskie dla istniejących skryptów.
                'srednica': rura['srednica'],
                'grubosc_scianki': rura['grubosc_scianki'],
                'srednica_oslony': osłona['srednica'] if osłona else None,
            }
            sekcje.append(sekcja)
    return sekcje


SEKCJE_RUR = _rozwin_sekcje(DEFINICJE_SEKCJI_RUR)


def _sprawdz_ciaglosc_sekcji(sekcje):
    if not sekcje:
        raise ValueError('Brak zdefiniowanych sekcji rur')
    for poprzednia, biezaca in zip(sekcje, sekcje[1:]):
        if abs(poprzednia['do_metra'] - biezaca['od_metra']) > 1e-9:
            raise ValueError(
                f"Przerwa lub nakładanie sekcji między {poprzednia['nazwa']} "
                f"a {biezaca['nazwa']}"
            )
    if abs(sekcje[0]['od_metra'] - 0.0) > 1e-9:
        raise ValueError('Pierwsza sekcja musi zaczynać się na 0 m')
    metr_dom = next(p['metr'] for p in PUNKTY_INFRASTRUKTURY if p['typ'] == 'dom')
    if abs(sekcje[-1]['do_metra'] - metr_dom) > 1e-9:
        raise ValueError('Ostatnia sekcja musi kończyć się przy domu')


_sprawdz_ciaglosc_sekcji(SEKCJE_RUR)

# 5. DANE Z TESTU TATY
POMIAR_TEST_SZCZELNOSCI = {
    'data': '22 IX',
    'godzina_start': '14:19',
    'godzina_koniec': '15:12',
    'cisnienie_poczatkowe_at': 3.0,
    'cisnienie_ustabilizowane_at': 1.4,
    'cisnienie_poczatkowe_bar': 3.0 * AT_NA_BAR,
    'cisnienie_ustabilizowane_bar': 1.4 * AT_NA_BAR,
    'slup_wody_poczatkowy_m': 30.0,
    'slup_wody_ustabilizowany_m': 14.0,
    'czas_spadku_min': 53.0,
    'punkt_zamkniety': 'Studzienka z reduktorem',
    'rozbior_w_domu': False,
}

POMIARY_WZROSTU_24_IX = [
    {'data': '24 IX', 'godzina': '16:22', 'cisnienie_at': 3.8},
    {'data': '24 IX', 'godzina': '16:24', 'cisnienie_at': 4.0},
    {'data': '24 IX', 'godzina': '16:29', 'cisnienie_at': 4.1},
    {'data': '24 IX', 'godzina': '16:35', 'cisnienie_at': 4.5},
    {'data': '24 IX', 'godzina': '16:40', 'cisnienie_at': 4.6},
    {'data': '24 IX', 'godzina': '16:46', 'cisnienie_at': 4.7},
    {'data': '24 IX', 'godzina': '16:58', 'cisnienie_at': 4.8},
    {'data': '24 IX', 'godzina': '17:16', 'cisnienie_at': 5.0},
]