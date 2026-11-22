# strata-xtx

Strata for one Radeon RX 7900 XTX under Linux: reads long prompts about twice as fast as the official release, without a single switch in the run configuration.

[Deutsche Fassung](README.de.md)

| Against the 0.2.18 release, measured on the same card | Release | strata-xtx |
|---|---:|---:|
| Reading a prompt of 32,000 tokens | 1,358 tokens/s | 2,851 tokens/s |
| Reading a prompt of 250,000 tokens | 206 s | 83 s |
| Decode in chat | 69.5 tokens/s | 76.3 tokens/s |
| Quality (my own task set, 102 tasks) | same | same |

- **Nothing to configure:** the engine recognises the card and turns the speed-up on by itself.
- **With a safety net:** one switch to turn it off, and an automatic restart in the exact mode if the engine reports non-finite values.
- **Small and easy to follow:** 207 lines in five files, as a patch and as a ready branch per Strata version.
- **The price:** the answers are not bit for bit the same as the release's, and the card draws 25 to 30 W more while reading. Details under "What I measured".

**The whole setup with all measurements and charts:** [faf.net/local-ai](https://faf.net/local-ai/) (Deutsch: [faf.net/lokale-ki](https://faf.net/lokale-ki/)).

This is an unofficial fork of [Strata](https://github.com/Niko1221/Strata) (MIT). It is not a Strata release, and questions about it belong here, not upstream. The change is small: 207 lines in five files. The current state sits on Strata v0.2.18 (branch `xtx-0.2.18`; the patch applied unchanged); v0.2.17, v0.2.16 and v0.2.15 can still be built (branches `xtx-0.2.17`, `xtx-0.2.16`, `xtx-0.2.15`).

## What it does

Strata's engine carries a number of switches (environment variables) for the prompt path that are off by default on this card generation, because several of them change the rounding. On newer cards Strata turns comparable ones on by itself. This build does the same for one case:

- Linux, exactly one visible GPU, that GPU a discrete `gfx1100` card (RX 7900 XTX or XT).
- In that case a table of 27 of the engine's switches applies. The engine newly sets 26 of them, one (`PF_FUSED`) is already on in the release. In addition a bare `--prefill auto` may take chunks of up to 32,768 tokens.
- Everything else runs the code it always ran: two cards, any other architecture, an integrated GPU, Windows.
- The table belongs to Strata's main engine only. The separate engine for Tencent Hy4-Flash that Strata 0.2.18 added (`strata-hy4`) reads none of these switches, so this build does not change Hy4-Flash ([measured](https://github.com/faf-net/ugreen-idx6011-egpu-llm/tree/main/messen/daten/2026-11-22-hy4-flash)).

Three more things:

- **Your setting wins.** A switch you set yourself, to any value, is never overridden.
- **One way out.** `STRATA_GFX1100_DEFAULTS=0` turns the whole table off, and the chunk rule with it.
- **Self-rescue.** If the engine reports non-finite values and Strata's own retry does not help, the server starts the engine once more without the table and keeps running in the slower, exact mode. The request that triggers this ends with an error itself (HTTP 503); the following ones are answered. `STRATA_GFX1100_RESCUE=0` in the `env` of the run config turns this restart off.

The engine prints one line at its start that names the build (`xtx-2`, on 0.2.17 and 0.2.18; `xtx-1` was the same table on 0.2.15 and 0.2.16 with a reading buffer of 192 instead of 384) and one line that lists the switches it set, so a log always says what ran. `strata --version` is unchanged.

## What I measured

Hardware: RX 7900 XTX in an OCuLink x4 dock on a UGREEN iDX6011 Pro (62 GiB RAM), card in my quiet power setting. Model: Qwen3.8-Flash-Next IQ3_XXS, once plain and once as the variant with a control vector and image input. All figures were measured on 21 and 22 Nov 2026 on Strata 0.2.18 unless stated otherwise; the setup is described in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm).

Reading a fresh prompt, tokens per second (median of two to three runs):

| Prompt tokens | Plain model | With control vector | Duration, plain model |
|---|---:|---:|---:|
| 4,077 | 1,485 | 1,482 | 2.7 s |
| 16,254 | 2,486 | 2,366 | 6.5 s |
| 65,025 | 3,113 | 3,238 | 20.9 s |
| 130,026 | 3,151 | 3,263 | 41.3 s |
| 248,054 | 3,075 | 3,172 | 80.7 s |

Against the unchanged 0.2.18 release, measured alternating (Strata's `tools/strata_bench.py --long`, three rounds, each engine loaded fresh, plain model):

| Median | Release 0.2.18 | This build |
|---|---:|---:|
| 4K prompt, tokens/s | 786 | 1,641 |
| 16K prompt, tokens/s | 1,385 | 2,479 |
| 32K prompt, tokens/s | 1,358 | 2,851 |
| chat decode, tokens/s | 69.5 | 76.3 |
| agent decode, tokens/s | 73.5 | 78.7 |

- **The table is the whole difference.** The same build with `STRATA_GFX1100_DEFAULTS=0` reads 16K at about 1,410 and 58K at about 1,309 tokens per second, with the table 2,479 / 2,552 and 3,277 / 3,163 (the first of two runs each; in the second both read slower).
- **A prompt of 250,000 tokens:** 81 to 83 s with this build (3,043 to 3,103 tokens per second, both models), 206 s on the unchanged release (1,223 tokens per second). The number hidden in the prompt was found every time.
- **Writing: equal to faster.** In the alternating comparison this build came out above the release in all three rounds, by 9 to 10 % in the chat part and 4 to 12 % in the agent part. After long prompts and in continuous writing I see no such gain (57 to 62 and 68 to 69 tokens per second). The slower long answers of the variant with control vector on 0.2.17 (64.3 tokens per second) did not come back on 0.2.18 (68.5).
- **Quality:** my task set scores 96 of 102 (plain) and 97 (with control vector) on 0.2.18; on 0.2.17 it was 95 and 97, on 0.2.16 97 and 96, on 0.2.15 97 and 98. On the unchanged 0.2.16 release it was the same as on this build: some tasks the model passes sometimes, on both (each repeated five times). A set of 102 tasks cannot show a difference of a few points, though; a larger paired comparison against the release is still to do.
- **Endurance:** 90 minutes of mixed requests on the model with control vector: 1,260 requests, none failed, 180 of 180 hidden numbers found, no non-finite value in the engine log.
- **Self-rescue:** with Strata's built-in fault injection the triggering request ended with an error (HTTP 503), the server restarted the engine once without the table and answered the following requests, with both models on 0.2.17 and with the model with control vector on 0.2.18. A 16K prompt was then read at about 1,300 tokens per second, that is in the slow mode, and the number was found.
- **Power:** while reading, the card draws 25 to 30 W more with the table (292 to 300 W against 267 to 270 W, measured on 18 Nov 2026 against the 0.2.14 release). Because reading takes half as long, the energy per token read is still about half: 0.037 to 0.047 against 0.070 to 0.087 Wh per 1,000 tokens. While writing the power is the same.
- **Cost:** answers are not bit-identical to the engine without the table. On top come about 0.6 GiB more host RAM after loading; I measured that on 18 Nov 2026 with the same switches on the 0.2.14 release and did not break it down again on 0.2.16, 0.2.17 or 0.2.18.
- **Earlier bases:** as `xtx-1` (buffer 192) the patch read 2,404 and 2,290 at 16K and 2,907 and 2,890 at 248K on Strata 0.2.16 (19 Nov 2026), and 2,345 and 2,248 / 2,906 and 2,847 on 0.2.15 (18 Nov). As `xtx-2` on 0.2.17 (21 Nov) it read 2,478 and 2,366 / 3,093 and 3,128, within 3 % of 0.2.18. From 65K on `xtx-2` reads 5 to 11 % more than `xtx-1`; I attribute that to the larger buffer, but it is one series per build, not an alternating comparison.

What I did not measure: the RX 7900 XT, a card in a full PCIe x16 slot, any other model or quant, Windows.

## The switches

`patch/gfx1100_defaults.cpp` is the table. Without the `STRATA_` prefix:

- Attention and block selection of the prompt on the matrix cores: `HIP_WMMA`, `SELECT_WMMA`, `PA_FAST`
- Experts and projections of the prompt: `PF_FUSED`, `PF_GEMM`, `PF_PAD`, `PF_F16=2`, `PF_HCDOWN`, `HC_UPMIX`, `QFUSE`, `FUSE_CONVAB`, `CVEC_FUSE`
- The recurrence of the prompt: `GDN_CHUNKED`, `GDN_HEAD`, `GDN_PP`, `GDN_CONVL2`, `GDN_NOY`
- Division of work and buffers: `PREFILL_CPU_SHARE=0.6`, `PREFILL_CPU_SHARE_MAX=4096`, `PREFILL_RING=384`, `STAGER_RING=64`, `KV_HOST_DMA`, `ADAPT_OVERLAP`, `SH_STREAM=0`
- The decode window: `QSA_ROWS`, `VERIFY_QDEDUP`, `HEAD_MIX_MULTI`

Every one of them exists in the unchanged engine. Strata's documentation describes a part of them; none is a promise. A release may rename or drop one, and the engine ignores an unknown name silently. That is why I test every new version before I use it.

## Build

You need Docker, a clone of Strata and the two release packages of the same version (engine `…-linux-x86_64-hip-rx7900` and control), unpacked into `<package>/engine` and `<package>/control`. The built engine is placed next to the ROCm libraries of the release package.

```sh
git clone https://github.com/Niko1221/Strata.git
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata/terminal
python3 xtx_bauen.py v0.2.18 --quelle Strata --paket <package> --ziel <output>
```

The result is `<output>/engine` and `<output>/control`, used like the release packages. `xtx_bauen.py` creates the branch `xtx-<version>` in the clone and writes the patch into it as a commit; Git needs a name and an e-mail address in the clone for that (`git config user.name`, `user.email`). The branches `xtx-0.2.17`, `xtx-0.2.16` and `xtx-0.2.15` of this repository are the patched source, if you would rather read or build that.

Since v0.2.16 Strata has a new folder layout: the engine lives under `engine/`, the server under `terminal/`. `patch/anwenden.py`, `bau/bauen.sh` and `xtx_bauen.py` recognise both layouts by themselves. Only the build image needs the right folder, because it reads Strata's `requirements.txt`: `Strata/terminal` from v0.2.16, `Strata` up to v0.2.15. The image holds tools only and can be used for both versions.

## A new Strata version

```sh
python3 xtx_bauen.py v<new> --quelle Strata --paket <package-new> --ziel <output>
```

`patch/anwenden.py` inserts the change at anchor lines of the original. If an anchor is gone in the new source, it stops and names it instead of patching halfway, and nothing is built.

A release can change more than anchor lines. With v0.2.16 the folders moved and build options were dropped; I had to follow both in the build script. So after every change I measure again before I use the build: speed with and without the table, the task set and the self-rescue with both models, plus an endurance run.

## Layout

| Path | Content |
|---|---|
| `patch/` | the two new source files and `anwenden.py`, which inserts them into a Strata source tree |
| `bau/` | build image and build script (ROCm 7.10 wheels for gfx110X) |
| `xtx_bauen.py` | fetch, patch, build, assemble |
| branch `xtx-<version>` | Strata at that tag with the patch applied |

## Licence

MIT, as Strata. Strata is the work of Niko1221 and the Strata contributors; see `LICENSE`.
