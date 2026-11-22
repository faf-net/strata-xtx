# strata-xtx

Strata für eine Radeon RX 7900 XTX unter Linux: liest lange Prompts etwa doppelt so schnell wie das offizielle Release, ohne einen einzigen Schalter in der Laufkonfiguration.

[English version](README.md)

| Gegenüber dem Release 0.2.19, auf derselben Karte gemessen | Release | strata-xtx `0.2.19-xtx3` |
|---|---:|---:|
| Prompt mit 32.000 Token einlesen | 1.472 Token/s | **3.054 Token/s** |
| Prompt mit 250.000 Token einlesen | 177 s | **78 s** |
| Schreiben im Chat | 70,6 Token/s | 75,3 Token/s |
| Schreiben im Agent-Test | 75,9 Token/s | **81,7 Token/s** |
| Qualität (eigener Aufgabensatz, 102 Aufgaben) | gleich | gleich |

**Neu mit 0.2.19:** Strata 0.2.19 bringt eigene Voreinstellungen für RDNA3-Karten mit und mit ihnen einen RAM-Wächter, der die Prompt-Stücke klein hält, solange nicht 6 GiB RAM frei bleiben. Mit einem 125B-Modell auf einer Maschine mit 64 GB ist das nie der Fall, also liest 0.2.19 lange Prompts in Stücken von 8K. Der bisherige Bau, unverändert auf 0.2.19 angewandt, las einen Prompt von 58K mit 1.497 statt 3.206 Token/s. `0.2.19-xtx3` nimmt Stratas eigenen Schalter `STRATA_GFX11_CHUNK=1` in die Tabelle auf und liest ihn mit 3.433, 7 % schneller als bisher. Einzelheiten unter [Strata 0.2.19 und sein RAM-Wächter](#strata-0219-und-sein-ram-wächter).

- **Nichts einzustellen:** Die Engine erkennt die Karte und schaltet die Beschleunigung selbst ein.
- **Abgesichert:** ein Schalter zum Abschalten, und ein selbsttätiger Neustart im exakten Modus, falls die Engine nicht-endliche Werte meldet.
- **Klein und nachvollziehbar:** 215 Zeilen in fünf Dateien, als Patch und als fertiger Zweig je Strata-Version.
- **Der Preis:** Die Antworten sind nicht Bit für Bit dieselben wie beim Release, und die Karte zieht beim Einlesen 25 bis 30 W mehr. Einzelheiten unter „Was ich gemessen habe“.

**Die ganze Anlage mit allen Messungen und Diagrammen:** [faf.net/lokale-ki](https://faf.net/lokale-ki/) (English: [faf.net/local-ai](https://faf.net/local-ai/)).

Dies ist ein inoffizieller Ableger von [Strata](https://github.com/Niko1221/Strata) (MIT). Es ist kein Strata-Release, und Fragen dazu gehören hierher, nicht zum Original. Die Änderung ist klein: 215 Zeilen in fünf Dateien. Der aktuelle Stand ist `0.2.19-xtx3` auf Strata v0.2.19 (Zweig `xtx-0.2.19`); v0.2.18, v0.2.17, v0.2.16 und v0.2.15 lassen sich mit dem damaligen Patch weiter bauen (Zweige `xtx-0.2.18` bis `xtx-0.2.15`). Die Bauten heißen `<Strata-Release>-xtx<Patchstand>`; die Zahl hinter xtx steigt nur, wenn sich der Patch selbst ändert.

## Was er tut

Stratas Engine bringt eine Reihe von Schaltern (Umgebungsvariablen) für das Einlesen des Prompts mit, die auf dieser Kartengeneration ausgeschaltet sind, weil mehrere davon die Rundung ändern. Auf neueren Karten schaltet Strata vergleichbare von selbst ein. Dieser Bau tut dasselbe für einen Fall:

- Linux, genau eine sichtbare Grafikkarte, und diese ist eine eigenständige `gfx1100`-Karte (RX 7900 XTX oder XT).
- Dann gilt eine Tabelle mit 28 Schaltern der Engine. 27 davon setzt die Engine neu, einer (`PF_FUSED`) ist im Release schon an. Dazu darf ein bloßes `--prefill auto` Stücke bis 32.768 Token nehmen; ab 0.2.19 sorgt Stratas eigenes `STRATA_GFX11_CHUNK=1` in der Tabelle dafür, dass sein RAM-Wächter sie nicht wieder verkleinert.
- Alles andere läuft wie bisher: zwei Karten, jede andere Architektur, eine integrierte Grafik, Windows.
- Die Tabelle gehört nur zu Stratas Haupt-Engine. Die eigenen Engines für Tencent Hy4-Flash (`strata-hy4`, seit 0.2.18, [gemessen](https://github.com/faf-net/ugreen-idx6011-egpu-llm/blob/main/messen/daten/2026-11-22-hy4-flash/README.de.md)) und Inkling 2 Mini (`strata-inkling`, seit 0.2.19) lesen keinen dieser Schalter; an ihnen ändert dieser Bau also nichts.

Dazu kommen drei Dinge:

- **Die eigene Einstellung gewinnt.** Ein Schalter, den man selbst setzt, wird nie überschrieben, gleich mit welchem Wert.
- **Ein Ausweg.** `STRATA_GFX1100_DEFAULTS=0` schaltet die ganze Tabelle ab und mit ihr die Regel für die Stückgröße.
- **Selbstrettung.** Meldet die Engine nicht-endliche Werte und hilft Stratas eigener zweiter Versuch nicht, startet der Server die Engine einmal ohne die Tabelle (und ab 0.2.19 ohne Stratas eigene RDNA3-Voreinstellungen, `STRATA_GFX11_DEFAULTS=0`) neu und läuft im langsameren, exakten Modus weiter. Die Anfrage, die das auslöst, endet selbst mit einem Fehler (HTTP 503); die folgenden werden beantwortet. `STRATA_GFX1100_RESCUE=0` im `env` der Laufkonfiguration schaltet diesen Neustart ab.

Die Engine schreibt beim Start eine Zeile mit dem Namen des Baus (`0.2.19-xtx3`; davor `xtx-2` auf 0.2.17 und 0.2.18, `xtx-1` auf 0.2.15 und 0.2.16 mit einem Einlesepuffer von 192 statt 384) und eine Zeile mit den Schaltern, die sie gesetzt hat. Ein Protokoll sagt damit immer, was gelaufen ist. `strata --version` bleibt unverändert.

## Was ich gemessen habe

Hardware: RX 7900 XTX in einem OCuLink-x4-Dock an einer UGREEN iDX6011 Pro (62 GiB RAM), Karte in meiner leisen Leistungseinstellung. Modell: Qwen3.8-Flash-Next IQ3_XXS, einmal unverändert und einmal als Variante mit Steuervektor und Bildeingang. Alle Werte sind am 22.11.2026 auf Strata 0.2.19 (`0.2.19-xtx3`) gemessen, wo nichts anderes dabeisteht; der Aufbau ist in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm) beschrieben.

Einlesen eines frischen Prompts in Token je Sekunde (Median aus zwei bis drei Läufen):

| Prompt-Token | Normales Modell | Mit Steuervektor | Dauer, normales Modell |
|---|---:|---:|---:|
| 4.077 | 1.555 | 1.460 | 2,6 s |
| 16.254 | 2.538 | 2.400 | 6,4 s |
| 65.025 | 3.439 | 3.469 | 18,9 s |
| 130.026 | 3.379 | 3.480 | 38,5 s |
| 248.054 | 3.324 | 3.381 | 74,6 s |

Gegen das unveränderte Release 0.2.19, im Wechsel gemessen (Stratas `tools/strata_bench.py --long`, drei Runden, jede Engine frisch geladen, normales Modell):

| Median | Release 0.2.19 | Dieser Bau |
|---|---:|---:|
| Prompt 4K, Token/s | 847 | 1.615 |
| Prompt 16K, Token/s | 1.510 | 2.528 |
| Prompt 32K, Token/s | 1.472 | 3.054 |
| Schreiben im Chat, Token/s | 70,6 | 75,3 |
| Schreiben im Agent-Test, Token/s | 75,9 | 81,7 |

- **Die Tabelle ist der ganze Unterschied.** Derselbe Bau mit `STRATA_GFX1100_DEFAULTS=0` liest 16K mit 1.511 und 58K mit 1.430 Token je Sekunde, mit der Tabelle 2.537 und 3.433 (Median aus zwei Runden zu je zwei Läufen).
- **Ein Prompt von 250.000 Token:** 77 bis 78 s mit diesem Bau (beide Modelle), 177 s auf dem unveränderten Release. Der Prompt des Aufgabensatzes mit 247.954 Token brauchte 73 bis 74 s (3.346 bis 3.393 Token je Sekunde). Die im Prompt versteckte Zahl wurde jedes Mal gefunden.
- **Schreiben: gleich bis schneller.** Im Wechselvergleich lag dieser Bau im Chat-Teil 7 % und im Agent-Teil 8 % über dem Release; bei voller Kartenleistung lief der Agent-Teil mit 90,9 gegen 79,5 Token je Sekunde. Nach langen Prompts und beim Dauerschreiben schreibt er mit 58 bis 65 und 65 bis 69 Token je Sekunde; Vergleichswerte des Release gibt es dafür auf 0.2.19 nicht.
- **Qualität:** Mein Aufgabensatz ergibt auf 0.2.19 98 von 102 (normal) und 97 (mit Steuervektor); auf 0.2.18 waren es 96 und 97, auf 0.2.17 95 und 97, auf 0.2.16 97 und 96, auf 0.2.15 97 und 98. Auf dem unveränderten Release 0.2.16 war es dasselbe wie auf diesem Bau: Einzelne Aufgaben besteht das Modell mal ja, mal nein, auf beiden Fassungen (je fünfmal wiederholt). Einen Unterschied von wenigen Punkten kann ein Satz von 102 Aufgaben allerdings nicht zeigen; ein größerer gepaarter Vergleich mit dem Release steht noch aus.
- **Dauerlauf:** 90 Minuten gemischte Anfragen auf dem Modell mit Steuervektor: 1.316 Anfragen, keine fehlgeschlagen, 188 von 188 versteckten Zahlen gefunden, kein nicht-endlicher Wert im Engine-Protokoll.
- **Selbstrettung:** Mit Stratas eingebauter Fehlerinjektion endete die auslösende Anfrage mit einem Fehler (HTTP 503), der Server startete die Engine einmal ohne die Tabelle neu und beantwortete die folgenden Anfragen, auf 0.2.17 mit beiden Modellen, auf 0.2.18 und 0.2.19 mit dem Modell mit Steuervektor. Ein Prompt von 16K wurde danach mit rund 1.300 Token je Sekunde gelesen, also im langsamen Modus, und die Zahl gefunden.
- **Strom:** Beim Einlesen zieht die Karte mit der Tabelle 25 bis 30 W mehr (292 bis 300 W gegen 267 bis 270 W, am 18.11.2026 gegen das Release 0.2.14 gemessen). Weil das Einlesen halb so lange dauert, ist die Energie je gelesenem Token trotzdem rund halb so hoch: 0,037 bis 0,047 gegen 0,070 bis 0,087 Wh je 1.000 Token. Beim Schreiben ist die Leistung gleich.
- **Preis:** Die Antworten sind nicht Bit für Bit gleich wie ohne die Tabelle. Dazu kommen rund 0,6 GiB mehr Arbeitsspeicher nach dem Laden; das habe ich am 18.11.2026 mit denselben Schaltern auf dem Release 0.2.14 gemessen und auf späteren Versionen nicht neu aufgeschlüsselt.
- **Frühere Basen:** Als `xtx-1` (Puffer 192) las der Patch auf Strata 0.2.16 (19.11.2026) bei 16K 2.404 und 2.290, bei 248K 2.907 und 2.890 Token je Sekunde, auf 0.2.15 (18.11.) 2.345 und 2.248 / 2.906 und 2.847. Als `xtx-2` auf 0.2.17 (21.11.) las er 2.478 und 2.366 / 3.093 und 3.128, auf 0.2.18 (22.11.) 2.486 und 2.366 / 3.075 und 3.172. Ab 65K liest `xtx-2` 5 bis 11 % mehr als `xtx-1`; das schreibe ich dem größeren Puffer zu, es ist aber je Bau eine Messreihe, kein Vergleich im Wechsel. `0.2.19-xtx3` liest ab 64K 7 bis 10 % mehr als `xtx-2` auf 0.2.18.

Nicht gemessen habe ich: die RX 7900 XT, eine Karte in einem vollen PCIe-x16-Steckplatz, ein anderes Modell oder Quant, Windows.

## Strata 0.2.19 und sein RAM-Wächter

Strata 0.2.19 hat eigene Voreinstellungen für eigenständige RDNA3-Karten bekommen (`engine/include/strata/core/gfx11_extra.hpp`), darunter eine Regel, die Prompt-Stücke bis 32K Token erlaubt. Mit dieser Regel schaltet sich aber auch ein RAM-Wächter ein, der als Abhilfe für [#2090](https://github.com/Niko1221/Strata/issues/2090) kam: Größere Stücke nimmt er nur, wenn der zusätzliche Leihspeicher plus 6 GiB in den verfügbaren RAM passt. Mit geladenem normalem Modell hatte meine Maschine 7,7 GiB verfügbar, 32K-Stücke brauchen 9,2 GiB mehr, also ging der Wächter auf 8K-Stücke zurück (16K mit der Variante mit Steuervektor). Welche Stückgröße die Engine genommen hat, steht in ihrem Protokoll.

| Einlesen, Token/s | 16K, normal | 58K, normal | 128K, mit Steuervektor |
|---|---:|---:|---:|
| bisheriger Bau `0.2.18-xtx2` | 2.510 | 3.206 | 3.292 |
| Release 0.2.19 wie geliefert | 1.511 | 1.430 | – |
| bisheriger Patch unverändert auf 0.2.19 | 1.586 (−37 %) | 1.497 (−53 %) | 2.657 (−19 %) |
| Release 0.2.19 mit `STRATA_GFX11_CHUNK=1` (ein Lauf) | 1.851 | 2.550 | 2.718 |
| **`0.2.19-xtx3`** | **2.537 (+1 %)** | **3.433 (+7 %)** | **3.516 (+7 %)** |

Median aus zwei Runden zu je zwei Läufen, 22.11.2026. `STRATA_GFX11_CHUNK=1` ist Stratas eigener Weg, die Obergrenze von 32K zu behalten; `0.2.19-xtx3` trägt ihn in der Tabelle, also liest der Bau wie bisher und etwas schneller. Der Wächter soll das Auslagern verhindern: Mit `0.2.19-xtx3` blieb der kleinste verfügbare RAM beim Einlesen, wo er auf 0.2.18 lag (3,5 gegen 3,6 GiB normal, 5,2 gegen 5,5 GiB mit Steuervektor), der Swap bewegte sich nicht, und der 90-Minuten-Dauerlauf hatte keinen Fehler. Auf einer Maschine mit weniger Spielraum kann der Wächter recht haben; `STRATA_GFX11_CHUNK` mit einem anderen Wert in der eigenen Konfiguration gewinnt gegen die Tabelle. Das Release allein mit dem Schalter liest weiter langsamer als dieser Bau, weil sein Einlesepuffer 96 statt 384 Plätze hat.

Rohdaten: [`messen/daten/2026-11-22-strata-xtx-0.2.19/`](https://github.com/faf-net/ugreen-idx6011-egpu-llm/tree/main/messen/daten/2026-11-22-strata-xtx-0.2.19) im Repository der Anlage.

## Die Schalter

`patch/gfx1100_defaults.cpp` ist die Tabelle. Ohne die Vorsilbe `STRATA_`:

- Aufmerksamkeit und Blockauswahl des Prompts auf den Matrixkernen: `HIP_WMMA`, `SELECT_WMMA`, `PA_FAST`
- Experten und Projektionen des Prompts: `PF_FUSED`, `PF_GEMM`, `PF_PAD`, `PF_F16=2`, `PF_HCDOWN`, `HC_UPMIX`, `QFUSE`, `FUSE_CONVAB`, `CVEC_FUSE`
- Die Rekurrenz des Prompts: `GDN_CHUNKED`, `GDN_HEAD`, `GDN_PP`, `GDN_CONVL2`, `GDN_NOY`
- Arbeitsteilung und Puffer: `PREFILL_CPU_SHARE=0.6`, `PREFILL_CPU_SHARE_MAX=4096`, `PREFILL_RING=384`, `STAGER_RING=64`, `KV_HOST_DMA`, `ADAPT_OVERLAP`, `SH_STREAM=0`
- Das Fenster beim Schreiben: `QSA_ROWS`, `VERIFY_QDEDUP`, `HEAD_MIX_MULTI`
- Stratas eigene Obergrenze der Stückgröße für RDNA3 (ab 0.2.19): `GFX11_CHUNK=1`

Jeder davon steckt in der unveränderten Engine. Stratas Dokumentation beschreibt einen Teil; zugesichert ist keiner. Ein Release kann einen umbenennen oder streichen, und die Engine ignoriert einen unbekannten Namen stillschweigend. Deshalb teste ich jede neue Version, bevor ich sie nutze.

## Bauen

Nötig sind Docker, ein Klon von Strata und die beiden Release-Pakete derselben Version (Engine `…-linux-x86_64-hip-rx7900` und Control), entpackt nach `<paket>/engine` und `<paket>/control`. Die gebaute Engine liegt neben den ROCm-Bibliotheken des Release-Pakets.

```sh
git clone https://github.com/Niko1221/Strata.git
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata/terminal
python3 xtx_bauen.py v0.2.19 --quelle Strata --paket <paket> --ziel <ausgabe>
```

Das Ergebnis sind `<ausgabe>/engine` und `<ausgabe>/control`, zu verwenden wie die Release-Pakete. `xtx_bauen.py` legt im Klon den Zweig `xtx-<version>` an und schreibt den Patch dort als Commit hinein; Git braucht dafür im Klon einen Namen und eine E-Mail-Adresse (`git config user.name`, `user.email`). Die Zweige `xtx-0.2.19` bis `xtx-0.2.15` dieses Repositorys sind der gepatchte Quelltext, falls man lieber den liest oder baut.

Seit v0.2.16 hat Strata eine neue Ordnerstruktur: Die Engine liegt unter `engine/`, der Server unter `terminal/`. `patch/anwenden.py`, `bau/bauen.sh` und `xtx_bauen.py` erkennen beide Strukturen selbst. Nur das Bau-Image braucht den richtigen Ordner, weil es Stratas `requirements.txt` einliest: ab v0.2.16 `Strata/terminal`, bis v0.2.15 `Strata`. Das Image enthält nur Werkzeuge und lässt sich für beide Versionen verwenden.

## Eine neue Strata-Version

```sh
python3 xtx_bauen.py v<neu> --quelle Strata --paket <paket-neu> --ziel <ausgabe>
```

`patch/anwenden.py` setzt die Änderung an Ankerzeilen des Originals ein. Fehlt ein Anker im neuen Quelltext, bricht es ab und nennt ihn, statt halb zu patchen, und es wird nichts gebaut.

Ein Release kann mehr ändern als Ankerzeilen. Mit v0.2.16 sind die Ordner umgezogen, und Bauoptionen sind entfallen; beides musste ich im Bauskript nachziehen. Nach jedem Wechsel messe ich deshalb neu, bevor ich den Bau nutze: Tempo mit und ohne Tabelle, den Aufgabensatz und die Selbstrettung mit beiden Modellen, dazu einen Dauerlauf. Warum, zeigt v0.2.19: Der Patch ließ sich sauber anwenden, und der Bau bestand seine schnellen Prüfungen, las lange Prompts aber nur mit halbem Tempo. Erst der Vergleich mit dem laufenden Bau hat das gezeigt.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `patch/` | die beiden neuen Quelldateien und `anwenden.py`, das sie in einen Strata-Quelltext einsetzt |
| `bau/` | Bau-Image und Bauskript (ROCm-7.10-Wheels für gfx110X) |
| `xtx_bauen.py` | holen, patchen, bauen, zusammenstellen |
| Zweig `xtx-<version>` | Strata am Tag `v<version>` mit eingesetztem Patch |

## Lizenz

MIT, wie Strata. Strata ist das Werk von Niko1221 und den Strata-Mitwirkenden; siehe `LICENSE`.
