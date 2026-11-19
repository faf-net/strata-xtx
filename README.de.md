# strata-xtx

Strata für eine Radeon RX 7900 XTX unter Linux: Die Engine liest Prompts etwa doppelt so schnell, ohne einen einzigen Schalter in der Laufkonfiguration.

[English version](README.md)

Dies ist ein inoffizieller Ableger von [Strata](https://github.com/Niko1221/Strata) (MIT). Es ist kein Strata-Release, und Fragen dazu gehören hierher, nicht zum Original. Die Änderung ist klein: rund 200 Zeilen in fünf Dateien. Der aktuelle Stand sitzt auf Strata v0.2.16 (Zweig `xtx-0.2.16`); v0.2.15 lässt sich weiter bauen (Zweig `xtx-0.2.15`).

## Was er tut

Stratas Engine bringt eine Reihe von Schaltern (Umgebungsvariablen) für das Einlesen des Prompts mit, die auf dieser Kartengeneration ausgeschaltet sind, weil mehrere davon die Rundung ändern. Auf neueren Karten schaltet Strata vergleichbare von selbst ein. Dieser Bau tut dasselbe für einen Fall:

- Linux, genau eine sichtbare Grafikkarte, und diese ist eine eigenständige `gfx1100`-Karte (RX 7900 XTX oder XT).
- Dann gilt eine Tabelle mit 27 Schaltern der Engine. 26 davon setzt die Engine neu, einer (`PF_FUSED`) ist im Release schon an. Dazu darf ein bloßes `--prefill auto` Stücke bis 32.768 Token nehmen.
- Alles andere läuft wie bisher: zwei Karten, jede andere Architektur, eine integrierte Grafik, Windows.

Dazu kommen drei Dinge:

- **Die eigene Einstellung gewinnt.** Ein Schalter, den man selbst setzt, wird nie überschrieben, gleich mit welchem Wert.
- **Ein Ausweg.** `STRATA_GFX1100_DEFAULTS=0` schaltet die ganze Tabelle ab und mit ihr die Regel für die Stückgröße.
- **Selbstrettung.** Meldet die Engine nicht-endliche Werte und hilft Stratas eigener zweiter Versuch nicht, startet der Server die Engine einmal ohne die Tabelle neu und läuft im langsameren, exakten Modus weiter. Die Anfrage, die das auslöst, endet selbst mit einem Fehler (HTTP 503); die folgenden werden beantwortet. `STRATA_GFX1100_RESCUE=0` im `env` der Laufkonfiguration schaltet diesen Neustart ab.

Die Engine schreibt beim Start eine Zeile mit dem Namen des Baus (`xtx-1`) und eine Zeile mit den Schaltern, die sie gesetzt hat. Ein Protokoll sagt damit immer, was gelaufen ist. `strata --version` bleibt unverändert.

## Was ich gemessen habe

Hardware: RX 7900 XTX in einem OCuLink-x4-Dock an einer UGREEN iDX6011 Pro (62 GiB RAM), Karte in meiner leisen Leistungseinstellung. Modell: Qwen3.8-Flash-Next IQ3_XXS, einmal unverändert und einmal als Variante mit Steuervektor und Bildeingang. Alle Werte sind am 18. und 19.11.2026 auf Strata 0.2.16 gemessen, wo nichts anderes dabeisteht; der Aufbau ist in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm) beschrieben.

Einlesen eines frischen Prompts in Token je Sekunde (Median aus zwei bis drei Läufen):

| Prompt-Token | Normales Modell | Mit Steuervektor | Dauer, normales Modell |
|---|---:|---:|---:|
| 4.077 | 1.470 | 1.438 | 2,8 s |
| 16.254 | 2.404 | 2.290 | 6,8 s |
| 65.025 | 3.021 | 2.925 | 21,5 s |
| 130.026 | 2.968 | 2.933 | 43,8 s |
| 248.054 | 2.907 | 2.890 | 85,4 s |

Gegen das unveränderte Release 0.2.16, im Wechsel gemessen (Stratas `tools/strata_bench.py --long`, drei Runden, jede Engine frisch geladen, normales Modell):

| Median | Release 0.2.16 | Dieser Bau |
|---|---:|---:|
| Prompt 4K, Token/s | 783 | 1.645 |
| Prompt 16K, Token/s | 1.357 | 2.295 |
| Prompt 32K, Token/s | 1.321 | 2.650 |
| Schreiben im Chat, Token/s | 69,6 | 72,5 |
| Schreiben im Agent-Test, Token/s | 72,3 | 81,7 |

