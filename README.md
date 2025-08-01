# MetaGPT with a local vLLM Server

This guide provides step-by-step instructions to set up and run a  MetaGPT that utilizes a local, vLLM-powered, OpenAI-compatible server as its API server. The entire environment is containerized using Docker for consistency and isolation.

## Table of Contents

- [Setup & Installation](#setup--installation)
  - [1. Build and Launch the Docker Container](#1-build-and-launch-the-docker-container)
  - [2. First-Time Setup Inside the Container](#2-first-time-setup-inside-the-container)
  - [3. Set Up Virtual Environments](#3-set-up-virtual-environments)
- [Running the Application](#running-the-application)
  - [Terminal 1: Start the vLLM Server](#terminal-1-start-the-vllm-server)
  - [Terminal 2: Run MetaGPT](#terminal-2-run-metagpt)
- [Running Benchmarks (HumanEval & MBPP)](#running-benchmarks-humaneval--mbpp)
  - [Initial Setup for Benchmarks](#initial-setup-for-benchmarks)
  - [Configure Models for Benchmarking](#configure-models-for-benchmarking)
  - [Run HumanEval Benchmark](#run-humaneval-benchmark)
  - [Run MBPP Benchmark](#run-mbpp-benchmark)
  - [View Benchmark Results](#view-benchmark-results)

## Setup & Installation

Follow these steps to build the Docker image, set up the container, and install all necessary dependencies.

### 1. Build and Launch the Docker Container

First, clone the repository and run the provided scripts to build the Docker image and launch the initial container.

```bash
# Create a workspace directory and navigate into it
mkdir ~/workspace
cd ~/workspace

# Clone the project repository
git clone https://github.com/casys-kaist-internal/agent-serving_MetaGPT.git
cd agent-serving_MetaGPT
# ---- submodules setup
git submodule init
git submodule udpate --recursive

cd docker/ubuntu-server

# Build the Docker image
./build.sh

# IMPORTANT: configure mounting parameters at `launch.sh` script before launching it.
# Launch the container. This will drop you directly into the container's terminal.
./launch.sh
```

### 2. First-Time Setup Inside the Container

Once you are inside the container's terminal, you need to perform a one-time setup to install Miniconda.

```bash
# Run the Miniconda installation script
# The installer will prompt you for input at several points.
# Follow this sequence: ENTER -> yes -> ENTER -> yes
bash ~/Miniconda3-py310_25.5.1-1-Linux-x86_64.sh

# Activate the new shell configuration
source ~/.bashrc

# Clean up the installation script
rm Miniconda3-py310_25.5.1-1-Linux-x86_64.sh 
```

### 3. Set Up Virtual Environments

Now, run the setup script to create two separate Conda environments: `metagpt` and `vllm` (MetaGPT and vLLM are installed in each env respectively). This process isolates dependencies and can take around 30 minutes depending on your server's environment.

```bash
# Navigate to the project root
cd workspace/agent-serving_MetaGPT/

# Make the setup script executable
chmod +x set_virtual.sh

# Run the script to create and configure the Conda environments
./set_virtual.sh

# After the script completes, exit the container. The initial setup is now complete.
exit
```

## Running the Application

To run the application, you will need **two separate terminals**. One will run the vLLM server, and the other will run the MetaGPT.

### Terminal 1: Start the vLLM Server

```bash
# Start and attach to the container
docker start -ai ${USER}_metagpt

# Activate the vLLM conda environment
conda activate vllm

# Load environment variables (e.g., model name)
# IMPORTANT: Change VLLM_MODEL_NAME in .envrc file to the model you will serve with vLLM
source /home/${USER}/workspace/agent-serving_MetaGPT/.envrc

# Serve the model using vLLM
# This example uses a tensor-parallel-size of 2.
# Adjust this line as needed for your setup.
vllm serve $VLLM_MODEL_NAME --tensor-parallel-size 2
```

> **Keep this terminal open.** The vLLM server must remain running for MetaGPT to make API calls to it.

### Terminal 2: Run MetaGPT

```bash
# Open a new shell in the running container
docker exec -it ${USER}_metagpt /bin/bash

# Activate the MetaGPT conda environment
conda activate metagpt
```

#### Configure MetaGPT

You need to tell MetaGPT to use your local vLLM server. Open and edit the `config/config2.yaml` file to match the following:

```yaml
# Path: ~/workspace/agent-serving_MetaGPT/config/config2.yaml

llm:
  api_type: "openai"
  model: "Qwen/Qwen3-4B"  # IMPORTANT: Change this to the model you are serving with vLLM
  base_url: "http://127.0.0.1:8000/v1"
  api_key: "token-abc123"
```

#### Run MetaGPT Examples

Now you are ready to run MetaGPT.

```bash
# Navigate to the project root
cd workspace/agent-serving_MetaGPT

# 1. Test basic server communication with a simple example
python examples/hello_world.py

# 2. Run the full Software Company multi-agent system to create a game
# The --n-round parameter ensures the simulation runs long enough to complete the project.
cd metagpt
python software_company.py "Make a cli number guessing game that can be played. The computer should pick a random number between 1 and 100. The user then guesses the number, and the computer tells them if their guess is too high or too low. The game ends when the user guesses the correct number, and it should tell them how many guesses it took." --n_round 25
```

You have now successfully set up and run a multi-agent MetaGPT system powered by your local vLLM server!

## Running Benchmarks (HumanEval & MBPP)

This section details how to run MetaGPT's `aflow` optimization framework to evaluate LLM performance on HumanEval and MBPP datasets using your vLLM backend. The vLLM server launching (Terminal 1) remains the same as described above.

### Initial Setup for Benchmarks

In your **MetaGPT Terminal (Terminal 2)**, perform the following steps for benchmark-specific setup:

```bash
# Ensure you are in the MetaGPT conda environment
conda activate metagpt

# Install necessary libraries for benchmark evaluation (e.g., sympy for MATH, python-box for general utility)
pip install sympy python-box

# Navigate to the project root
cd ~/workspace/agent-serving_MetaGPT/
```

### Configure Models for Benchmarking

For `aflow` benchmarks, MetaGPT uses a slightly different model configuration within `config2.yaml`, typically under a `models` section for more fine-grained control over various LLMs.

**IMPORTANT:** You must ensure the model names used in your benchmark commands (`--opt_model_name`, `--exec_model_name`) match an entry in this `models` section.

Open and edit your `config/config2.yaml` file to include a `models` section:

```yaml
# Path: ~/workspace/agent-serving_MetaGPT/config/config2.yaml

# Ensure this section is at the top level
llm:
  api_type: "openai"
  model: "Qwen/Qwen3-4B" # This is your default model for general MetaGPT tasks
  base_url: "http://127.0.0.1:8000/v1"
  api_key: "token-abc123"

# Add this 'models' section for aflow benchmarks
models:
  "Qwen/Qwen3-4B": # IMPORTANT: This name must match the model served by vLLM AND used in benchmark commands
    api_type: "openai"
    base_url: "http://127.0.0.1:8000/v1"
    api_key: "token-abc123"
    temperature: 0 
CALC_USAGE: True 
```

### Run HumanEval Benchmark

Execute the following command in **Terminal 2 (MetaGPT terminal)** to run the HumanEval benchmark.

```bash
# IMPORTANT:
# - `--if_first_optimize True` should ONLY be set to True for the very first run across ALL benchmarks.
#   For subsequent runs (even if you change dataset), set it to False.
# - `--opt_model_name` and `--exec_model_name` MUST match an entry under the `models` section in config2.yaml.
# - The model specified in `--exec_model_name` is the one whose performance is being measured.

python -m examples.aflow.optimize --dataset HumanEval \
--sample 4 \
--optimized_path metagpt/ext/aflow/scripts/optimized \
--initial_round 1 \
--max_rounds 20 \
--check_convergence True \
--validation_rounds 5 \
--if_first_optimize False \
--opt_model_name Qwen/Qwen3-4B \
--exec_model_name Qwen/Qwen3-4B
```

### Run MBPP Benchmark

Execute the following command in **Terminal 2 (MetaGPT terminal)** to run the MBPP benchmark.

```bash
# IMPORTANT:
# - `--if_first_optimize True` should ONLY be set to True for the very first run across ALL benchmarks.
#   For subsequent runs (even if you change dataset), set it to False.
# - `--opt_model_name` and `--exec_model_name` MUST match an entry under the `models` section in config2.yaml.
# - The model specified in `--exec_model_name` is the one whose performance is being measured.

python -m examples.aflow.optimize --dataset MBPP \
--sample 4 \
--optimized_path metagpt/ext/aflow/scripts/optimized \
--initial_round 1 \
--max_rounds 20 \
--check_convergence True \
--validation_rounds 5 \
--if_first_optimize False \
--opt_model_name Qwen/Qwen3-4B \
--exec_model_name Qwen/Qwen3-4B
```

### View Benchmark Results

The benchmark results, including performance scores and optimization details, will be saved under the specified `--optimized_path`.

---

**Crucial Note on Model Configuration:**
When changing the model for your experiments, you **MUST** ensure consistency across all relevant configuration points:
1.**`.envrc` file**: `VLLM_MODEL_NAME` (for vLLM server startup)
2.**`config/config2.yaml`**: Both `llm.model` (default for general MetaGPT) and the model name under the `models` section (for `aflow` specific use).
3.**Benchmark Command**: `--opt_model_name` and `--exec_model_name` parameters.

This ensures that vLLM is serving the correct model, and MetaGPT's `aflow` framework is configured to use it properly for both optimization and execution phases.
