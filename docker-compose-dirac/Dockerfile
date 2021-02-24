#
#   Extension docker image to contain Docker-compose, curl and bash
#       to run the tests scripts in.
#
#.......................................................................
FROM docker:latest

RUN apk add --update py3-pip python3-dev libffi-dev openssl-dev gcc libc-dev make curl bash git py3-cryptography && \
    pip install docker-compose && \
    rm -rf /var/cache/apk/*

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sh"]
