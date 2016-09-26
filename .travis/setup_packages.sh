#!/usr/bin/env bash
set -ex

if [[ "${TRAVIS_OS_NAME}" == 'osx' ]]; then # OS X
    brew update

    # easier to find path
    brew install coreutils

    # pyenv dependencies
    brew install autoconf openssl pkg-config readline xz
fi
# No need to setup packages in Linux build
