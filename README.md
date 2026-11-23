# multicamera_ai_system

Desktopová aplikácia v Pythone, ktorá spracúva viac video zdrojov naraz (video súbory, webkamera, RTSP/HLS), zjednocuje ich formát a posiela ich do modelu YOLOv8 na detekciu objektov.

## Čo systém robí

- **Prijíma viac zdrojov súčasne:** video súbory (`.mp4`, `.avi`), webkameru a RTSP/HLS URL. Zdroje sa pridávajú a odoberajú za behu cez tlačidlá v UI.
- **Normalizuje vstup:** každý snímok sa zmení na 640×360 a prevedie z BGR do RGB. FPS sa normalizuje na cieľových 15 FPS tak, že sa spracúva len každý N-tý snímok (N = zdrojové FPS / 15, minimálne 1).
- **Detekuje objekty modelom YOLOv8n:** len triedy COCO 0, 1, 2, 3, 5, 7 (osoba, bicykel, auto, motorka, autobus, nákladiak). Pre každý snímok sa meria čas inferencie a FPS.
- **Ukladá snímky s metadátami:** každý 30. snímok streamu, na ktorom je aspoň jeden objekt, sa uloží ako JPG do `frames/<PROTOKOL>/`. Riadok s časovou značkou (`YYYYMMDD_HHMMSS`), názvom streamu, protokolom, počtom detekcií, FPS a časom inferencie sa pridá do `logs/metadata.csv`. Ukladanie a zber štatistík sa spustia až pri **aspoň 4 aktívnych streamoch** (`REQUIRED_STREAMS` v `ui/dashboard.py`).
- **Zobrazuje dashboard a výkonnostný report:** všetky streamy sú v jednej mriežke s údajmi FPS, latencia AI, počet objektov, protokol a stav. Pri zatvorení okna sa vypíše súhrn a uloží do `logs/performance_report.csv`. Ak zdroj prestane vracať snímky, systém sa ho pokúsi znova otvoriť.

## Architektúra a štruktúra priečinkov

```
multicamera_ai_system/
├── main.py                 # vstupný bod, spustí úvodnú obrazovku
├── requirements.txt
├── core/
│   ├── settings.py         # konštanty (rozlíšenie, FPS, N-tý snímok, triedy YOLO, rozmery UI)
│   ├── stream_manager.py   # pridávanie/odoberanie/znovupripojenie zdrojov, detekcia protokolu
│   ├── normalizer.py       # zmena rozlíšenia a farebného priestoru
│   ├── detector.py         # YOLOv8 inferencia + meranie FPS a latencie
│   ├── extractor.py        # ukladanie snímkov (frames/) a metadát (logs/metadata.csv)
│   └── performance.py      # agregácia štatistík a report (logs/performance_report.csv)
├── ui/
│   ├── start_menu.py       # úvodná obrazovka (Tkinter)
│   └── dashboard.py        # hlavné okno s mriežkou streamov a ovládaním
└── tests/
    └── test_modules.py     # unit testy (unittest)
```

Tok dát pre každý snímok: **zdroj (`stream_manager`) → `normalizer` → `detector` → `extractor` / `performance` → dashboard (`ui`)**.

Priečinky `frames/` a `logs/` vznikajú pri behu programu. Priečinky `videos/`, `output/`, váhy `*.pt` a obrázky/videá sú v `.gitignore`.

## Požiadavky a inštalácia

Potrebuješ:

- Python 3 s knižnicou Tkinter (na Windowse je súčasťou štandardnej inštalácie; na Linuxe ju treba doinštalovať z balíkov systému, napr. `python3-tk`).
- Balíky z `requirements.txt`: `opencv-python`, `ultralytics`, `numpy`, `pillow` (verzie nie sú pripnuté).
- Model `yolov8n.pt`. Kód ho načíta menom `YOLO("yolov8n.pt")` a súbor v repozitári nie je. Podľa dokumentácie knižnice `ultralytics` sa pri prvom spustení stiahne sám, preto treba internet.

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Testované s Pythonom 3.13.3 (Windows).

## Spustenie

Z koreňového priečinka projektu:

```
python main.py
```

(na Linuxe `python3 main.py`)

Otvorí sa úvodná obrazovka, tlačidlo **START SYSTEM** otvorí dashboard. Tlačidlá v dashboarde:

- **ADD VIDEO** – výber súboru `.mp4` alebo `.avi`,
- **ADD WEBCAM** – pripojí kameru s indexom 0,
- **ADD STREAM** – zadáš RTSP alebo HLS (`.m3u8`) URL,
- **REMOVE STREAM** – odstráni stream podľa čísla.

Poznámky k platforme (vyplývajú z kódu, nespúšťané):

- Webkamera sa otvára cez `cv2.CAP_DSHOW`, čo je backend pre Windows. Na Linuxe nemusí fungovať.
- Okná používajú `root.state("zoomed")`, čo je určené pre Windows. Na Linuxe správanie nie je overené.
- Ukladanie snímkov a report vzniknú až pri aspoň 4 streamoch (pozri vyššie).

## Testy

Testy používajú modul `unittest` (nie pytest) a nepotrebujú kameru ani model. Spúšťaj ich z koreňového priečinka, lebo niektoré testy zapisujú do `logs/`:

```
python -m unittest discover -s tests -v
```

Alternatívne `python tests/test_modules.py`. Testy pokrývajú detekciu protokolu, normalizáciu snímku, agregáciu výkonnostných štatistík, konštanty v `settings.py` a odoberanie streamov (s atrapou `VideoCapture`). **Nepokrývajú** detektor YOLO, UI ani reálne pripojenie k zdrojom.

Výsledok: testy prechádzajú (35 testov, OK).

## Použité technológie

- Python, Tkinter (UI)
- OpenCV (`opencv-python`) – čítanie zdrojov, zmena veľkosti, kreslenie
- Ultralytics YOLOv8 (`yolov8n`) – detekcia objektov
- NumPy, Pillow – práca s obrazom
- `unittest` – testy

## Autor

Veronika Mukosii, TUKE, 2026
