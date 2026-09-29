# Diagnostyka i Symulacja Rurociągu Grawitacyjnego

Projekt obliczeniowo-diagnostyczny rurociągu grawitacyjnego o długości 601 m z redukcją PE20 i punktem newralgicznym na Złączce 1 (km 309.46).

## Struktura projektu

- `config.py` - centralna konfiguracja parametrów geometrii, materiałów i pomiarów
- `dane/poprawny_profil.txt` - źródłowy profil trasy
- `core/` - parser profilu i wspólne obliczenia hydrauliczne
- `skrypty/` - zestaw skryptów obliczeniowych w Pythonie
- `web/index.html` - interaktywny symulator do przeglądarki
- `wykresy/` - generowane automatycznie wykresy PNG

## Uruchomienie środowiska

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt