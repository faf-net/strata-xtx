# strata-xtx

Strata für eine Radeon RX 7900 XTX unter Linux: Die Engine liest Prompts etwa doppelt so schnell, ohne einen einzigen Schalter in der Laufkonfiguration.

[English version](README.md)

Dies ist ein inoffizieller Ableger von [Strata](https://github.com/Niko1221/Strata) (MIT). Es ist kein Strata-Release, und Fragen dazu gehören hierher, nicht zum Original. Die Änderung ist klein: 207 Zeilen in fünf Dateien auf Strata v0.2.15.

## Was er tut

Stratas Engine bringt eine Reihe von Schaltern (Umgebungsvariablen) für das Einlesen des Prompts mit, die auf dieser Kartengeneration ausgeschaltet sind, weil mehrere davon die Rundung ändern. Auf neueren Karten schaltet Strata vergleichbare von selbst ein. Dieser Bau tut dasselbe für einen Fall:

- Linux, genau eine sichtbare Grafikkarte, und diese ist eine eigenständige `gfx1100`-Karte (RX 7900 XTX oder XT).
- Dann schaltet die Engine 27 ihrer eigenen Schalter ein und lässt ein bloßes `--prefill auto` Stücke bis 32.768 Token nehmen.
- Alles andere läuft wie bisher: zwei Karten, jede andere Architektur, eine integrierte Grafik, Windows.

Dazu kommen drei Dinge:

- **Die eigene Einstellung gewinnt.** Ein Schalter, den man selbst setzt, wird nie überschrieben, gleich mit welchem Wert.
- **Ein Ausweg.** `STRATA_GFX1100_DEFAULTS=0` schaltet die ganze Tabelle ab und mit ihr die Regel für die Stückgröße.
- **Selbstrettung.** Meldet die Engine nicht-endliche Werte und hilft Stratas eigener zweiter Versuch nicht, startet der Server die Engine einmal ohne die Tabelle neu und läuft im langsameren, exakten Modus weiter.

Die Engine schreibt beim Start eine Zeile mit dem Namen des Baus (`xtx-1`) und eine Zeile mit den Schaltern, die sie gesetzt hat. Ein Protokoll sagt damit immer, was gelaufen ist. `strata --version` bleibt unverändert.

## Was ich gemessen habe

Hardware: RX 7900 XTX in einem OCuLink-x4-Dock an einer UGREEN iDX6011 Pro (62 GiB RAM), Karte in meiner leisen Leistungseinstellung. Modell: Qwen3.8-Flash-Next IQ3_XXS, einmal unverändert und einmal als Variante mit Steuervektor und Bildeingang. Alle Werte gemessen am 18.11.2026; der Aufbau ist in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm) beschrieben.

Einlesen eines Prompts in Token je Sekunde (Mittel aus zwei Runden):

| Prompt | Normales Modell, Tabelle aus | Normales Modell, dieser Bau | Mit Steuervektor, dieser Bau |
|---|---:|---:|---:|
| 4K | 798 | 839 | 776 |
| 16K | 1.382 | 2.357 | 2.242 |
| 58K | 1.313 | 2.952 | 2.884 |
| 128K | – | 3.053 | 2.978 |
| 250K | – | 2.904 | 2.870 |

- **So schnell wie mit von Hand gesetzten Schaltern.** Das Release Strata 0.2.14 mit den Schaltern in der Laufkonfiguration las 840 / 2.357 / 2.952 Token je Sekunde bei 4K / 16K / 58K.
- **Das Schreiben bleibt gleich**, innerhalb der Streuung des Tests: 58 bis 63 Token je Sekunde in jeder Variante.
- **Qualität:** Mein Aufgabensatz ergibt 97 von 102 (normal) und 98 von 102 (mit Steuervektor), wie das Release. Eine versteckte Zahl wurde in jedem langen Prompt gefunden.
- **Dauerlauf:** 90 Minuten gemischte Anfragen auf dem Modell mit Steuervektor: 1.246 Anfragen, keine fehlgeschlagen, 178 von 178 versteckten Zahlen gefunden, kein nicht-endlicher Wert im Engine-Protokoll.
- **Selbstrettung:** Mit Stratas eingebauter Fehlerinjektion startete der Server die Engine einmal ohne die Tabelle neu und beantwortete die folgenden Anfragen.
- **Preis:** rund 0,6 GiB mehr Arbeitsspeicher nach dem Laden. Die Antworten sind nicht Bit für Bit gleich wie ohne die Tabelle.

Nicht gemessen habe ich: die RX 7900 XT, eine Karte in einem vollen PCIe-x16-Steckplatz, ein anderes Modell oder Quant, Windows.

## Die Schalter

`patch/gfx1100_defaults.cpp` ist die Tabelle. Ohne die Vorsilbe `STRATA_`:

- Aufmerksamkeit und Blockauswahl des Prompts auf den Matrixkernen: `HIP_WMMA`, `SELECT_WMMA`, `PA_FAST`
- Experten und Projektionen des Prompts: `PF_FUSED`, `PF_GEMM`, `PF_PAD`, `PF_F16=2`, `PF_HCDOWN`, `HC_UPMIX`, `QFUSE`, `FUSE_CONVAB`, `CVEC_FUSE`
- Die Rekurrenz des Prompts: `GDN_CHUNKED`, `GDN_HEAD`, `GDN_PP`, `GDN_CONVL2`, `GDN_NOY`
- Arbeitsteilung und Puffer: `PREFILL_CPU_SHARE=0.6`, `PREFILL_CPU_SHARE_MAX=4096`, `PREFILL_RING=192`, `STAGER_RING=64`, `KV_HOST_DMA`, `ADAPT_OVERLAP`, `SH_STREAM=0`
- Das Fenster beim Schreiben: `QSA_ROWS`, `VERIFY_QDEDUP`, `HEAD_MIX_MULTI`

Jeder davon steckt in der unveränderten Engine. Stratas Dokumentation beschreibt einen Teil; zugesichert ist keiner. Ein Release kann einen umbenennen oder streichen, und die Engine ignoriert einen unbekannten Namen stillschweigend. Deshalb teste ich jede neue Version, bevor ich sie nutze.

## Bauen

Nötig sind Docker, ein Klon von Strata und die beiden Release-Pakete derselben Version (Engine `…-linux-x86_64-hip-rx7900` und Control), entpackt nach `<paket>/engine` und `<paket>/control`. Die gebaute Engine liegt neben den ROCm-Bibliotheken des Release-Pakets.

```sh
git clone https://github.com/Niko1221/Strata.git
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata
python3 xtx_bauen.py v0.2.15 --quelle Strata --paket <paket> --ziel <ausgabe>
```

Das Ergebnis sind `<ausgabe>/engine` und `<ausgabe>/control`, zu verwenden wie die Release-Pakete. Der erste Bau dauert auf acht Kernen rund fünf Minuten, ein erneuter rund eine. Der Zweig `xtx-0.2.15` dieses Repositorys ist der gepatchte Quelltext, falls man lieber den liest oder baut.

## Eine neue Strata-Version

```sh
python3 xtx_bauen.py v0.2.16 --quelle Strata --paket <paket-0.2.16> --ziel <ausgabe>
```

`patch/anwenden.py` setzt die Änderung an Ankerzeilen des Originals ein. Fehlt ein Anker im neuen Quelltext, bricht es ab und nennt ihn, statt halb zu patchen, und es wird nichts gebaut.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `patch/` | die beiden neuen Quelldateien und `anwenden.py`, das sie in einen Strata-Quelltext einsetzt |
| `bau/` | Bau-Image und Bauskript (ROCm-7.10-Wheels für gfx110X) |
| `xtx_bauen.py` | holen, patchen, bauen, zusammenstellen |
| Zweig `xtx-<version>` | Strata an diesem Tag mit eingesetztem Patch |

## Lizenz

MIT, wie Strata. Strata ist das Werk von Niko1221 und den Strata-Mitwirkenden; siehe `LICENSE`.
