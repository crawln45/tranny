#!/bin/bash
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done

# Current script directory
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# Virtualenv destination dir
VIRTENV_DIR="$DIR/virtenv"

virtualenv2 $VIRTENV_DIR
source $VIRTENV_DIR/bin/activate
pip install -r requirements.txt
