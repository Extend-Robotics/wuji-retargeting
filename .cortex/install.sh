#!/bin/sh
set -e
cd "$(dirname "$0")/.."

# --ignore-installed: overlay apt scipy; --no-deps: don't drift the image's numpy pin
pip3 install --ignore-installed --no-deps -r requirements_py38.txt
