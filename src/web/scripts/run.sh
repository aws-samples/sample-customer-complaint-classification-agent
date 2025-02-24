#!/bin/bash

# Make sure you're running this script from the /web directory in this repository.

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
echo -e "$SCRIPT_PATH\n"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists streamlit; then
    echo -e "Dependencies missing, running install.sh\n"
    bash install.sh
fi

pushd "$SCRIPT_PATH" || echo "pushd failed to save script directory." && exit
cd ..
pwd
streamlit run app.py
popd || exit
