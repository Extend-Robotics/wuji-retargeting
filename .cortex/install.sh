#!/bin/sh
# Python dependencies for the cortex image build.
#
# cortex_docker runs every src/*/.cortex/install.sh it finds in the ros1
# workspace, from that repo's own root; arch-dependent steps probe
# dpkg --print-architecture themselves. A non-zero exit fails the image build.
set -e

# --ignore-installed: overlay the apt scipy instead of uninstalling it.
# --no-deps: the image pins numpy (jetson-quirks#1); a bare install would
# drift it to 1.24, so leave deps alone - scipy 1.10 accepts the pin.
# The py3.8 marker inside the file makes this a no-op on jammy.
pip3 install --ignore-installed --no-deps -r requirements_py38.txt
