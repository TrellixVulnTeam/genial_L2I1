#!/usr/bin/env bash
set -ex

if [[ "${TRAVIS_OS_NAME}" == 'osx' ]]; then
    # Install some custom requirements on OS X
    export QMAKE=/usr/local/Cellar/qt5/5.6.1-1/bin/qmake
    # Initialize pyenv
    eval "$(pyenv init -)"
    pyenv install 3.5.2
    pyenv global 3.5.2
    pyenv versions

else
    # Install some custom requirements on Linux
    # Disable temporarily exit on error
    set +e
    source ~/build/adamscott/genial/.travis/qt56-env.sh
    # Reenable exit on error
    set -e
    # Initialize pyenv
    eval "$(pyenv init -)"
    case "${TOXENV}" in
        py35-32-pyqt5)
            export CONFIGURE_OPTS="--with-arch=i386"
            export CFLAGS="-arch i386"
            export LDFLAGS="-arch i386"
            ;;
        py35-64-pyqt5)
            echo "" > /dev/null
            ;;
    esac
    pyenv install 3.5.2
    pyenv global 3.5.2
    pyenv versions
fi

sudo pip install --upgrade pip
sudo pip install tox

pushd ~
mkdir -p build
pushd build # ~ -> ~/build
SIP_DIR="./sip"
if [ ! "$(ls -A $SIP_DIR)" ]; then
    CACHED_SIP=false
    wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.18/sip-4.18.tar.gz
    tar -zxf sip-4.18.tar.gz
    mkdir -p sip
    mv -v sip-4.18/* sip/
else
    CACHED_SIP=true
fi
pushd sip # ~/build -> ~/build/sip
ls -l
if [ ! "${CACHED_SIP}" = true ]; then
    python configure.py
    make -j3
fi
make install -j3
popd # ~/build/sip -> ~/build

PYQT5_DIR="./PyQt5_gpl"
if [ ! "$(ls -A $PYQT5_DIR)" ]; then
    CACHED_PYQT5=false
    wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.6/PyQt5_gpl-5.6.tar.gz
    tar -zxf PyQt5_gpl-5.6.tar.gz
    mkdir -p PyQt5_gpl
    mv -v PyQt5_gpl-5.6/* PyQt5_gpl/
else
    CACHED_PYQT5=true
fi
pushd PyQt5_gpl # ~/build -> ~/build/PyQt5_gpl
if [ ! "${CACHED_PYQT5}" = true ]; then
    python configure.py --qmake $QMAKE --confirm-license
    make -j3
fi
make install -j3
popd # ~/build/PyQt5_gpl -> ~/build
popd # ~/build -> ~
popd
