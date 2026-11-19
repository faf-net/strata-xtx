#!/usr/bin/env python3
"""Setzt die gfx1100-Voreinstellungen in einen Strata-Quelltext ein (Stand: v0.2.16; v0.2.15 mit der alten Ordnerstruktur geht weiter).

  python3 anwenden.py <strata-quelltext>

Zwei neue Dateien (gfx1100_defaults.hpp/.cpp) und acht kleine Einfügungen: ein Include und zwei Blöcke in
src/program/generate.cpp, eine Quelldatei in cmake/strata_gpu_engine.cmake und vier Stellen in serve/server.py (der Neustart
ohne die Tabelle nach nicht-endlichen Werten). Jede Einfügung hängt an einer Ankerzeile
des Originals; fehlt ein Anker (neue Strata-Version), bricht das Skript ab und nennt ihn, statt halb zu patchen.
Ein zweiter Lauf ändert nichts mehr.
"""
import os, shutil, sys

HIER = os.path.dirname(os.path.abspath(__file__))
MARKE = "gfx1100_defaults"

INCLUDE_ANKER = '#include "strata/core/arch_defaults.hpp"\n'
INCLUDE_NEU = INCLUDE_ANKER + '#include "strata/core/gfx1100_defaults.hpp"\n'

ENV_ANKER = "            strata::core::apply_arch_defaults(ad.gcnArchName, all_igpu, o.batch, kMmqBuilt);\n"
ENV_NEU = """#if defined(STRATA_USE_HIP)
            {   // one discrete gfx1100 card under Linux (gfx1100_defaults.hpp): before apply_arch_defaults; a switch the user set is kept
                int nd1100 = 0;
                if (cudaGetDeviceCount(&nd1100) != cudaSuccess) nd1100 = 0;
                (void) cudaGetLastError();
                std::fprintf(stderr, "strata: build %s (Strata engine %s with defaults for one RX 7900 XTX / XT)\\n", strata::core::kGfx1100Build, STRATA_VERSION);
                strata::core::apply_gfx1100_defaults(ad.gcnArchName, ad.integrated != 0, nd1100);
            }
#endif
""" + ENV_ANKER

CHUNK_ANKER = """#if defined(STRATA_USE_HIP) && !defined(_WIN32)
    if (o.prefill_auto_bare && o.prefill_auto_cap == 0) {
        // gfx1200 / gfx1201 (RDNA4, Linux)"""
CHUNK_NEU = """#if defined(STRATA_USE_HIP) && !defined(_WIN32)
    if (o.prefill_auto_bare && o.prefill_auto_cap == 0) {
        // one discrete gfx1100 card (gfx1100_defaults.hpp): a bare `--prefill auto` may reach 32768, as STRATA_PREFILL_AUTO_MAX=32768 does.
        // An explicit --prefill N, auto:N or STRATA_PREFILL_AUTO_MAX is never touched; STRATA_GFX1100_DEFAULTS=0 keeps 8192.
        cudaDeviceProp xp{};
        int xn = 0;
        if (cudaGetDeviceCount(&xn) == cudaSuccess && cudaGetDeviceProperties(&xp, 0) == cudaSuccess) {
            const int64_t top = strata::core::gfx1100_chunk_ceiling(xp.gcnArchName, xp.integrated != 0, xn);
            if (top > 0) {
                o.prefill_auto_max = top;
                o.prefill_chunk = top;
                std::fprintf(stderr, "strata generate: gfx1100: --prefill auto may take chunks up to %lld (STRATA_GFX1100_DEFAULTS=0 keeps 8192)\\n", (long long) top);
            }
        }
        (void) cudaGetLastError();
    }
    if (o.prefill_auto_bare && o.prefill_auto_cap == 0) {
        // gfx1200 / gfx1201 (RDNA4, Linux)"""

CMAKE_ANKER = "src/core/arch_defaults.cpp src/core/nv_defaults.cpp"
CMAKE_NEU = "src/core/arch_defaults.cpp src/core/gfx1100_defaults.cpp src/core/nv_defaults.cpp"


