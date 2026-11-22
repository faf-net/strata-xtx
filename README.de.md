# strata-xtx

Strata für eine Radeon RX 7900 XTX unter Linux: liest lange Prompts etwa doppelt so schnell wie das offizielle Release, ohne einen einzigen Schalter in der Laufkonfiguration.

[English version](README.md)

| Gegenüber dem Release 0.2.18, auf derselben Karte gemessen | Release | strata-xtx |
|---|---:|---:|
| Prompt mit 32.000 Token einlesen | 1.358 Token/s | 2.851 Token/s |
| Prompt mit 250.000 Token einlesen | 206 s | 83 s |
| Schreiben im Chat | 69,5 Token/s | 76,3 Token/s |
| Qualität (eigener Aufgabensatz, 102 Aufgaben) | gleich | gleich |

- **Nichts einzustellen:** Die Engine erkennt die Karte und schaltet die Beschleunigung selbst ein.
- **Abgesichert:** ein Schalter zum Abschalten, und ein selbsttätiger Neustart im exakten Modus, falls die Engine nicht-endliche Werte meldet.
- **Klein und nachvollziehbar:** 207 Zeilen in fünf Dateien, als Patch und als fertiger Zweig je Strata-Version.
- **Der Preis:** Die Antworten sind nicht Bit für Bit dieselben wie beim Release, und die Karte zieht beim Einlesen 25 bis 30 W mehr. Einzelheiten unter „Was ich gemessen habe“.

