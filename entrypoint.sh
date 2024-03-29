#!/usr/bin/env bash

if [[ ! -z "${REDIS_URL}" ]]; then
    PONG=`redis-cli -u ${REDIS_URL} ping | grep PONG`
    while [ -z "$PONG" ]; do
        sleep 2
        echo "Waiting for redis server to become available..."
        PONG=`redis-cli -u ${REDIS_URL} ping | grep PONG`
    done
fi

until flask db upgrade
do
    echo "Waiting for postgres server to become available..."
    sleep 2
done

gunicorn -c gunicorn.conf.py project:app
