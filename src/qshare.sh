#!/bin/bash

script_dir=$(dirname $0)

echo "Script DIR: $script_dir"
if [ -d "$script_dir/venv/bin" ]; then
	source "$script_dir/venv/bin/activate"
fi

"$script_dir/qshare.py" $@

