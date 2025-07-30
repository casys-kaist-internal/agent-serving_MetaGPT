#!/bin/bash

set -e

log() {
    echo "=================================================="
    echo ">>> $1"
    echo "=================================================="
}

BASE_DIR=~/workspace/agent-serving_MetaGPT

log "Agreement to Anaconda TOS"
# conda config --set anaconda_tos_key yes
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

log "Creating Conda virtual environment 'metagpt' (Python 3.10)"
conda create -n metagpt python=3.10 -y

log "Installing 'metagpt'"
conda run -n metagpt python -m pip install --upgrade pip
conda run -n metagpt pip install -e .
log "'metagpt' installation complete"


log "Creating Conda virtual environment 'vllm' (Python 3.10)"
conda create -n vllm python=3.10 -y

log "Installing 'vllm'"
VLLM_DIR="$BASE_DIR/external/agent-serving_vllm"
cd "$VLLM_DIR"

conda run -n vllm python -m pip install --upgrade pip
conda run -n vllm pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
conda run -n vllm python use_existing_torch.py
conda run -n vllm pip install -r requirements/build.txt
conda run -n vllm pip install --no-build-isolation -e .
log "'vllm' installation complete"

# --- Final completion message ---
log "All virtual environment setup has been successfully completed."
echo "Available Conda environments:"
conda env list
echo "
To activate the 'metagpt' environment: conda activate metagpt
To activate the 'vllm' environment:    conda activate vllm
"