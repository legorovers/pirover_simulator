# syntax=docker/dockerfile:1
FROM debian:latest
ARG DEBIAN_FRONTEND=noninteractive

# Copy current working directory
COPY ./ /
# Install Dependancies
RUN apt-get update && apt-get install -y python3 python3-pip python3-tk \
            libgl1-mesa-dev xvfb python3-numpy\
            python3-pyglet mesa-utils libgl1-mesa-dri\
            libgl1-mesa-glx


EXPOSE 3000

# Run APP

CMD Xvfb :99 -screen 0 1024x768x16 & python3 pysim.py
