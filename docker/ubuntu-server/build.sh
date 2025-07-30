#!/bin/bash

docker build . \
	--build-arg UID=$(id -u) \
	--build-arg GID=$(id -g) \
	--build-arg USERNAME=$USER \
	-t ${USER}/metagpt:latest
