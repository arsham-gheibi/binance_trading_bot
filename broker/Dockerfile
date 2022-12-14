FROM redis:7.0.6-alpine3.17
LABEL maintainer="Roboland"

COPY ./run.sh /run.sh

USER root

RUN mkdir -p /data && \
    chmod 755 /data && \
    chmod +x /run.sh && \
    adduser --disabled-password --no-create-home broker

ARG BROKER_PASS

ENV BROKER_PASS=${BROKER_PASS}

VOLUME /data

CMD [ "/run.sh" ]
