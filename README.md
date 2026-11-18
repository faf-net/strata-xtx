# strata-xtx

Strata for one Radeon RX 7900 XTX under Linux: the engine reads prompts about twice as fast without a single switch in the run configuration.

[Deutsche Fassung](README.de.md)

This is an unofficial derivative of [Strata](https://github.com/Niko1221/Strata) (MIT). It is not a Strata release, and questions about it belong here, not upstream. The change is small: 207 lines in five files on top of Strata v0.2.15.

## What it does

Strata's engine carries a number of switches (environment variables) for the prompt path that are off by default on this card generation, because several of them change the rounding. On newer cards Strata turns comparable ones on by itself. This build does the same for one case:

- Linux, exactly one visible GPU, that GPU a discrete `gfx1100` card (RX 7900 XTX or XT).
- In that case the engine turns on 27 of its own switches and lets a bare `--prefill auto` take chunks of up to 32,768 tokens.
- Everything else runs the code it always ran: two cards, any other architecture, an integrated GPU, Windows.

Three more things:

- **Your setting wins.** A switch you set yourself, to any value, is never overridden.
- **One way out.** `STRATA_GFX1100_DEFAULTS=0` turns the whole table off, and the chunk rule with it.
- **Self-rescue.** If the engine reports non-finite values and Strata's own retry does not help, the server starts the engine once more without the table and keeps running in the slower, exact mode.

The engine prints one line at its start that names the build (`xtx-1`) and one line that lists the switches it set, so a log always says what ran. `strata --version` is unchanged.

## What I measured

Hardware: RX 7900 XTX in an OCuLink x4 dock on a UGREEN iDX6011 Pro (62 GiB RAM), card in my quiet power setting. Model: Qwen3.8-Flash-Next IQ3_XXS, once plain and once as the variant with a control vector and image input. All figures measured on 18 Nov 2026; the setup is described in [ugreen-idx6011-egpu-llm](https://github.com/faf-net/ugreen-idx6011-egpu-llm).

Reading a prompt, tokens per second (mean of two rounds):

| Prompt | Plain model, table off | Plain model, this build | With control vector, this build |
|---|---:|---:|---:|
| 4K | 798 | 839 | 776 |
| 16K | 1,382 | 2,357 | 2,242 |
| 58K | 1,313 | 2,952 | 2,884 |
| 128K | – | 3,053 | 2,978 |
| 250K | – | 2,904 | 2,870 |

- **Same speed as setting the switches by hand.** The Strata 0.2.14 release with the switches in the run configuration read 840 / 2,357 / 2,952 tokens per second at 4K / 16K / 58K.
- **Writing is unchanged** within the scatter of the test: 58 to 63 tokens per second in every variant.
- **Quality:** my task set scores 97 of 102 (plain) and 98 of 102 (with control vector), the same as the release. A hidden number was found in every long prompt.
- **Endurance:** 90 minutes of mixed requests on the model with control vector: 1,246 requests, none failed, 178 of 178 hidden numbers found, no non-finite value in the engine log.
- **Self-rescue:** with Strata's built-in fault injection the server restarted the engine once without the table and answered the following requests.
- **Cost:** about 0.6 GiB more host RAM after loading. Answers are not bit-identical to the engine without the table.

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
docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile Strata
python3 xtx_bauen.py v0.2.15 --quelle Strata --paket <package> --ziel <output>
```

The result is `<output>/engine` and `<output>/control`, used like the release packages. The first build takes about five minutes on eight cores, a rebuild about one. The branch `xtx-0.2.15` of this repository is the patched source, if you would rather read or build that.

## A new Strata version

```sh
python3 xtx_bauen.py v0.2.16 --quelle Strata --paket <package-0.2.16> --ziel <output>
```

`patch/anwenden.py` inserts the change at anchor lines of the original. If an anchor is gone in the new source, it stops and names it instead of patching halfway, and nothing is built.

## Layout

| Path | Content |
|---|---|
| `patch/` | the two new source files and `anwenden.py`, which inserts them into a Strata source tree |
| `bau/` | build image and build script (ROCm 7.10 wheels for gfx110X) |
| `xtx_bauen.py` | fetch, patch, build, assemble |
| branch `xtx-<version>` | Strata at that tag with the patch applied |

## Licence

MIT, as Strata. Strata is the work of Niko1221 and the Strata contributors; see `LICENSE`.
