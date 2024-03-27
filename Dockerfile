FROM alpine:latest

RUN apk update && \
    apk add --no-cache make gcc musl-dev

ENV HOME /home/user
RUN mkdir -p ${HOME}
WORKDIR ${HOME}
