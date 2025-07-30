# MetaGPT with a local vLLM Server

This guide provides step-by-step instructions to set up and run a  MetaGPT that utilizes a local, vLLM-powered, OpenAI-compatible server as its API server. The entire environment is containerized using Docker for consistency and isolation.

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
cd agent-serving_MetaGPT/docker/ubuntu-server

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

Now, run the setup script to create two separate Conda environments: `metagpt` and `vllm` (MetaGPT and vLLM are installed in each env respectively). This process isolates dependencies and can take around 20 minutes depending on your server's environment.

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
  model: "Qwen/Qwen3-8B"  # IMPORTANT: Change this to the model you are serving with vLLM
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