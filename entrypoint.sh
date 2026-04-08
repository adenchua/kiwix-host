#!/bin/bash
set -e
redis-server --daemonize yes
if [ "$1" = "convert" ]; then
    shift
    exec python convert.py "$@"
else
    exec python download.py "$@"
fi
