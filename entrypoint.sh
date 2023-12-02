#!/bin/sh
set -e

if [ "$1" = 'cac' ]; then
    python -u /cac/app.py
    exit
fi

exec "$@"