# strata-xtx

Strata für eine Radeon RX 7900 XTX unter Linux: liest lange Prompts etwa doppelt so schnell wie das offizielle Release, ohne einen einzigen Schalter in der Laufkonfiguration.

[English version](README.md)

| Gegenüber dem Release 0.2.17, auf derselben Karte gemessen | Release | strata-xtx |
|---|---:|---:|
| Prompt mit 32.000 Token einlesen | 1.352 Token/s | 2.848 Token/s |
| Prompt mit 250.000 Token einlesen | 207 s | 82 s |
| Schreiben im Chat | 67,9 Token/s | 77,7 Token/s |
| Qualität (eigener Aufgabensatz, 102 Aufgaben) | gleich | gleich |

- **Nichts einzustellen:** Die Engine erkennt die Karte und schaltet die Beschleunigung selbst ein.
- **Abgesichert:** ein Schalter zum Abschalten, und ein selbsttätiger Neustart im exakten Modus, falls die Engine nicht-endliche Werte meldet.
- **Klein und nachvollziehbar:** 207 Zeilen in fünf Dateien, als Patch und als fertiger Zweig je Strata-Version.
- **Der Preis:** Die Antworten sind nicht Bit für Bit dieselben wie beim Release, und die Karte zieht beim Einlesen 25 bis 30 W mehr. Einzelheiten unter „Was ich gemessen habe“.

