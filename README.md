# strata-xtx

Strata for one Radeon RX 7900 XTX under Linux: the engine reads prompts about twice as fast without a single switch in the run configuration.

[Deutsche Fassung](README.de.md)

This is an unofficial fork of [Strata](https://github.com/Niko1221/Strata) (MIT). It is not a Strata release, and questions about it belong here, not upstream. The change is small: about 200 lines in five files. The current state sits on Strata v0.2.16 (branch `xtx-0.2.16`); v0.2.15 can still be built (branch `xtx-0.2.15`).

## What it does

Strata's engine carries a number of switches (environment variables) for the prompt path that are off by default on this card generation, because several of them change the rounding. On newer cards Strata turns comparable ones on by itself. This build does the same for one case:

- Linux, exactly one visible GPU, that GPU a discrete `gfx1100` card (RX 7900 XTX or XT).
- In that case a table of 27 of the engine's switches applies. The engine newly sets 26 of them, one (`PF_FUSED`) is already on in the release. In addition a bare `--prefill auto` may take chunks of up to 32,768 tokens.
- Everything else runs the code it always ran: two cards, any other architecture, an integrated GPU, Windows.

Three more things:

- **Your setting wins.** A switch you set yourself, to any value, is never overridden.
- **One way out.** `STRATA_GFX1100_DEFAULTS=0` turns the whole table off, and the chunk rule with it.
- **Self-rescue.** If the engine reports non-finite values and Strata's own retry does not help, the server starts the engine once more without the table and keeps running in the slower, exact mode. The request that triggers this ends with an error itself (HTTP 503); the following ones are answered. `STRATA_GFX1100_RESCUE=0` in the `env` of the run config turns this restart off.

The engine prints one line at its start that names the build (`xtx-1`) and one line that lists the switches it set, so a log always says what ran. `strata --version` is unchanged.

## What I measured

Hardware: RX 7900 XTX in an OCuLink x4 dock on a UGREEN iDX6011 Pro (62 GiB RAM), card in my quiet power setting. Model: Qwen3.8-Flash-Next IQ3_XXS, once plain and once as the variant with a control vector and image input. All figures were measured on 18 and 19 Nov 2026 on Strata 0.2.16 unless stated otherwise; the setup is described in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm).

Reading a fresh prompt, tokens per second (median of two to three runs):

| Prompt tokens | Plain model | With control vector | Duration, plain model |
|---|---:|---:|---:|
| 4,077 | 1,470 | 1,438 | 2.8 s |
| 16,254 | 2,404 | 2,290 | 6.8 s |
| 65,025 | 3,021 | 2,925 | 21.5 s |
| 130,026 | 2,968 | 2,933 | 43.8 s |
| 248,054 | 2,907 | 2,890 | 85.4 s |

Against the unchanged 0.2.16 release, measured alternating (Strata's `tools/strata_bench.py --long`, three rounds, each engine loaded fresh, plain model):

| Median | Release 0.2.16 | This build |
|---|---:|---:|
| 4K prompt, tokens/s | 783 | 1,645 |
| 16K prompt, tokens/s | 1,357 | 2,295 |
| 32K prompt, tokens/s | 1,321 | 2,650 |
| chat decode, tokens/s | 69.6 | 72.5 |
| agent decode, tokens/s | 72.3 | 81.7 |

- **The table is the whole difference.** The same build with `STRATA_GFX1100_DEFAULTS=0` reads 16K at about 1,390 and 58K at about 1,320 tokens per second, with the table 2,386 / 2,367 and 3,021 / 2,982.
- **A prompt of 250,000 tokens:** 85 to 87 s with this build (2,838 to 2,917 tokens per second, both models), 204 s on the unchanged release (1,220 tokens per second, with control vector). The number hidden in the prompt was found every time.
- **Writing: equal to slightly faster.** In the alternating comparison this build came out a little above the release in all three rounds in the chat part, and in two of three in the agent part. After long prompts and in continuous writing I see no difference (51 to 59 and 67 to 68 tokens per second).
- **Quality:** my task set scores 97 of 102 (plain) and 96 to 98 of 102 depending on the run (with control vector). On the unchanged release it is the same: two tasks the model passes sometimes, on both (each repeated five times).
- **Endurance:** 90 minutes of mixed requests on the model with control vector: 1,232 requests, none failed, 176 of 176 hidden numbers found, no non-finite value in the engine log.
- **Self-rescue:** with Strata's built-in fault injection the triggering request ended with an error (HTTP 503), the server restarted the engine once without the table and answered the following requests, with both models. A 16K prompt was then read at about 1,300 tokens per second, that is in the slow mode, and the number was found.
- **Power:** while reading, the card draws 25 to 30 W more with the table (292 to 300 W against 267 to 270 W, measured on 18 Nov 2026 against the 0.2.14 release). Because reading takes half as long, the energy per token read is still about half: 0.037 to 0.047 against 0.070 to 0.087 Wh per 1,000 tokens. While writing the power is the same.
- **Cost:** answers are not bit-identical to the engine without the table. On top come about 0.6 GiB more host RAM after loading; I measured that on 18 Nov 2026 with the same switches on the 0.2.14 release and did not break it down again on 0.2.16.
- **On Strata 0.2.15** the same patch read equally fast on 18 Nov 2026 (16K: 2,345 and 2,248, 248K: 2,906 and 2,847 tokens per second).

What I did not measure: the RX 7900 XT, a card in a full PCIe x16 slot, any other model or quant, Windows.

## The switches

`patch/gfx1100_defaults.cpp` is the table. Without the `STRATA_` prefix:

- Attention and block selection of the prompt on the matrix cores: `HIP_WMMA`, `SELECT_WMMA`, `PA_FAST`
- Experts and projections of the prompt: `PF_FUSED`, `PF_GEMM`, `PF_PAD`, `PF_F16=2`, `PF_HCDOWN`, `HC_UPMIX`, `QFUSE`, `FUSE_CONVAB`, `CVEC_FUSE`
- The recurrence of the prompt: `GDN_CHUNKED`, `GDN_HEAD`, `GDN_PP`, `GDN_CONVL2`, `GDN_NOY`
- Division of work and buffers: `PREFILL_CPU_SHARE=0.6`, `PREFILL_CPU_SHARE_MAX=4096`, `PREFILL_RING=192`, `STAGER_RING=64`, `KV_HOST_DMA`, `ADAPT_OVERLAP`, `SH_STREAM=0`
- The decode window: `QSA_ROWS`, `VERIFY_QDEDUP`, `HEAD_MIX_MULTI`

Every one of them exists in the unchanged engine. Strata's documentation describes a part of them; none is a promise. A release may rename or drop one, and the engine ignores an unknown name silently. That is why I test every new version before I use it.

## Build

You need Docker, a clone of Strata and the two release packages of the same version (engine `…-linux-x86_64-hip-rx7900` and control), unpacked into `<package>/engine` and `<package>/control`. The built engine is placed next to the ROCm libraries of the release package.

```sh
git clone https://github.com/Niko1221/Strata.git
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata/terminal
python3 xtx_bauen.py v0.2.16 --quelle Strata --paket <package> --ziel <output>
```

The result is `<output>/engine` and `<output>/control`, used like the release packages. `xtx_bauen.py` creates the branch `xtx-<version>` in the clone and writes the patch into it as a commit; Git needs a name and an e-mail address in the clone for that (`git config user.name`, `user.email`). The branches `xtx-0.2.16` and `xtx-0.2.15` of this repository are the patched source, if you would rather read or build that.

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
