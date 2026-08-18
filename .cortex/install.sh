#!/bin/sh
# Python setup for the cortex image build.
#
# cortex_docker runs every src/*/.cortex/install.sh it finds in the ros1
# workspace, from that repo's own root. TARGETARCH is amd64 or arm64. A
# non-zero exit fails the image build.
set -e

# Focal only: apt scipy 1.3.3 predates Rotation.as_matrix (scipy 1.4) and
# scipy>=1.11 drops py3.8. The jammy images satisfy the pyproject floors.
python3 -c 'import sys; sys.exit(0 if sys.version_info < (3, 9) else 1)' || exit 0

# --ignore-installed: overlay the apt scipy instead of uninstalling it.
# --no-deps: the image pins numpy (jetson-quirks#1); a bare install would
# drift it to 1.24, so leave deps alone - scipy 1.10 accepts the pin.
pip3 install --ignore-installed --no-deps 'scipy>=1.4,<1.11'