**Die ganze Anlage mit allen Messungen und Diagrammen:** [faf.net/lokale-ki](https://faf.net/lokale-ki/) (English: [faf.net/local-ai](https://faf.net/local-ai/)).

Dies ist ein inoffizieller Ableger von [Strata](https://github.com/Niko1221/Strata) (MIT). Es ist kein Strata-Release, und Fragen dazu gehören hierher, nicht zum Original. Die Änderung ist klein: 207 Zeilen in fünf Dateien. Der aktuelle Stand sitzt auf Strata v0.2.17 (Zweig `xtx-0.2.17`); v0.2.16 und v0.2.15 lassen sich weiter bauen (Zweige `xtx-0.2.16`, `xtx-0.2.15`).

## Was er tut

Stratas Engine bringt eine Reihe von Schaltern (Umgebungsvariablen) für das Einlesen des Prompts mit, die auf dieser Kartengeneration ausgeschaltet sind, weil mehrere davon die Rundung ändern. Auf neueren Karten schaltet Strata vergleichbare von selbst ein. Dieser Bau tut dasselbe für einen Fall:

- Linux, genau eine sichtbare Grafikkarte, und diese ist eine eigenständige `gfx1100`-Karte (RX 7900 XTX oder XT).
- Dann gilt eine Tabelle mit 27 Schaltern der Engine. 26 davon setzt die Engine neu, einer (`PF_FUSED`) ist im Release schon an. Dazu darf ein bloßes `--prefill auto` Stücke bis 32.768 Token nehmen.
- Alles andere läuft wie bisher: zwei Karten, jede andere Architektur, eine integrierte Grafik, Windows.

Dazu kommen drei Dinge:

- **Die eigene Einstellung gewinnt.** Ein Schalter, den man selbst setzt, wird nie überschrieben, gleich mit welchem Wert.
- **Ein Ausweg.** `STRATA_GFX1100_DEFAULTS=0` schaltet die ganze Tabelle ab und mit ihr die Regel für die Stückgröße.
- **Selbstrettung.** Meldet die Engine nicht-endliche Werte und hilft Stratas eigener zweiter Versuch nicht, startet der Server die Engine einmal ohne die Tabelle neu und läuft im langsameren, exakten Modus weiter. Die Anfrage, die das auslöst, endet selbst mit einem Fehler (HTTP 503); die folgenden werden beantwortet. `STRATA_GFX1100_RESCUE=0` im `env` der Laufkonfiguration schaltet diesen Neustart ab.

Die Engine schreibt beim Start eine Zeile mit dem Namen des Baus (`xtx-2`; `xtx-1` war dieselbe Tabelle auf 0.2.15 und 0.2.16 mit einem Einlesepuffer von 192 statt 384) und eine Zeile mit den Schaltern, die sie gesetzt hat. Ein Protokoll sagt damit immer, was gelaufen ist. `strata --version` bleibt unverändert.

## Was ich gemessen habe

Hardware: RX 7900 XTX in einem OCuLink-x4-Dock an einer UGREEN iDX6011 Pro (62 GiB RAM), Karte in meiner leisen Leistungseinstellung. Modell: Qwen3.8-Flash-Next IQ3_XXS, einmal unverändert und einmal als Variante mit Steuervektor und Bildeingang. Alle Werte sind am 20. und 21.11.2026 auf Strata 0.2.17 gemessen, wo nichts anderes dabeisteht; der Aufbau ist in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm) beschrieben.

Einlesen eines frischen Prompts in Token je Sekunde (Median aus zwei bis drei Läufen):

| Prompt-Token | Normales Modell | Mit Steuervektor | Dauer, normales Modell |
|---|---:|---:|---:|
| 4.077 | 1.511 | 1.505 | 2,7 s |
| 16.254 | 2.478 | 2.366 | 6,6 s |
| 65.025 | 3.193 | 3.214 | 20,4 s |
| 130.026 | 3.103 | 3.252 | 41,9 s |
| 248.054 | 3.093 | 3.128 | 80,2 s |

Gegen das unveränderte Release 0.2.17, im Wechsel gemessen (Stratas `tools/strata_bench.py --long`, drei Runden, jede Engine frisch geladen, normales Modell):

| Median | Release 0.2.17 | Dieser Bau |
|---|---:|---:|
| Prompt 4K, Token/s | 785 | 1.576 |
| Prompt 16K, Token/s | 1.390 | 2.481 |
| Prompt 32K, Token/s | 1.352 | 2.848 |
| Schreiben im Chat, Token/s | 67,9 | 77,7 |
| Schreiben im Agent-Test, Token/s | 72,1 | 80,9 |

- **Die Tabelle ist der ganze Unterschied.** Derselbe Bau mit `STRATA_GFX1100_DEFAULTS=0` liest 16K mit rund 1.425 und 58K mit rund 1.303 Token je Sekunde, mit der Tabelle 2.586 / 2.581 und 3.268 / 3.171.
- **Ein Prompt von 250.000 Token:** 82 bis 84 s mit diesem Bau (3.003 bis 3.065 Token je Sekunde, beide Modelle), 207 s auf dem unveränderten Release (1.216 Token je Sekunde). Die im Prompt versteckte Zahl wurde jedes Mal gefunden.
- **Schreiben: gleich bis schneller.** Im Wechselvergleich lag dieser Bau in allen drei Runden über dem Release, im Chat-Teil um 5 bis 15 %, im Agent-Teil um 8 bis 13 %. Nach langen Prompts und beim Dauerschreiben sehe ich keinen solchen Gewinn (57 bis 63 und 64 bis 70 Token je Sekunde); bei langen Antworten schrieb die Variante mit Steuervektor sogar etwas langsamer als auf 0.2.16 (64,3 gegen 67,4), das beobachte ich weiter.
- **Qualität:** Mein Aufgabensatz ergibt auf 0.2.17 95 von 102 (normal) und 97 (mit Steuervektor); auf 0.2.16 waren es 97 und 96, auf 0.2.15 97 und 98. Auf dem unveränderten Release 0.2.16 war es dasselbe wie auf diesem Bau: Einzelne Aufgaben besteht das Modell mal ja, mal nein, auf beiden Fassungen (je fünfmal wiederholt).
- **Dauerlauf:** 90 Minuten gemischte Anfragen auf dem Modell mit Steuervektor: 1.267 Anfragen, keine fehlgeschlagen, 181 von 181 versteckten Zahlen gefunden, kein nicht-endlicher Wert im Engine-Protokoll.
- **Selbstrettung:** Mit Stratas eingebauter Fehlerinjektion endete die auslösende Anfrage mit einem Fehler (HTTP 503), der Server startete die Engine einmal ohne die Tabelle neu und beantwortete die folgenden Anfragen, mit beiden Modellen. Ein Prompt von 16K wurde danach mit rund 1.300 Token je Sekunde gelesen, also im langsamen Modus, und die Zahl gefunden.
- **Strom:** Beim Einlesen zieht die Karte mit der Tabelle 25 bis 30 W mehr (292 bis 300 W gegen 267 bis 270 W, am 18.11.2026 gegen das Release 0.2.14 gemessen). Weil das Einlesen halb so lange dauert, ist die Energie je gelesenem Token trotzdem rund halb so hoch: 0,037 bis 0,047 gegen 0,070 bis 0,087 Wh je 1.000 Token. Beim Schreiben ist die Leistung gleich.
- **Preis:** Die Antworten sind nicht Bit für Bit gleich wie ohne die Tabelle. Dazu kommen rund 0,6 GiB mehr Arbeitsspeicher nach dem Laden; das habe ich am 18.11.2026 mit denselben Schaltern auf dem Release 0.2.14 gemessen und auf 0.2.16 und 0.2.17 nicht neu aufgeschlüsselt.
- **Frühere Basen:** Als `xtx-1` (Puffer 192) las der Patch auf Strata 0.2.16 (19.11.2026) bei 16K 2.404 und 2.290, bei 248K 2.907 und 2.890 Token je Sekunde, auf 0.2.15 (18.11.) 2.345 und 2.248 / 2.906 und 2.847. Ab 65K liest `xtx-2` 5 bis 11 % mehr; das schreibe ich dem größeren Puffer zu, es ist aber je Bau eine Messreihe, kein Vergleich im Wechsel.

Nicht gemessen habe ich: die RX 7900 XT, eine Karte in einem vollen PCIe-x16-Steckplatz, ein anderes Modell oder Quant, Windows.

## Die Schalter

`patch/gfx1100_defaults.cpp` ist die Tabelle. Ohne die Vorsilbe `STRATA_`:

- Aufmerksamkeit und Blockauswahl des Prompts auf den Matrixkernen: `HIP_WMMA`, `SELECT_WMMA`, `PA_FAST`
- Experten und Projektionen des Prompts: `PF_FUSED`, `PF_GEMM`, `PF_PAD`, `PF_F16=2`, `PF_HCDOWN`, `HC_UPMIX`, `QFUSE`, `FUSE_CONVAB`, `CVEC_FUSE`
- Die Rekurrenz des Prompts: `GDN_CHUNKED`, `GDN_HEAD`, `GDN_PP`, `GDN_CONVL2`, `GDN_NOY`
- Arbeitsteilung und Puffer: `PREFILL_CPU_SHARE=0.6`, `PREFILL_CPU_SHARE_MAX=4096`, `PREFILL_RING=384`, `STAGER_RING=64`, `KV_HOST_DMA`, `ADAPT_OVERLAP`, `SH_STREAM=0`
- Das Fenster beim Schreiben: `QSA_ROWS`, `VERIFY_QDEDUP`, `HEAD_MIX_MULTI`

Jeder davon steckt in der unveränderten Engine. Stratas Dokumentation beschreibt einen Teil; zugesichert ist keiner. Ein Release kann einen umbenennen oder streichen, und die Engine ignoriert einen unbekannten Namen stillschweigend. Deshalb teste ich jede neue Version, bevor ich sie nutze.

## Bauen

Nötig sind Docker, ein Klon von Strata und die beiden Release-Pakete derselben Version (Engine `…-linux-x86_64-hip-rx7900` und Control), entpackt nach `<paket>/engine` und `<paket>/control`. Die gebaute Engine liegt neben den ROCm-Bibliotheken des Release-Pakets.

```sh
git clone https://github.com/Niko1221/Strata.git
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata/terminal
python3 xtx_bauen.py v0.2.17 --quelle Strata --paket <paket> --ziel <ausgabe>
```

Das Ergebnis sind `<ausgabe>/engine` und `<ausgabe>/control`, zu verwenden wie die Release-Pakete. `xtx_bauen.py` legt im Klon den Zweig `xtx-<version>` an und schreibt den Patch dort als Commit hinein; Git braucht dafür im Klon einen Namen und eine E-Mail-Adresse (`git config user.name`, `user.email`). Die Zweige `xtx-0.2.17`, `xtx-0.2.16` und `xtx-0.2.15` dieses Repositorys sind der gepatchte Quelltext, falls man lieber den liest oder baut.

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
