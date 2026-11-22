# strata-xtx

Strata for one Radeon RX 7900 XTX under Linux: reads long prompts about twice as fast as the official release, without a single switch in the run configuration.

[Deutsche Fassung](README.de.md)

| Against the 0.2.19 release, measured on the same card | Release | strata-xtx `0.2.19-xtx3` |
|---|---:|---:|
| Reading a prompt of 32,000 tokens | 1,472 tokens/s | **3,054 tokens/s** |
| Reading a prompt of 250,000 tokens | 177 s | **78 s** |
| Decode in chat | 70.6 tokens/s | 75.3 tokens/s |
| Decode in the agent run | 75.9 tokens/s | **81.7 tokens/s** |
| Quality (my own task set, 102 tasks) | same | same |

**New with 0.2.19:** Strata 0.2.19 brings its own defaults for RDNA3 cards, and with them a RAM guard that keeps prompt chunks small unless 6 GiB of RAM stay free. With a 125B model on a 64 GB machine that never happens, so 0.2.19 reads long prompts in 8K chunks. The previous build, applied unchanged to 0.2.19, read a 58K prompt at 1,497 instead of 3,206 tokens/s. `0.2.19-xtx3` adds Strata's own switch `STRATA_GFX11_CHUNK=1` to the table and reads it at 3,433, 7 % faster than before. Details under [Strata 0.2.19 and its RAM guard](#strata-0219-and-its-ram-guard).

- **Nothing to configure:** the engine recognises the card and turns the speed-up on by itself.
- **With a safety net:** one switch to turn it off, and an automatic restart in the exact mode if the engine reports non-finite values.
- **Small and easy to follow:** 215 lines in five files, as a patch and as a ready branch per Strata version.
- **The price:** the answers are not bit for bit the same as the release's, and the card draws 25 to 30 W more while reading. Details under "What I measured".

**The whole setup with all measurements and charts:** [faf.net/local-ai](https://faf.net/local-ai/) (Deutsch: [faf.net/lokale-ki](https://faf.net/lokale-ki/)).

This is an unofficial fork of [Strata](https://github.com/Niko1221/Strata) (MIT). It is not a Strata release, and questions about it belong here, not upstream. The change is small: 215 lines in five files. The current state is `0.2.19-xtx3` on Strata v0.2.19 (branch `xtx-0.2.19`); v0.2.18, v0.2.17, v0.2.16 and v0.2.15 can still be built with the patch as it was then (branches `xtx-0.2.18` to `xtx-0.2.15`). Builds are named `<Strata release>-xtx<patch revision>`; the number after xtx only goes up when the patch itself changes.

## What it does

Strata's engine carries a number of switches (environment variables) for the prompt path that are off by default on this card generation, because several of them change the rounding. On newer cards Strata turns comparable ones on by itself. This build does the same for one case:

- Linux, exactly one visible GPU, that GPU a discrete `gfx1100` card (RX 7900 XTX or XT).
- In that case a table of 28 of the engine's switches applies. The engine newly sets 27 of them, one (`PF_FUSED`) is already on in the release. In addition a bare `--prefill auto` may take chunks of up to 32,768 tokens; from 0.2.19 on, Strata's own `STRATA_GFX11_CHUNK=1` in the table keeps its RAM guard from shrinking them again.
- Everything else runs the code it always ran: two cards, any other architecture, an integrated GPU, Windows.
- The table belongs to Strata's main engine only. The separate engines for Tencent Hy4-Flash (`strata-hy4`, since 0.2.18, [measured](https://github.com/faf-net/ugreen-idx6011-egpu-llm/tree/main/messen/daten/2026-11-22-hy4-flash)) and Inkling 2 Mini (`strata-inkling`, since 0.2.19) read none of these switches, so this build does not change them.

Three more things:

- **Your setting wins.** A switch you set yourself, to any value, is never overridden.
- **One way out.** `STRATA_GFX1100_DEFAULTS=0` turns the whole table off, and the chunk rule with it.
- **Self-rescue.** If the engine reports non-finite values and Strata's own retry does not help, the server starts the engine once more without the table (and, from 0.2.19 on, without Strata's own RDNA3 defaults, `STRATA_GFX11_DEFAULTS=0`) and keeps running in the slower, exact mode. The request that triggers this ends with an error itself (HTTP 503); the following ones are answered. `STRATA_GFX1100_RESCUE=0` in the `env` of the run config turns this restart off.

The engine prints one line at its start that names the build (`0.2.19-xtx3`; before that `xtx-2` on 0.2.17 and 0.2.18, `xtx-1` on 0.2.15 and 0.2.16 with a reading buffer of 192 instead of 384) and one line that lists the switches it set, so a log always says what ran. `strata --version` is unchanged.

## What I measured

Hardware: RX 7900 XTX in an OCuLink x4 dock on a UGREEN iDX6011 Pro (62 GiB RAM), card in my quiet power setting. Model: Qwen3.8-Flash-Next IQ3_XXS, once plain and once as the variant with a control vector and image input. All figures were measured on 22 Nov 2026 on Strata 0.2.19 (`0.2.19-xtx3`) unless stated otherwise; the setup is described in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm).

