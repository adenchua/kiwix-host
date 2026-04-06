#!/bin/bash
set -e
redis-server --daemonize yes
exec python download.py "$@"
