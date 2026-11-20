// src/core/gfx1100_defaults.cpp - see include/strata/core/gfx1100_defaults.hpp.
#include "strata/core/gfx1100_defaults.hpp"

#include "strata/kernels/gfx_arch.hpp"

#include <cstdio>
#include <cstdlib>

namespace strata::core {

bool gfx1100_defaults_on(const char* gcn_arch, bool integrated, int n_devices, bool windows) {
    if (windows || integrated || n_devices != 1) return false;
    if (!strata::kernels::gfx_arch_is(gcn_arch, "gfx1100")) return false;
    const char* off = std::getenv("STRATA_GFX1100_DEFAULTS");
    return !(off != nullptr && off[0] == '0');
}

bool gfx1100_defaults_on(const char* gcn_arch, bool integrated, int n_devices) {
#if defined(_WIN32)
    return gfx1100_defaults_on(gcn_arch, integrated, n_devices, true);
#else
    return gfx1100_defaults_on(gcn_arch, integrated, n_devices, false);
#endif
}

std::vector<std::pair<std::string, std::string>> gfx1100_default_env(const char* gcn_arch, bool integrated, int n_devices, bool windows) {
    std::vector<std::pair<std::string, std::string>> t;
    if (!gfx1100_defaults_on(gcn_arch, integrated, n_devices, windows)) return t;
    t = {
        // the prompt's attention and block selection on the matrix cores
        {"STRATA_HIP_WMMA", "1"},
        {"STRATA_SELECT_WMMA", "1"},
        {"STRATA_PA_FAST", "1"},
        // the prompt's experts and projections: fused kernels, FP16 products
        {"STRATA_PF_FUSED", "1"},
        {"STRATA_PF_GEMM", "1"},
        {"STRATA_PF_PAD", "1"},
        {"STRATA_PF_F16", "2"},
        {"STRATA_PF_HCDOWN", "1"},
        {"STRATA_HC_UPMIX", "1"},
        {"STRATA_QFUSE", "1"},
        {"STRATA_FUSE_CONVAB", "1"},
        {"STRATA_CVEC_FUSE", "1"},       // a steered layer's write, control vector and next norm in one pass (only acts with a control vector)
        // the prompt's gated DeltaNet recurrence
        {"STRATA_GDN_CHUNKED", "1"},
        {"STRATA_GDN_HEAD", "1"},
        {"STRATA_GDN_PP", "1"},
        {"STRATA_GDN_CONVL2", "1"},
        {"STRATA_GDN_NOY", "1"},
        // who does what, and the buffers in between
        {"STRATA_PREFILL_CPU_SHARE", "0.6"},
        {"STRATA_PREFILL_CPU_SHARE_MAX", "4096"},
        {"STRATA_PREFILL_RING", "384"},
        {"STRATA_STAGER_RING", "64"},
        {"STRATA_KV_HOST_DMA", "1"},
        {"STRATA_ADAPT_OVERLAP", "1"},
        {"STRATA_SH_STREAM", "0"},
        // the decode window
        {"STRATA_QSA_ROWS", "1"},
        {"STRATA_VERIFY_QDEDUP", "1"},
        {"STRATA_HEAD_MIX_MULTI", "1"},
    };
    return t;
}

std::vector<std::string> apply_gfx1100_defaults(const char* gcn_arch, bool integrated, int n_devices) {
    std::vector<std::string> set;
#if defined(_WIN32)
    const bool windows = true;
#else
    const bool windows = false;
#endif
    for (const auto& kv : gfx1100_default_env(gcn_arch, integrated, n_devices, windows)) {
        if (std::getenv(kv.first.c_str()) != nullptr) continue;   // the user's setting wins, whatever it is
#if defined(_WIN32)
        _putenv_s(kv.first.c_str(), kv.second.c_str());
#else
        setenv(kv.first.c_str(), kv.second.c_str(), 0);
#endif
        set.push_back(kv.first);
    }
    if (!set.empty()) {
        std::fprintf(stderr, "strata: gfx1100 (one RX 7900 XTX / XT): %zu prompt-path switches on by default (about twice the prompt speed; "
                             "answers differ in the last bits; STRATA_GFX1100_DEFAULTS=0 turns them off; a switch you set is kept): ", set.size());
        for (size_t i = 0; i < set.size(); ++i) std::fprintf(stderr, "%s%s", i ? " " : "", set[i].c_str() + 7);
        std::fprintf(stderr, "\n");
    }
    return set;
}

int64_t gfx1100_chunk_ceiling(const char* gcn_arch, bool integrated, int n_devices) {
    return gfx1100_defaults_on(gcn_arch, integrated, n_devices) ? 32768 : 0;
}

}  // namespace strata::core
