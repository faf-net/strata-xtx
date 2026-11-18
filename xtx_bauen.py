#!/usr/bin/env python3
"""Den Eigenbau für eine Strata-Version herstellen: Quelltext holen, Patch einsetzen, bauen, Engine-Ordner zusammenstellen.

  python3 xtx_bauen.py v0.2.15 --quelle <klon> --paket <release-paket> --ziel <ausgabe>
  python3 xtx_bauen.py v0.2.15 --quelle <klon> --paket <release-paket> --ziel <ausgabe> --nur-bau

  --quelle   Klon von https://github.com/Niko1221/Strata (wird auf den Zweig xtx-<version> gestellt)
  --paket    entpackte Release-Pakete dieser Version: <paket>/engine (strata-engine-…-linux-x86_64-hip-rx7900.tar.gz)
             und <paket>/control (strata-control-…-linux-x86_64.tar.gz). Aus engine/ kommen die ROCm-Bibliotheken,
             neben denen die gebaute Engine liegt; aus control/ der Server.
  --ziel     Ausgabe: <ziel>/engine (mit unserer Datei strata; die des Pakets bleibt als strata.release daneben),
             <ziel>/control (mit serve/server.py aus dem Zweig), <ziel>/BUILD-XTX.json
  --nur-bau  Quelltext-Zweig steht schon, nur neu bauen und einsetzen

Vorher einmal das Bau-Image herstellen (im Klon, wegen requirements.txt):
  docker build -t strata-bau:rocm-7.10 -f <dieses-repo>/bau/Dockerfile <klon>
Fehlt im neuen Quelltext ein Anker des Patches, bricht patch/anwenden.py ab und es wird nichts gebaut.
"""
import argparse, json, os, shutil, subprocess, sys, time

HIER = os.path.dirname(os.path.abspath(__file__))
p = argparse.ArgumentParser()
p.add_argument("tag")
p.add_argument("--quelle", required=True)
p.add_argument("--paket", required=True)
p.add_argument("--ziel", required=True)
p.add_argument("--nur-bau", action="store_true")
p.add_argument("--image", default="strata-bau:rocm-7.10")
a = p.parse_args()
SRC, PAKET, ZIEL = (os.path.abspath(x) for x in (a.quelle, a.paket, a.ziel))
ver = a.tag.lstrip("v")
GIT = ["git", "-C", SRC]


def lauf(*befehl, **kw):
    print("+", " ".join(befehl), flush=True)
    return subprocess.run(befehl, check=True, **kw)


def main():
    for pfad in (f"{PAKET}/engine/strata", f"{PAKET}/control/serve/server.py"):
        if not os.path.exists(pfad):
            sys.exit(f"Release-Paket fehlt: {pfad}")
    if not a.nur_bau:
        lauf(*GIT, "fetch", "--tags", "-q", "origin")
        lauf(*GIT, "checkout", "-q", "-B", f"xtx-{ver}", a.tag)
        lauf(sys.executable, f"{HIER}/patch/anwenden.py", SRC)
        lauf(*GIT, "add", "-A", "include/strata/core/gfx1100_defaults.hpp", "src/core/gfx1100_defaults.cpp",
             "src/program/generate.cpp", "cmake/strata_gpu_engine.cmake", "serve/server.py")
        lauf(*GIT, "commit", "-q", "-m", "gfx1100: prompt-path defaults for one discrete RX 7900 XTX / XT under Linux")
    aus = f"{ZIEL}/bau"
    os.makedirs(aus, exist_ok=True)
    lauf("docker", "run", "--rm", "--name", "strata-bau", "-e", f"JOBS={os.environ.get('JOBS', '8')}", "-v", f"{SRC}:/src",
         "-v", f"{aus}:/aus", "-v", f"{HIER}/bau/bauen.sh:/bauen.sh:ro", a.image, "sh", "/bauen.sh")
    for teil in ("engine", "control"):
        if not os.path.isdir(f"{ZIEL}/{teil}"):
            lauf("cp", "-a", f"{PAKET}/{teil}", f"{ZIEL}/{teil}")
    if not os.path.exists(f"{ZIEL}/engine/strata.release"):
        shutil.copy2(f"{PAKET}/engine/strata", f"{ZIEL}/engine/strata.release")
    shutil.copy2(f"{aus}/strata", f"{ZIEL}/engine/strata")
    os.chmod(f"{ZIEL}/engine/strata", 0o755)
    shutil.copy2(f"{SRC}/serve/server.py", f"{ZIEL}/control/serve/server.py")
    kopf = subprocess.run([*GIT, "log", "-1", "--format=%H"], capture_output=True, text=True).stdout.strip()
    basis = subprocess.run([*GIT, "rev-list", "-n", "1", a.tag], capture_output=True, text=True).stdout.strip()
    json.dump({"built": time.strftime("%Y-%m-%d %H:%M:%S"), "strata_tag": a.tag, "strata_commit": basis, "branch_commit": kopf,
               "arch": "gfx1100", "image": a.image, "libraries_from": f"release package {ver} (engine folder)",
               "control_from": f"release package {ver}, serve/server.py from the branch"},
              open(f"{ZIEL}/BUILD-XTX.json", "w"), indent=1)
    print(f"fertig: {ZIEL}")


if __name__ == "__main__":
    main()
