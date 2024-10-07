# syntax=docker/dockerfile:1
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

# Copy current working directory
COPY ./ /
# Install Dependancies
RUN apt-get update && apt-get install -y python3 python3-pip python3-tk libgl1-mesa-dev xvfb
RUN pip install -r requirements.txt

ENV DISPLAY=:99

# Run APP

CMD Xvfb :99 -screen 0 1024x768x16 & python3 pysim.py