Reading a fresh prompt, tokens per second (median of two to three runs):

| Prompt tokens | Plain model | With control vector | Duration, plain model |
|---|---:|---:|---:|
| 4,077 | 1,555 | 1,460 | 2.6 s |
| 16,254 | 2,538 | 2,400 | 6.4 s |
| 65,025 | 3,439 | 3,469 | 18.9 s |
| 130,026 | 3,379 | 3,480 | 38.5 s |
| 248,054 | 3,324 | 3,381 | 74.6 s |

Against the unchanged 0.2.19 release, measured alternating (Strata's `tools/strata_bench.py --long`, three rounds, each engine loaded fresh, plain model):

| Median | Release 0.2.19 | This build |
|---|---:|---:|
| 4K prompt, tokens/s | 847 | 1,615 |
| 16K prompt, tokens/s | 1,510 | 2,528 |
| 32K prompt, tokens/s | 1,472 | 3,054 |
| chat decode, tokens/s | 70.6 | 75.3 |
| agent decode, tokens/s | 75.9 | 81.7 |

- **The table is the whole difference.** The same build with `STRATA_GFX1100_DEFAULTS=0` reads 16K at 1,511 and 58K at 1,430 tokens per second, with the table 2,537 and 3,433 (median of two rounds of two runs).
- **A prompt of 250,000 tokens:** 77 to 78 s with this build (both models), 177 s on the unchanged release. The task set's prompt of 247,954 tokens took 73 to 74 s (3,346 to 3,393 tokens per second). The number hidden in the prompt was found every time.
- **Writing: equal to faster.** In the alternating comparison this build came out 7 % above the release in the chat part and 8 % in the agent part; at full card power the agent part ran at 90.9 against 79.5 tokens per second. After long prompts and in continuous writing it writes at 58 to 65 and 65 to 69 tokens per second; I have no release figures for these cases on 0.2.19.
- **Quality:** my task set scores 98 of 102 (plain) and 97 (with control vector) on 0.2.19; on 0.2.18 it was 96 and 97, on 0.2.17 95 and 97, on 0.2.16 97 and 96, on 0.2.15 97 and 98. On the unchanged 0.2.16 release it was the same as on this build: some tasks the model passes sometimes, on both (each repeated five times). A set of 102 tasks cannot show a difference of a few points, though; a larger paired comparison against the release is still to do.
- **Endurance:** 90 minutes of mixed requests on the model with control vector: 1,316 requests, none failed, 188 of 188 hidden numbers found, no non-finite value in the engine log.
- **Self-rescue:** with Strata's built-in fault injection the triggering request ended with an error (HTTP 503), the server restarted the engine once without the table and answered the following requests, with both models on 0.2.17 and with the model with control vector on 0.2.18 and 0.2.19. A 16K prompt was then read at about 1,300 tokens per second, that is in the slow mode, and the number was found.
- **Power:** while reading, the card draws 25 to 30 W more with the table (292 to 300 W against 267 to 270 W, measured on 18 Nov 2026 against the 0.2.14 release). Because reading takes half as long, the energy per token read is still about half: 0.037 to 0.047 against 0.070 to 0.087 Wh per 1,000 tokens. While writing the power is the same.
- **Cost:** answers are not bit-identical to the engine without the table. On top come about 0.6 GiB more host RAM after loading; I measured that on 18 Nov 2026 with the same switches on the 0.2.14 release and did not break it down again on later versions.
- **Earlier bases:** as `xtx-1` (buffer 192) the patch read 2,404 and 2,290 at 16K and 2,907 and 2,890 at 248K on Strata 0.2.16 (19 Nov 2026), and 2,345 and 2,248 / 2,906 and 2,847 on 0.2.15 (18 Nov). As `xtx-2` on 0.2.17 (21 Nov) it read 2,478 and 2,366 / 3,093 and 3,128, and on 0.2.18 (22 Nov) 2,486 and 2,366 / 3,075 and 3,172. From 65K on `xtx-2` reads 5 to 11 % more than `xtx-1`; I attribute that to the larger buffer, but it is one series per build, not an alternating comparison. `0.2.19-xtx3` reads 7 to 10 % more than `xtx-2` on 0.2.18 from 64K on.

What I did not measure: the RX 7900 XT, a card in a full PCIe x16 slot, any other model or quant, Windows.

## Strata 0.2.19 and its RAM guard

Strata 0.2.19 added its own defaults for discrete RDNA3 cards (`engine/include/strata/core/gfx11_extra.hpp`), among them a rule that allows prompt chunks of up to 32K tokens. Taking that rule also turns on a RAM guard that came as the fix for [#2090](https://github.com/Niko1221/Strata/issues/2090): bigger chunks are used only if the extra cache loan plus 6 GiB fits into the RAM that is available. With the plain model loaded, my machine had 7.7 GiB available, 32K chunks need 9.2 GiB more, so the guard stepped down to 8K chunks (16K with the variant with control vector). The engine log says which chunk size it took.

| Prompt reading, tokens/s | 16K, plain | 58K, plain | 128K, with control vector |
|---|---:|---:|---:|
| previous build `0.2.18-xtx2` | 2,510 | 3,206 | 3,292 |
| release 0.2.19 as shipped | 1,511 | 1,430 | – |
| previous patch unchanged on 0.2.19 | 1,586 (−37 %) | 1,497 (−53 %) | 2,657 (−19 %) |
| release 0.2.19 with `STRATA_GFX11_CHUNK=1` (one run) | 1,851 | 2,550 | 2,718 |
| **`0.2.19-xtx3`** | **2,537 (+1 %)** | **3,433 (+7 %)** | **3,516 (+7 %)** |

Median of two rounds of two runs, 22 Nov 2026. `STRATA_GFX11_CHUNK=1` is Strata's own way to keep the 32K ceiling; `0.2.19-xtx3` carries it in the table, so the build reads as before and a little faster. The guard is meant to prevent swapping: with `0.2.19-xtx3` the lowest available RAM while reading stayed where it was on 0.2.18 (3.5 against 3.6 GiB plain, 5.2 against 5.5 GiB with control vector), swap did not move, and the 90-minute endurance run had no error. On a machine with less headroom the guard may be right; `STRATA_GFX11_CHUNK` set to anything else in your config wins over the table. The release alone with the switch still reads slower than this build, because its reading ring has 96 instead of 384 slots.

Raw data: [`messen/daten/2026-11-22-strata-xtx-0.2.19/`](https://github.com/faf-net/ugreen-idx6011-egpu-llm/tree/main/messen/daten/2026-11-22-strata-xtx-0.2.19) in the setup repository.

## The switches

`patch/gfx1100_defaults.cpp` is the table. Without the `STRATA_` prefix:

- Attention and block selection of the prompt on the matrix cores: `HIP_WMMA`, `SELECT_WMMA`, `PA_FAST`
- Experts and projections of the prompt: `PF_FUSED`, `PF_GEMM`, `PF_PAD`, `PF_F16=2`, `PF_HCDOWN`, `HC_UPMIX`, `QFUSE`, `FUSE_CONVAB`, `CVEC_FUSE`
- The recurrence of the prompt: `GDN_CHUNKED`, `GDN_HEAD`, `GDN_PP`, `GDN_CONVL2`, `GDN_NOY`
- Division of work and buffers: `PREFILL_CPU_SHARE=0.6`, `PREFILL_CPU_SHARE_MAX=4096`, `PREFILL_RING=384`, `STAGER_RING=64`, `KV_HOST_DMA`, `ADAPT_OVERLAP`, `SH_STREAM=0`
- The decode window: `QSA_ROWS`, `VERIFY_QDEDUP`, `HEAD_MIX_MULTI`
- Strata's own chunk ceiling for RDNA3 (from 0.2.19): `GFX11_CHUNK=1`

Every one of them exists in the unchanged engine. Strata's documentation describes a part of them; none is a promise. A release may rename or drop one, and the engine ignores an unknown name silently. That is why I test every new version before I use it.

## Build

You need Docker, a clone of Strata and the two release packages of the same version (engine `…-linux-x86_64-hip-rx7900` and control), unpacked into `<package>/engine` and `<package>/control`. The built engine is placed next to the ROCm libraries of the release package.

```sh
git clone https://github.com/Niko1221/Strata.git
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata/terminal
python3 xtx_bauen.py v0.2.19 --quelle Strata --paket <package> --ziel <output>
```

The result is `<output>/engine` and `<output>/control`, used like the release packages. `xtx_bauen.py` creates the branch `xtx-<version>` in the clone and writes the patch into it as a commit; Git needs a name and an e-mail address in the clone for that (`git config user.name`, `user.email`). The branches `xtx-0.2.19` to `xtx-0.2.15` of this repository are the patched source, if you would rather read or build that.

Since v0.2.16 Strata has a new folder layout: the engine lives under `engine/`, the server under `terminal/`. `patch/anwenden.py`, `bau/bauen.sh` and `xtx_bauen.py` recognise both layouts by themselves. Only the build image needs the right folder, because it reads Strata's `requirements.txt`: `Strata/terminal` from v0.2.16, `Strata` up to v0.2.15. The image holds tools only and can be used for both versions.

## A new Strata version

```sh
python3 xtx_bauen.py v<new> --quelle Strata --paket <package-new> --ziel <output>
```

`patch/anwenden.py` inserts the change at anchor lines of the original. If an anchor is gone in the new source, it stops and names it instead of patching halfway, and nothing is built.

A release can change more than anchor lines. With v0.2.16 the folders moved and build options were dropped; I had to follow both in the build script. So after every change I measure again before I use the build: speed with and without the table, the task set and the self-rescue with both models, plus an endurance run. v0.2.19 shows why: the patch applied cleanly and the build passed its quick checks, but it read long prompts at half speed. Only the comparison against the build in use showed it.

## Layout

| Path | Content |
|---|---|
| `patch/` | the two new source files and `anwenden.py`, which inserts them into a Strata source tree |
| `bau/` | build image and build script (ROCm 7.10 wheels for gfx110X) |
| `xtx_bauen.py` | fetch, patch, build, assemble |
| branch `xtx-<version>` | Strata at that tag with the patch applied |

## Licence

MIT, as Strata. Strata is the work of Niko1221 and the Strata contributors; see `LICENSE`.
