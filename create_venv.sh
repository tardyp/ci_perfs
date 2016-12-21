VERSION="0.8.14"

virtualenv sandbox_$VERSION
. sandbox_$VERSION/bin/activate
pip install "buildbot[bundle]==$VERSION"