**Die ganze Anlage mit allen Messungen und Diagrammen:** [faf.net/lokale-ki](https://faf.net/lokale-ki/) (English: [faf.net/local-ai](https://faf.net/local-ai/)).

Dies ist ein inoffizieller Ableger von [Strata](https://github.com/Niko1221/Strata) (MIT). Es ist kein Strata-Release, und Fragen dazu gehören hierher, nicht zum Original. Die Änderung ist klein: 207 Zeilen in fünf Dateien. Der aktuelle Stand sitzt auf Strata v0.2.18 (Zweig `xtx-0.2.18`; der Patch ließ sich unverändert anwenden); v0.2.17, v0.2.16 und v0.2.15 lassen sich weiter bauen (Zweige `xtx-0.2.17`, `xtx-0.2.16`, `xtx-0.2.15`).

## Was er tut

Stratas Engine bringt eine Reihe von Schaltern (Umgebungsvariablen) für das Einlesen des Prompts mit, die auf dieser Kartengeneration ausgeschaltet sind, weil mehrere davon die Rundung ändern. Auf neueren Karten schaltet Strata vergleichbare von selbst ein. Dieser Bau tut dasselbe für einen Fall:

- Linux, genau eine sichtbare Grafikkarte, und diese ist eine eigenständige `gfx1100`-Karte (RX 7900 XTX oder XT).
- Dann gilt eine Tabelle mit 27 Schaltern der Engine. 26 davon setzt die Engine neu, einer (`PF_FUSED`) ist im Release schon an. Dazu darf ein bloßes `--prefill auto` Stücke bis 32.768 Token nehmen.
- Alles andere läuft wie bisher: zwei Karten, jede andere Architektur, eine integrierte Grafik, Windows.
- Die Tabelle gehört nur zu Stratas Haupt-Engine. Die eigene Engine für Tencent Hy4-Flash, die mit Strata 0.2.18 dazukam (`strata-hy4`), liest keinen dieser Schalter; an Hy4-Flash ändert dieser Bau also nichts ([gemessen](https://github.com/faf-net/ugreen-idx6011-egpu-llm/blob/main/messen/daten/2026-11-22-hy4-flash/README.de.md)).

Dazu kommen drei Dinge:

- **Die eigene Einstellung gewinnt.** Ein Schalter, den man selbst setzt, wird nie überschrieben, gleich mit welchem Wert.
- **Ein Ausweg.** `STRATA_GFX1100_DEFAULTS=0` schaltet die ganze Tabelle ab und mit ihr die Regel für die Stückgröße.
- **Selbstrettung.** Meldet die Engine nicht-endliche Werte und hilft Stratas eigener zweiter Versuch nicht, startet der Server die Engine einmal ohne die Tabelle neu und läuft im langsameren, exakten Modus weiter. Die Anfrage, die das auslöst, endet selbst mit einem Fehler (HTTP 503); die folgenden werden beantwortet. `STRATA_GFX1100_RESCUE=0` im `env` der Laufkonfiguration schaltet diesen Neustart ab.

Die Engine schreibt beim Start eine Zeile mit dem Namen des Baus (`xtx-2`, auf 0.2.17 und 0.2.18; `xtx-1` war dieselbe Tabelle auf 0.2.15 und 0.2.16 mit einem Einlesepuffer von 192 statt 384) und eine Zeile mit den Schaltern, die sie gesetzt hat. Ein Protokoll sagt damit immer, was gelaufen ist. `strata --version` bleibt unverändert.

## Was ich gemessen habe

Hardware: RX 7900 XTX in einem OCuLink-x4-Dock an einer UGREEN iDX6011 Pro (62 GiB RAM), Karte in meiner leisen Leistungseinstellung. Modell: Qwen3.8-Flash-Next IQ3_XXS, einmal unverändert und einmal als Variante mit Steuervektor und Bildeingang. Alle Werte sind am 21. und 22.11.2026 auf Strata 0.2.18 gemessen, wo nichts anderes dabeisteht; der Aufbau ist in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm) beschrieben.

Einlesen eines frischen Prompts in Token je Sekunde (Median aus zwei bis drei Läufen):

| Prompt-Token | Normales Modell | Mit Steuervektor | Dauer, normales Modell |
|---|---:|---:|---:|
| 4.077 | 1.485 | 1.482 | 2,7 s |
| 16.254 | 2.486 | 2.366 | 6,5 s |
| 65.025 | 3.113 | 3.238 | 20,9 s |
| 130.026 | 3.151 | 3.263 | 41,3 s |
| 248.054 | 3.075 | 3.172 | 80,7 s |

Gegen das unveränderte Release 0.2.18, im Wechsel gemessen (Stratas `tools/strata_bench.py --long`, drei Runden, jede Engine frisch geladen, normales Modell):

| Median | Release 0.2.18 | Dieser Bau |
|---|---:|---:|
| Prompt 4K, Token/s | 786 | 1.641 |
| Prompt 16K, Token/s | 1.385 | 2.479 |
| Prompt 32K, Token/s | 1.358 | 2.851 |
| Schreiben im Chat, Token/s | 69,5 | 76,3 |
| Schreiben im Agent-Test, Token/s | 73,5 | 78,7 |

- **Die Tabelle ist der ganze Unterschied.** Derselbe Bau mit `STRATA_GFX1100_DEFAULTS=0` liest 16K mit rund 1.410 und 58K mit rund 1.309 Token je Sekunde, mit der Tabelle 2.479 / 2.552 und 3.277 / 3.163 (jeweils der erste von zwei Läufen; im zweiten lasen beide langsamer).
- **Ein Prompt von 250.000 Token:** 81 bis 83 s mit diesem Bau (3.043 bis 3.103 Token je Sekunde, beide Modelle), 206 s auf dem unveränderten Release (1.223 Token je Sekunde). Die im Prompt versteckte Zahl wurde jedes Mal gefunden.
- **Schreiben: gleich bis schneller.** Im Wechselvergleich lag dieser Bau in allen drei Runden über dem Release, im Chat-Teil um 9 bis 10 %, im Agent-Teil um 4 bis 12 %. Nach langen Prompts und beim Dauerschreiben sehe ich keinen solchen Gewinn (57 bis 62 und 68 bis 69 Token je Sekunde). Die langsameren langen Antworten der Variante mit Steuervektor auf 0.2.17 (64,3 Token je Sekunde) kamen auf 0.2.18 nicht wieder (68,5).
- **Qualität:** Mein Aufgabensatz ergibt auf 0.2.18 96 von 102 (normal) und 97 (mit Steuervektor); auf 0.2.17 waren es 95 und 97, auf 0.2.16 97 und 96, auf 0.2.15 97 und 98. Auf dem unveränderten Release 0.2.16 war es dasselbe wie auf diesem Bau: Einzelne Aufgaben besteht das Modell mal ja, mal nein, auf beiden Fassungen (je fünfmal wiederholt). Einen Unterschied von wenigen Punkten kann ein Satz von 102 Aufgaben allerdings nicht zeigen; ein größerer gepaarter Vergleich mit dem Release steht noch aus.
- **Dauerlauf:** 90 Minuten gemischte Anfragen auf dem Modell mit Steuervektor: 1.260 Anfragen, keine fehlgeschlagen, 180 von 180 versteckten Zahlen gefunden, kein nicht-endlicher Wert im Engine-Protokoll.
- **Selbstrettung:** Mit Stratas eingebauter Fehlerinjektion endete die auslösende Anfrage mit einem Fehler (HTTP 503), der Server startete die Engine einmal ohne die Tabelle neu und beantwortete die folgenden Anfragen, auf 0.2.17 mit beiden Modellen, auf 0.2.18 mit dem Modell mit Steuervektor. Ein Prompt von 16K wurde danach mit rund 1.300 Token je Sekunde gelesen, also im langsamen Modus, und die Zahl gefunden.
- **Strom:** Beim Einlesen zieht die Karte mit der Tabelle 25 bis 30 W mehr (292 bis 300 W gegen 267 bis 270 W, am 18.11.2026 gegen das Release 0.2.14 gemessen). Weil das Einlesen halb so lange dauert, ist die Energie je gelesenem Token trotzdem rund halb so hoch: 0,037 bis 0,047 gegen 0,070 bis 0,087 Wh je 1.000 Token. Beim Schreiben ist die Leistung gleich.
- **Preis:** Die Antworten sind nicht Bit für Bit gleich wie ohne die Tabelle. Dazu kommen rund 0,6 GiB mehr Arbeitsspeicher nach dem Laden; das habe ich am 18.11.2026 mit denselben Schaltern auf dem Release 0.2.14 gemessen und auf 0.2.16, 0.2.17 und 0.2.18 nicht neu aufgeschlüsselt.
- **Frühere Basen:** Als `xtx-1` (Puffer 192) las der Patch auf Strata 0.2.16 (19.11.2026) bei 16K 2.404 und 2.290, bei 248K 2.907 und 2.890 Token je Sekunde, auf 0.2.15 (18.11.) 2.345 und 2.248 / 2.906 und 2.847. Als `xtx-2` auf 0.2.17 (21.11.) las er 2.478 und 2.366 / 3.093 und 3.128, innerhalb von 3 % von 0.2.18. Ab 65K liest `xtx-2` 5 bis 11 % mehr als `xtx-1`; das schreibe ich dem größeren Puffer zu, es ist aber je Bau eine Messreihe, kein Vergleich im Wechsel.

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
python3 xtx_bauen.py v0.2.18 --quelle Strata --paket <paket> --ziel <ausgabe>
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
