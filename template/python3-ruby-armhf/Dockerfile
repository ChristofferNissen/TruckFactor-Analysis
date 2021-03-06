FROM openfaas/classic-watchdog:0.18.1 as watchdog

#FROM python:3-alpine
FROM ruby:alpine

# Allows you to add additional packages via build-arg
ARG ADDITIONAL_PACKAGE

RUN apk add git
RUN apk add python3
RUN python3 --version

# Ruby environment variables
ENV GEM_HOME=/usr/local/bundle
ENV PATH=$PATH:/usr/local/bundle/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN mkdir -p "$GEM_HOME" && chmod 777 "$GEM_HOME"

RUN apk --update add --virtual build_deps \
    build-base \
    libc-dev \
    linux-headers \
    cmake \
    && apk --no-cache add icu-dev libressl-dev \
    && gem install github-linguist \
    && apk del build_deps build-base libc-dev linux-headers cmake

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog
RUN apk --no-cache add ${ADDITIONAL_PACKAGE}

# Add non root user
RUN addgroup -S app && adduser app -S -G app

WORKDIR /home/app/

COPY index.py           .
COPY requirements.txt   .

RUN apk add --update py-pip

RUN chown -R app /home/app && \
  mkdir -p /home/app/py && chown -R app /home/app
USER app
ENV PATH=$PATH:/home/app/.local/bin:/home/app/python/bin/
ENV PYTHONPATH=$PYTHONPATH:/home/app/python

RUN pip install -r requirements.txt --target=/home/app/python

RUN mkdir -p function
RUN touch ./function/__init__.py

WORKDIR /home/app/function/
COPY function/requirements.txt	.

RUN pip install -r requirements.txt --target=/home/app/python

WORKDIR /home/app/

USER root

COPY function           function

# Allow any user-id for OpenShift users.
RUN chown -R app:app ./ && \
  chmod -R 777 /home/app/python

USER app

ENV fprocess="python3 index.py"
EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]

# test that gem file can be found
# RUN git clone https://github.com/Praqma/helmsman
# WORKDIR helmsman
# RUN github-linguist --breakdown
