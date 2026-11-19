# Bauumgebung für Strata (HIP/ROCm) auf der RX 7900 XTX (gfx1100): nur Werkzeuge, kein Quelltext.
# Der Quelltext wird beim Bauen hineingemountet (bauen.sh), damit ein neuer Stand ohne neues Image baut.
#   docker build -t strata-bau:rocm-7.10 -f bau/Dockerfile <Strata-Klon>/terminal     (bis v0.2.15: <Strata-Klon>)
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl git python3 python3-pip python3-venv unzip libatomic1 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ROCm aus AMDs TheRock-Wheels, Version wie Strata sie für gfx110X festlegt (setup.py: ROCM_VERSION_DEFAULT)
ARG ROCM_INDEX=https://rocm.nightlies.amd.com/v2/gfx110X-dgpu/
ARG ROCM_WHEEL=7.10.0a20251120

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt cmake ninja \
    && /opt/venv/bin/pip install --no-cache-dir --index-url "$ROCM_INDEX" "rocm[libraries,devel]==$ROCM_WHEEL"

# "rocm-sdk path --root" packt beim ersten Aufruf die Entwicklerdateien aus (u. a. hip-lang für CMake).
RUN /opt/venv/bin/rocm-sdk path --root

WORKDIR /src
