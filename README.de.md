# strata-xtx

Strata für eine Radeon RX 7900 XTX unter Linux: liest Prompts 1,3- bis 2,0-mal so schnell wie das offizielle Release, ohne einen einzigen Schalter in der Laufkonfiguration.

[English version](README.md)

| Gegenüber dem Release 0.2.22, auf derselben Karte gemessen | Release | strata-xtx `0.2.22-xtx3` |
|---|---:|---:|
| Prompt mit 4.000 Token einlesen | 842 Token/s | **1.686 Token/s** |
| Prompt mit 32.000 Token einlesen | 2.289 Token/s | **3.066 Token/s** |
| Prompt mit 250.000 Token einlesen | 104 s | **79 s** |
| Schreiben im Chat | 74,7 Token/s | 79,3 Token/s |
| Schreiben im Agent-Test | 79,3 Token/s | 83,3 Token/s |
| Qualität (eigener Aufgabensatz, 102 Aufgaben) | gleich | gleich |

**Neu mit 0.2.22:** An der Engine ändert sich für eine Karte nichts, der Patch greift unverändert. Control gibt einer Anfrage ohne Sampling-Angabe auf Modellen mit `--mtp` jetzt wieder das Sampling der Modellkarte ([#7070](https://github.com/Niko1221/Strata/issues/7070)): bei Flash-Next Temperatur 1,0 statt greedy. Wer kein Sampling mitschickt und weiter greedy antworten lassen will, trägt `"sampling": {"temperature": 0}` in die Laufkonfiguration ein ([Einzelheiten](#strata-0222-sampling-für-anfragen-ohne-angabe)). **0.2.21:** Das Release hat aufgeholt. Es lockert seinen RAM-Wächter ([#6687](https://github.com/Niko1221/Strata/issues/6687)) und liest auf meiner Maschine jetzt in Stücken von 16K statt 8K: 32K mit 2.217 statt 1.475 Token/s, 250.000 Token in 103 statt 175 s. Der Patch ließ sich unverändert anwenden und liest wie auf 0.2.20; der Vorsprung auf das Release ist damit vom rund Doppelten auf das 1,3- bis 1,9-Fache geschrumpft ([Einzelheiten](#strata-0221-das-release-holt-auf)). **0.2.20:** Der Patch ließ sich unverändert anwenden; 0.2.20 änderte für diese Karte nichts. Den CPU-Anteil bei kurzen Prompts habe ich neu gemessen: Die Tabelle bleibt, wie sie ist ([Einzelheiten](#was-ich-auf-0220-ausprobiert-habe)). **Seit 0.2.19:** Strata bringt eigene Voreinstellungen für RDNA3-Karten mit und mit ihnen einen RAM-Wächter, der die Prompt-Stücke klein hält, solange nicht 6 GiB RAM frei bleiben. Mit einem 125B-Modell auf einer Maschine mit 64 GB ist das nie der Fall, also lasen 0.2.19 und 0.2.20 lange Prompts in Stücken von 8K. Der bisherige Bau, unverändert auf 0.2.19 angewandt, las einen Prompt von 58K mit 1.497 statt 3.206 Token/s. `0.2.19-xtx3` nimmt Stratas eigenen Schalter `STRATA_GFX11_CHUNK=1` in die Tabelle auf und liest ihn mit 3.433, 7 % schneller als bisher. Einzelheiten unter [Strata 0.2.19 und sein RAM-Wächter](#strata-0219-und-sein-ram-wächter).

- **Nichts einzustellen:** Die Engine erkennt die Karte und schaltet die Beschleunigung selbst ein.
- **Abgesichert:** ein Schalter zum Abschalten, und ein selbsttätiger Neustart im exakten Modus, falls die Engine nicht-endliche Werte meldet.
- **Klein und nachvollziehbar:** 215 Zeilen in fünf Dateien, als Patch und als fertiger Zweig je Strata-Version.
- **Der Preis:** Die Antworten sind nicht Bit für Bit dieselben wie beim Release, und die Karte zieht beim Einlesen 25 bis 30 W mehr. Einzelheiten unter „Was ich gemessen habe“.

**Die ganze Anlage mit allen Messungen und Diagrammen:** [faf.net/lokale-ki](https://faf.net/lokale-ki/) (English: [faf.net/local-ai](https://faf.net/local-ai/)).

Dies ist ein inoffizieller Ableger von [Strata](https://github.com/Niko1221/Strata) (MIT). Es ist kein Strata-Release, und Fragen dazu gehören hierher, nicht zum Original. Die Änderung ist klein: 215 Zeilen in fünf Dateien. Der aktuelle Stand ist `0.2.22-xtx3` auf Strata v0.2.22 (Zweig `xtx-0.2.22`); v0.2.21 bis v0.2.15 lassen sich mit dem damaligen Patch weiter bauen (Zweige `xtx-0.2.21` bis `xtx-0.2.15`). Die Bauten heißen `<Strata-Release>-xtx<Patchstand>`; die Zahl hinter xtx steigt nur, wenn sich der Patch selbst ändert.

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

Die Engine schreibt beim Start eine Zeile mit dem Namen des Baus (`0.2.22-xtx3`, davor `0.2.21-xtx3`, `0.2.20-xtx3` und `0.2.19-xtx3`; früher `xtx-2` auf 0.2.17 und 0.2.18, `xtx-1` auf 0.2.15 und 0.2.16 mit einem Einlesepuffer von 192 statt 384) und eine Zeile mit den Schaltern, die sie gesetzt hat. Ein Protokoll sagt damit immer, was gelaufen ist. `strata --version` bleibt unverändert.

## Was ich gemessen habe

Hardware: RX 7900 XTX in einem OCuLink-x4-Dock an einer UGREEN iDX6011 Pro (62 GiB RAM), Karte in meiner leisen Leistungseinstellung. Modell: Qwen3.8-Flash-Next IQ3_XXS, einmal unverändert und einmal als Variante mit Steuervektor und Bildeingang. Alle Werte sind am 25. und 26.11.2026 auf Strata 0.2.22 (`0.2.22-xtx3`) gemessen, wo nichts anderes dabeisteht; der Aufbau ist in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm) beschrieben.

Einlesen eines frischen Prompts in Token je Sekunde (Median aus zwei bis drei Läufen):

| Prompt-Token | Normales Modell | Mit Steuervektor | Dauer, normales Modell |
|---|---:|---:|---:|
| 4.076 | 1.554 | 1.495 | 2,6 s |
| 16.192 | 2.165 | 2.388 | 7,5 s |
| 64.967 | 3.444 | 3.425 | 18,9 s |
| 130.144 | 3.401 | 3.485 | 38,3 s |
| 247.791 | 3.322 | 3.308 | 74,6 s |

Der 16K-Wert des normalen Modells ist ein Ausreißer: Seine drei Läufe lasen 2.108, 2.165 und 2.556 Token je Sekunde, während auf der Maschine wenig RAM frei war; auf 0.2.21 waren es 2.539.

Gegen das unveränderte Release 0.2.22, im Wechsel gemessen (Stratas `tools/strata_bench.py --long`, drei Runden, jede Engine frisch geladen, normales Modell):

| Median | Release 0.2.22 | Dieser Bau |
|---|---:|---:|
| Prompt 4K, Token/s | 842 | 1.686 |
| Prompt 16K, Token/s | 1.999 | 2.521 |
| Prompt 32K, Token/s | 2.289 | 3.066 |
| Schreiben im Chat, Token/s | 74,7 | 79,3 |
| Schreiben im Agent-Test, Token/s | 79,3 | 83,3 |

- **Die Tabelle ist der ganze Unterschied.** Derselbe Bau mit `STRATA_GFX1100_DEFAULTS=0` liest 16K mit 2.001 bis 2.015 Token je Sekunde, also wie das Release in Stücken von 16K; 58K in drei von sechs Ladungen mit 2.031 bis 2.081 und in den übrigen drei mit rund 2.540 (der RAM-Wächter des Release steht hier genau auf der Kante zu 32K-Stücken); mit der Tabelle liest das Modell mit Steuervektor 16K mit 2.415 und 58K mit 3.437. Auf 0.2.20 waren es ohne Tabelle 1.454 und 1.427 in Stücken von 8K.
- **Ein Prompt von 250.000 Token:** 79 s mit diesem Bau, 104 s auf dem unveränderten Release (0.2.21: 103 s, 0.2.20: 175 s); bei 128.000 Token 38 gegen 54 s. Der Prompt des Aufgabensatzes mit 247.954 Token brauchte 73,6 bis 74,8 s (beide Modelle). Die im Prompt versteckte Zahl wurde jedes Mal gefunden.
- **Schreiben: gleich bis schneller.** Im Wechselvergleich lag dieser Bau im Chat-Teil 6 % und im Agent-Teil 5 % über dem Release; bei voller Kartenleistung (eine Runde) lief der Chat-Teil mit 79,5 gegen 73,3 und der Agent-Teil mit 87,7 gegen 79,0 Token je Sekunde. Nach langen Prompts schreibt er mit 59 bis 65 und bei langen Antworten mit 69 bis 72 Token je Sekunde; Vergleichswerte des Release gibt es dafür auf 0.2.22 nicht.
- **Qualität:** Mein Aufgabensatz ergibt auf 0.2.22 97 von 102 (normal) und 95 (mit Steuervektor); auf 0.2.21 waren es 96 und 97, auf 0.2.20 und 0.2.19 98 und 97, auf 0.2.18 waren es 96 und 97, auf 0.2.17 95 und 97, auf 0.2.16 97 und 96, auf 0.2.15 97 und 98. Auf dem unveränderten Release 0.2.16 war es dasselbe wie auf diesem Bau: Einzelne Aufgaben besteht das Modell mal ja, mal nein, auf beiden Fassungen (je fünfmal wiederholt). Einen Unterschied von wenigen Punkten kann ein Satz von 102 Aufgaben allerdings nicht zeigen; ein größerer gepaarter Vergleich mit dem Release steht noch aus.
- **Dauerlauf:** 90 Minuten gemischte Anfragen auf dem Modell mit Steuervektor: 1.316 Anfragen, keine fehlgeschlagen, 188 von 188 versteckten Zahlen gefunden, kein nicht-endlicher Wert im Engine-Protokoll, verfügbarer RAM nie unter 5,4 GiB.
- **Selbstrettung:** Mit Stratas eingebauter Fehlerinjektion endete die auslösende Anfrage mit einem Fehler (HTTP 503), der Server startete die Engine einmal ohne die Tabelle neu und beantwortete die folgenden Anfragen, auf 0.2.17 mit beiden Modellen, auf 0.2.18 bis 0.2.22 mit dem Modell mit Steuervektor. Ein Prompt von 16K wurde danach mit rund 1.300 Token je Sekunde gelesen, also im langsamen Modus, und die Zahl gefunden.
- **Strom:** Beim Einlesen zieht die Karte mit der Tabelle 25 bis 30 W mehr (292 bis 300 W gegen 267 bis 270 W, am 18.11.2026 gegen das Release 0.2.14 gemessen). Weil das Einlesen halb so lange dauert, ist die Energie je gelesenem Token trotzdem rund halb so hoch: 0,037 bis 0,047 gegen 0,070 bis 0,087 Wh je 1.000 Token. Beim Schreiben ist die Leistung gleich.
- **Preis:** Die Antworten sind nicht Bit für Bit gleich wie ohne die Tabelle. Dazu kommen rund 0,6 GiB mehr Arbeitsspeicher nach dem Laden; das habe ich am 18.11.2026 mit denselben Schaltern auf dem Release 0.2.14 gemessen und auf späteren Versionen nicht neu aufgeschlüsselt.
- **Frühere Basen:** Als `xtx-1` (Puffer 192) las der Patch auf Strata 0.2.16 (19.11.2026) bei 16K 2.404 und 2.290, bei 248K 2.907 und 2.890 Token je Sekunde, auf 0.2.15 (18.11.) 2.345 und 2.248 / 2.906 und 2.847. Als `xtx-2` auf 0.2.17 (21.11.) las er 2.478 und 2.366 / 3.093 und 3.128, auf 0.2.18 (22.11.) 2.486 und 2.366 / 3.075 und 3.172. Ab 65K liest `xtx-2` 5 bis 11 % mehr als `xtx-1`; das schreibe ich dem größeren Puffer zu, es ist aber je Bau eine Messreihe, kein Vergleich im Wechsel. `0.2.19-xtx3` liest ab 64K 7 bis 10 % mehr als `xtx-2` auf 0.2.18; `0.2.20-xtx3` liest innerhalb von 1 % wie `0.2.19-xtx3`, `0.2.21-xtx3` innerhalb von 1,5 % wie `0.2.20-xtx3` und `0.2.22-xtx3` ab 64K innerhalb von 0,5 % wie `0.2.21-xtx3`.

Nicht gemessen habe ich: die RX 7900 XT, eine Karte in einem vollen PCIe-x16-Steckplatz, ein anderes Modell oder Quant, Windows.

## Strata 0.2.22: Sampling für Anfragen ohne Angabe

- **An der Engine nichts Neues.** Strata 0.2.22 (Engine und Control 0.1.69) ändert für eine Karte nur eine Speicherregel für zwei Karten, Symboldateien und die Versionsnummer. Das Release liest wie 0.2.21 (842 / 1.999 / 2.289 Token/s bei 4K / 16K / 32K), Schreiben in Paaren 66,1 gegen 64,6 Token/s. Der Patch greift unverändert; der Unterschied zum Release ist bis auf den Baunamen derselbe wie auf 0.2.21.
- **Sampling ([#7070](https://github.com/Niko1221/Strata/issues/7070)).** Seit 0.2.20 lief eine Anfrage ohne Sampling-Angabe auf jedem mit `--mtp` gestarteten Modell greedy. Ab 0.2.22 nimmt Flash-Next wieder das Sampling der Modellkarte: mit Denken Temperatur 1,0, top_p 0,95, top_k 20, ohne Denken zusätzlich presence penalty 1,5. Mein Agent schickt kein Sampling mit, seine Anfragen wären ab diesem Release also mit Temperatur 1,0 gelaufen. Ein Block `"sampling": {"temperature": 0}` in der Laufkonfiguration hält sie greedy; eine Anfrage, die ihr eigenes Sampling nennt, bekommt es weiterhin. Gemessen mit Anfragen in der Form meines Agenten: Mit dem Block antworten sie wie auf 0.2.21.
- **Ein falscher Alarm.** Im ersten Vergleich gegen `0.2.21-xtx3` schrieb das Modell mit Steuervektor in einer Ladung des neuen Baus mit 50 statt 65 Token/s. Ein Tausch von Engine und Control über Kreuz, das alte Paar doppelt als A/A-Kontrolle, zeigte keinen Unterschied zwischen den Bauten (alle innerhalb von 98 bis 105 %); die langsamen Ladungen kamen vom Speicherdruck auf der Maschine und trafen den alten Bau ebenso.

Rohdaten: [`messen/daten/2026-11-26-strata-xtx-0.2.22/`](https://github.com/faf-net/ugreen-idx6011-egpu-llm/tree/main/messen/daten/2026-11-26-strata-xtx-0.2.22) im Repository der Anlage (`checks/build-test*.json`, `checks/cause-2x2-run*.json`, `checks/sampling-7070.json`).

## Strata 0.2.21: das Release holt auf

- **Die Abhilfe im Release.** Strata 0.2.21 (Engine 0.1.67) ändert den RAM-Wächter aus 0.2.19 ([#6687](https://github.com/Niko1221/Strata/issues/6687)): Liegen keine Experten fest im RAM, zählt er nur noch die Hälfte des Leihspeichers und hält 3 statt 6 GiB Reserve. Auf meiner Maschine liest das unveränderte Release damit in Stücken von 16K statt 8K: 16K 32 % und 32K 50 % schneller als 0.2.20 (1.980 und 2.217 statt 1.503 und 1.475 Token/s).
- **32K-Stücke verfehlt es hier knapp.** Laut Engine-Log braucht es 4.675 MiB Leihe plus 3.072 MiB Reserve, frei waren 7.688 MiB (im zweiten Lauf 7.736): Es fehlten 59 (11) MiB. Dieser Bau setzt weiter `STRATA_GFX11_CHUNK=1` und liest in Stücken von 32K; im Dauerlauf fiel der verfügbare RAM dabei nie unter 5,5 GiB.
- **Was vom Vorsprung bleibt.** Bei 4K liest dieser Bau 1,9-mal, bei 16K 1,3-mal und bei 32K 1,4-mal so schnell wie das Release 0.2.21. Die Stückgröße erklärt davon nur noch einen Teil; den Rest tragen die übrigen 26 Schalter der Tabelle.
- **Folgeanfragen eines Agenten.** In #6687 berichtete ein anderer Nutzer (RX 7800 XT), dass eine niedrigere Stream-Schwelle (1.024 statt 3.072) die Wartezeit auf eine Folgeanfrage mit rund 1.600 neuen Token halbiert. Dieser Bau streamt erst ab 4.095 Token (die Grenze des CPU-Anteils, `PREFILL_CPU_SHARE_MAX=4096`). Ich habe 4.096, 2.048 und 1.024 verglichen: ein Vorspann von 4K oder 32K aus dem Gesprächs-Cache, dann 500, 1.600 oder 3.000 neue Token, beide Modelle, zwei Runden leise und eine mit voller Leistung. Mit 4.096 wartet das Modell mit Steuervektor 1,5 bis 3,4 s; mit 2.048 sind es bei 3.000 neuen Token 5,3 statt 3,4 s, mit 1.024 schon bei 1.600 neuen Token 5,2 statt 2,6 s. Auf dieser Karte mit einem 125B-Modell, dessen Experten im RAM liegen, kostet der gestreamte Weg pauschal rund 5 s. Die Tabelle bleibt bei 4.096.

Rohdaten: [`messen/daten/2026-11-24-strata-xtx-0.2.21/`](https://github.com/faf-net/ugreen-idx6011-egpu-llm/tree/main/messen/daten/2026-11-24-strata-xtx-0.2.21) im Repository der Anlage (`checks/build-test.json`, `checks/stream-floor-follow-ups.json`).

## Was ich auf 0.2.20 ausprobiert habe

- **CPU-Anteil bei kurzen Prompts.** Die Tabelle lässt den untätigen Prozessor bei Prompt-Stücken bis 4.096 Token einen Teil der Experten übernehmen (`PREFILL_CPU_SHARE=0.6`, `PREFILL_CPU_SHARE_MAX=4096`). Auf `0.2.19-xtx3` machte der Anteil 1K-Prompts 2,7-mal und 4K-Prompts 26 % schneller als ohne; Stratas eigene Grenze 3.072 kostete bei 4K ein Drittel, ein Anteil von 0,4 oder 0,8 las wie 0,6. Auf 0.2.20 habe ich die Grenzen 3.072, 3.584, 4.096, 4.608 und 6.144 mit Prompts von 2K bis 16K verglichen (drei Runden leise im Wechsel und eine mit voller Leistung, beide Modelle): 4.096 hält 4K bei 1.131 statt 714 Token/s mit 3.072; bei 16K lesen alle Grenzen gleich (2.517 bis 2.545); 6.144 liest 6K 30 % schneller, 8K aber 12 % langsamer. Die Tabelle bleibt bei 4.096.
- **hipBLASLt-Tuning-Tabelle.** Sie abzuschalten änderte nichts über die Streuung hinaus; neu getunt habe ich sie deshalb nicht.
- **Die Stückgröße wird jetzt geprüft.** Seit 0.2.19 liest jede Prüfung eines neuen Baus die Stückgröße aus dem Engine-Log und fällt durch, wenn sie nicht 32.768 Token beträgt.
- **Der Name des Baus folgt dem Release.** `patch/anwenden.py` setzt ihn aus dem Release-Tag, auf dem der Quelltext steht, und aus `PATCHSTAND`; `v0.2.20` ergibt `0.2.20-xtx3`, die Zahl hinter xtx steigt nur, wenn sich der Patch ändert.

Rohdaten: [`messen/daten/2026-11-23-strata-xtx-0.2.20/`](https://github.com/faf-net/ugreen-idx6011-egpu-llm/tree/main/messen/daten/2026-11-23-strata-xtx-0.2.20) im Repository der Anlage (`checks/cpu-share-ceiling.json`, `checks/cpu-share-and-hipblaslt-0.2.19.json`).

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
python3 xtx_bauen.py v0.2.22 --quelle Strata --paket <paket> --ziel <ausgabe>
```

Das Ergebnis sind `<ausgabe>/engine` und `<ausgabe>/control`, zu verwenden wie die Release-Pakete. `xtx_bauen.py` legt im Klon den Zweig `xtx-<version>` an und schreibt den Patch dort als Commit hinein; Git braucht dafür im Klon einen Namen und eine E-Mail-Adresse (`git config user.name`, `user.email`). Die Zweige `xtx-0.2.22` bis `xtx-0.2.15` dieses Repositorys sind der gepatchte Quelltext, falls man lieber den liest oder baut.

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