- **Die Tabelle ist der ganze Unterschied.** Derselbe Bau mit `STRATA_GFX1100_DEFAULTS=0` liest 16K mit rund 1.390 und 58K mit rund 1.320 Token je Sekunde, mit der Tabelle 2.386 / 2.367 und 3.021 / 2.982.
- **Ein Prompt von 250.000 Token:** 85 bis 87 s mit diesem Bau (2.838 bis 2.917 Token je Sekunde, beide Modelle), 204 s auf dem unveränderten Release (1.220 Token je Sekunde, mit Steuervektor). Die im Prompt versteckte Zahl wurde jedes Mal gefunden.
- **Schreiben: gleich bis leicht schneller.** Im Wechselvergleich lag dieser Bau im Chat-Teil in allen drei Runden etwas über dem Release, im Agent-Teil in zwei von drei. Nach langen Prompts und beim Dauerschreiben sehe ich keinen Unterschied (51 bis 59 und 67 bis 68 Token je Sekunde).
- **Qualität:** Mein Aufgabensatz ergibt 97 von 102 (normal) und 96 bis 98 von 102 je nach Lauf (mit Steuervektor). Auf dem unveränderten Release ist es dasselbe: Zwei Aufgaben besteht das Modell mal ja, mal nein, auf beiden Fassungen (je fünfmal wiederholt).
- **Dauerlauf:** 90 Minuten gemischte Anfragen auf dem Modell mit Steuervektor: 1.232 Anfragen, keine fehlgeschlagen, 176 von 176 versteckten Zahlen gefunden, kein nicht-endlicher Wert im Engine-Protokoll.
- **Selbstrettung:** Mit Stratas eingebauter Fehlerinjektion endete die auslösende Anfrage mit einem Fehler (HTTP 503), der Server startete die Engine einmal ohne die Tabelle neu und beantwortete die folgenden Anfragen, mit beiden Modellen. Ein Prompt von 16K wurde danach mit rund 1.300 Token je Sekunde gelesen, also im langsamen Modus, und die Zahl gefunden.
- **Strom:** Beim Einlesen zieht die Karte mit der Tabelle 25 bis 30 W mehr (292 bis 300 W gegen 267 bis 270 W, am 18.11.2026 gegen das Release 0.2.14 gemessen). Weil das Einlesen halb so lange dauert, ist die Energie je gelesenem Token trotzdem rund halb so hoch: 0,037 bis 0,047 gegen 0,070 bis 0,087 Wh je 1.000 Token. Beim Schreiben ist die Leistung gleich.
- **Preis:** Die Antworten sind nicht Bit für Bit gleich wie ohne die Tabelle. Dazu kommen rund 0,6 GiB mehr Arbeitsspeicher nach dem Laden; das habe ich am 18.11.2026 mit denselben Schaltern auf dem Release 0.2.14 gemessen und auf 0.2.16 nicht neu aufgeschlüsselt.
- **Auf Strata 0.2.15** las derselbe Patch am 18.11.2026 gleich schnell (16K: 2.345 und 2.248, 248K: 2.906 und 2.847 Token je Sekunde).

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
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata/terminal
python3 xtx_bauen.py v0.2.16 --quelle Strata --paket <paket> --ziel <ausgabe>
```

Das Ergebnis sind `<ausgabe>/engine` und `<ausgabe>/control`, zu verwenden wie die Release-Pakete. `xtx_bauen.py` legt im Klon den Zweig `xtx-<version>` an und schreibt den Patch dort als Commit hinein; Git braucht dafür im Klon einen Namen und eine E-Mail-Adresse (`git config user.name`, `user.email`). Die Zweige `xtx-0.2.16` und `xtx-0.2.15` dieses Repositorys sind der gepatchte Quelltext, falls man lieber den liest oder baut.

Seit v0.2.16 hat Strata eine neue Ordnerstruktur: Die Engine liegt unter `engine/`, der Server unter `terminal/`. `patch/anwenden.py`, `bau/bauen.sh` und `xtx_bauen.py` erkennen beide Strukturen selbst. Nur das Bau-Image braucht den richtigen Ordner, weil es Stratas `requirements.txt` einliest: ab v0.2.16 `Strata/terminal`, bis v0.2.15 `Strata`. Das Image enthält nur Werkzeuge und lässt sich für beide Versionen verwenden.

## Eine neue Strata-Version

```sh
python3 xtx_bauen.py v<neu> --quelle Strata --paket <paket-neu> --ziel <ausgabe>
```

`patch/anwenden.py` setzt die Änderung an Ankerzeilen des Originals ein. Fehlt ein Anker im neuen Quelltext, bricht es ab und nennt ihn, statt halb zu patchen, und es wird nichts gebaut.

Ein Release kann mehr ändern als Ankerzeilen. Mit v0.2.16 sind die Ordner umgezogen, und Bauoptionen sind entfallen; beides musste ich im Bauskript nachziehen. Nach jedem Wechsel messe ich deshalb neu, bevor ich den Bau nutze: Tempo mit und ohne Tabelle, den Aufgabensatz und die Selbstrettung mit beiden Modellen, dazu einen Dauerlauf.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `patch/` | die beiden neuen Quelldateien und `anwenden.py`, das sie in einen Strata-Quelltext einsetzt |
| `bau/` | Bau-Image und Bauskript (ROCm-7.10-Wheels für gfx110X) |
| `xtx_bauen.py` | holen, patchen, bauen, zusammenstellen |
| Zweig `xtx-<version>` | Strata am Tag `v<version>` mit eingesetztem Patch |

## Lizenz

MIT, wie Strata. Strata ist das Werk von Niko1221 und den Strata-Mitwirkenden; siehe `LICENSE`.
