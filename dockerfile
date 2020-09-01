FROM ubuntu:20.04
LABEL maintainer="psiinon@gmail.com"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -q -y --fix-missing curl git python3-pip

RUN pip3 install --upgrade python-owasp-zap-v2.4

WORKDIR /zap

copy wavsep wivet vulnerableApp /zap/
