#!/bin/bash

MAINTAINER=$USER
IMAGE_NAME="metagpt"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
IMAGE=$MAINTAINER/$IMAGE_NAME
TAG=latest
NAME="${MAINTAINER}_${IMAGE_NAME}"

    # -v ${HOME}/.cache:${HOME}/.cache \

docker run -it \
    --privileged \
    --cap-add SYS_ADMIN \
    --security-opt seccomp=unconfined \
    --net host \
    --ipc host \
    --gpus all \
    --shm-size=200g \
    --name ${NAME} \
    -v ${HOME}/workspace:${HOME}/workspace \
    -v ${HOME}/config:${HOME}/config \
    -v ${HOME}/.ssh:${HOME}/.ssh \
    -v /mnt:/mnt \
	-v /var/run/docker.sock:/var/run/docker.sock \
    ${IMAGE}:${TAG} bash
