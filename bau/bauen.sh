#!/bin/sh
# Baut die Engine aus dem hineingemounteten Quelltext (/src) nach /src/build-hip und legt sie nach /aus/strata.
# Läuft im Container strata-bau:rocm-7.10. Es wird nichts nachgeladen. Die Engine sucht ihre ROCm-Bibliotheken
# im eigenen Ordner (RUNPATH $ORIGIN), wie die Release-Pakete: sie wird in einen Engine-Ordner mit diesen Bibliotheken gelegt.
#   JOBS=8      parallele Übersetzungen
#   ZIEL=strata CMake-Ziel
#   TESTS=ON    Tests mitbauen
set -e
V=/opt/venv
SP=$(ls -d $V/lib/python3*/site-packages)
R=$($V/bin/rocm-sdk path --root)
L=$SP/_rocm_sdk_libraries_gfx110X_dgpu
BC=$(ls -d $R/lib/llvm/amdgcn/bitcode $R/amdgcn/bitcode 2>/dev/null | head -1)
export HIP_PLATFORM=amd HIP_COMPILER=clang HIP_RUNTIME=rocclr ROCM_PATH=$R HIP_PATH=$R
export PATH=$R/bin:$R/llvm/bin:$V/bin:$PATH LD_LIBRARY_PATH=$R/lib:$L/lib
cd /src
# Ab v0.2.16 (Ordner engine/) die Optionen von tools/packaging/build_hip_linux.sh, dem Skript der Release-Pakete;
# bis v0.2.15 die aus setup.py.
if [ -d engine/src ]; then QUELLE=engine; EXTRA="-DSTRATA_PORTABLE=ON"
else QUELLE=.; EXTRA="-DSTRATA_PREFILL_MMQ=ON -DSTRATA_Q6K_EXPERTS=ON -DSTRATA_MMQ_KQUANTS=ON -DSTRATA_MMQ=OFF"; fi
cmake -G Ninja -S $QUELLE -B build-hip -DCMAKE_BUILD_TYPE=Release \
  -DSTRATA_ENABLE_HIP=ON -DSTRATA_ENABLE_CUDA=OFF -DSTRATA_BUILD_TESTS=${TESTS:-OFF} $EXTRA \
  -DCMAKE_HIP_ARCHITECTURES=gfx1100 -DCMAKE_HIP_COMPILER=$R/llvm/bin/clang++ -DCMAKE_HIP_COMPILER_ROCM_ROOT=$R \
  "-DCMAKE_PREFIX_PATH=$R;$L" "-DCMAKE_HIP_FLAGS=--rocm-path=$R --rocm-device-lib-path=$BC" \
  -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON '-DCMAKE_INSTALL_RPATH=$ORIGIN'
cmake --build build-hip --target ${ZIEL:-strata} -j "${JOBS:-8}"
if [ -f build-hip/strata ]; then install -m 755 build-hip/strata /aus/strata; /aus/strata --version; fi