# ---- serve/server.py: Selbstrettung nach nicht-endlichen Werten (#879) ----
RETTUNG_ANKER_1 = "    def _say_died(self, e: Exception) -> None:\n"
RETTUNG_NEU_1 = '''    def _gfx1100_rescue(self) -> bool:
        """gfx1100 defaults (one RX 7900 XTX / XT, src/core/gfx1100_defaults.cpp): several of them compute the prompt with
        FP16 operands.  When the engine reports non-finite logits (#879) while that table is on, the engine is started
        again once with STRATA_GFX1100_DEFAULTS=0 (the code every other card runs) and stays there until the server is
        started again.  True when it was restarted.  STRATA_GFX1100_RESCUE=0 in the config's env turns this off."""
        eng = self.engine
        sp = getattr(eng, "spawn", None)
        if getattr(self, "_gfx1100_rescued", False) or not isinstance(sp, tuple) or len(sp) < 7:
            return False
        env = dict(sp[4] if sp[4] is not None else os.environ)
        if env.get("STRATA_GFX1100_RESCUE") == "0" or env.get("STRATA_GFX1100_DEFAULTS") == "0":
            return False
        try:                                             # only where the engine said at its start that the table is on
            with open(sp[3], "rb") as f:
                f.seek(0, os.SEEK_END)
                f.seek(max(0, f.tell() - 4_000_000))
                if b"gfx1100 (one RX 7900" not in f.read():
                    return False
        except (OSError, TypeError):
            return False
        env["STRATA_GFX1100_DEFAULTS"] = "0"
        eng.spawn = sp[:4] + (env,) + sp[5:]
        self._gfx1100_rescued = True
        print("[strata] gfx1100: non-finite logits (#879) with the gfx1100 prompt-path defaults on: starting the engine "
              "again without them (STRATA_GFX1100_DEFAULTS=0; prompts are read at about half the speed until the server "
              "is started again; STRATA_GFX1100_RESCUE=0 turns this off)", flush=True)
        try:
            eng.restart()
        except Exception as e:                           # the next request starts it (with the safe environment)
            print(f"[strata] gfx1100: the engine did not start again right away ({e}); the next request starts it", flush=True)
            return False
        return True

''' + RETTUNG_ANKER_1

RETTUNG_ANKER_2 = "        nf_retried = False                              # #879: the request was sent again after non-finite logits\n"
RETTUNG_NEU_2 = RETTUNG_ANKER_2 + "        nf_rescued = False                              # gfx1100: sent once more after the engine was restarted without its defaults\n"

RETTUNG_ANKER_3 = '''                            if n == 0:
                                finish = "error"
                                print("[strata] the engine's logits became non-finite again on the retry (#879): the "
'''
RETTUNG_NEU_3 = '''                            if n == 0 and not nf_rescued and self._gfx1100_rescue():
                                nf_rescued = True       # gfx1100: the engine runs without its prompt-path defaults now
                                del segments[segments_before:]
                                continue
''' + RETTUNG_ANKER_3

RETTUNG_ANKER_4 = '''                                  "reads its prompt from the start", flush=True)
                            finish = "length"
'''
RETTUNG_NEU_4 = '''                                  "reads its prompt from the start", flush=True)
                            self._gfx1100_rescue()      # gfx1100: the next request runs without the prompt-path defaults
                            finish = "length"
'''

MARKEN = ("gfx1100_defaults", "_gfx1100_rescue")


def ersetze(pfad, paare):
    s = open(pfad, encoding="utf-8").read()
    if any(m in s for m in MARKEN):
        print(f"schon gepatcht: {pfad}")
        return
    for name, alt, neu in paare:
        if s.count(alt) != 1:
            sys.exit(f"ANKER FEHLT oder mehrdeutig ({s.count(alt)} Treffer) in {pfad}: {name}")
        s = s.replace(alt, neu)
    open(pfad, "w", encoding="utf-8", newline="\n").write(s)
    print(f"gepatcht: {pfad} ({len(paare)} Stellen)")


def main():
    q = sys.argv[1]
    neu = os.path.isdir(os.path.join(q, "engine", "src"))      # ab v0.2.16: engine/ und terminal/ statt der Wurzel
    e, t = ("engine/", "terminal/") if neu else ("", "")
    shutil.copy(os.path.join(HIER, "gfx1100_defaults.hpp"), os.path.join(q, e + "include/strata/core/gfx1100_defaults.hpp"))
    shutil.copy(os.path.join(HIER, "gfx1100_defaults.cpp"), os.path.join(q, e + "src/core/gfx1100_defaults.cpp"))
    ersetze(os.path.join(q, e + "src/program/generate.cpp"),
            [("Include", INCLUDE_ANKER, INCLUDE_NEU), ("Tabelle setzen", ENV_ANKER, ENV_NEU), ("Chunk-Obergrenze", CHUNK_ANKER, CHUNK_NEU)])
    ersetze(os.path.join(q, e + "cmake/strata_gpu_engine.cmake"), [("Quelldatei", CMAKE_ANKER, CMAKE_NEU)])
    ersetze(os.path.join(q, t + "serve/server.py"),
            [("Rettung: Methode", RETTUNG_ANKER_1, RETTUNG_NEU_1), ("Rettung: Merker", RETTUNG_ANKER_2, RETTUNG_NEU_2),
             ("Rettung: Wiederholung", RETTUNG_ANKER_3, RETTUNG_NEU_3), ("Rettung: abgeschnittene Antwort", RETTUNG_ANKER_4, RETTUNG_NEU_4)])


if __name__ == "__main__":
    main()
