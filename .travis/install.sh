#!/usr/bin/env bash
set -ex

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    # Install some custom requirements on OS X
    sudo pip install --upgrade pip
    sudo pip install virtualenv
    sudo pip install virtualenvwrapper
    sudo pip install tox
else
    # Install some custom requirements on Linux
    case "${TOXENV}" in
        py34-32-pyqt5 | py35-32-pyqt5)
            sudo dpkg --add-architecture i386
            sudo apt-get -qq update
            case "${TOXENV}" in
                py34-32-pyqt5)
                    sudo apt-get install -y python3.4:i386
                    ;;
                py35-32-pyqt5)
                    sudo apt-get install -y python3.5:i386
                    ;;
            esac
            wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.18/sip-4.18.tar.gz
            tar -zxvf sip-4.18.tar.gz
            cd sip-4.18 && python configure.py && make && sudo make install && cd ..
            wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.6/PyQt5_gpl-5.6.tar.gz
            tar -zxvf PyQt5_gpl-5.6.tar.gz
            cd PyQt5_gpl-5.6 && python configure.py && make && sudo make install && cd ..
            sudo pip install --upgrade pip
            sudo pip install virtualenv
            sudo pip install virtualenvwrapper
            sudo pip install tox
            ;;
        py34-64-pyqt5 | py35-64-pyqt5)
            pip install --upgrade pip
            pip install virtualenv
            pip install virtualenvwrapper
            pip install tox
            ;;
    esac
fi