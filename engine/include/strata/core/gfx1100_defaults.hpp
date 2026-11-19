// include/strata/core/gfx1100_defaults.hpp - prompt-path defaults for ONE discrete RX 7900 XTX / XT (gfx1100) under Linux.
//
// The table turns on switches that already exist in the engine and are opt-in on this architecture.  It is applied only
// when exactly one GPU is visible, that GPU is a discrete gfx1100 card and the host is Linux: two cards, any other
// architecture (gfx1101 / gfx1102 included: not measured), an integrated GPU and Windows run the code they always ran.
//
// Why they are a default here: measured on an RX 7900 XTX in an OCuLink x4 dock (UGREEN iDX6011 Pro, 62 GiB RAM),
// Qwen3.8-Flash-Next IQ3_XXS native pack, engine 0.1.60, 17 / 18 Nov 2026, each against the same engine without them:
//   prompt   4K 789 -> 1,632 tok/s, 16K 1,406 -> 2,365, 58K 1,341 -> 3,048, 250K 205 s -> 87 s (with a control vector: 201 s -> 90 s)
//   decode   chat 65.6 -> 72.5 tok/s, agent 75.8 -> 82.4
//   quality  task set 98 and 97 of 102 without and with (two runs each); 32 of 32 hidden numbers found at 70K-250K
//   load     90 minutes of mixed requests twice (plain model, and with a control vector and image input): no failed request, no non-finite value
//   cost     about 0.6 GiB more host RAM after loading; the card draws 25 to 30 W more while reading a prompt, the same while writing
// Several switches change the rounding (FP16 operands on the matrix cores), so answers are not bit-identical to the
// engine without the table.  A switch the user set (to anything) is never overridden; STRATA_GFX1100_DEFAULTS=0 turns
// the whole table off, and with it the chunk rule below.
#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace strata::core {

/// This build's own name, printed once at engine start (stderr) so a log always says which engine wrote it.
/// `strata --version` is left as upstream prints it: the updater and setup read that line.
inline constexpr const char* kGfx1100Build = "xtx-1";

/// Whether the gfx1100 single-card defaults apply: Linux, exactly one visible device, discrete, gcn_arch "gfx1100",
/// and STRATA_GFX1100_DEFAULTS is not "0".  A pure rule apart from the one environment read, so a test can check it.
bool gfx1100_defaults_on(const char* gcn_arch, bool integrated, int n_devices, bool windows);
bool gfx1100_defaults_on(const char* gcn_arch, bool integrated, int n_devices);

/// The table: empty unless gfx1100_defaults_on().
std::vector<std::pair<std::string, std::string>> gfx1100_default_env(const char* gcn_arch, bool integrated, int n_devices, bool windows);

/// Sets the table in this process's environment where the user has not set the variable, prints one line to stderr
/// when it set anything and returns the names it set.  Call once, before apply_arch_defaults and before any engine
/// code reads its switches.
std::vector<std::string> apply_gfx1100_defaults(const char* gcn_arch, bool integrated, int n_devices);

/// The ceiling a bare `--prefill auto` may reach with the table on (32768, what STRATA_PREFILL_AUTO_MAX=32768 gave in
/// the measurements above); 0 when the table is off.  An explicit --prefill N, auto:N or STRATA_PREFILL_AUTO_MAX wins.
int64_t gfx1100_chunk_ceiling(const char* gcn_arch, bool integrated, int n_devices);

}  // namespace strata::core
