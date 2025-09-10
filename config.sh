#!/bin/bash
# Install virtual environment
mkdir -p .venv
python3 -m venv .venv
source .venv/bin/activate
pip3 install flask flask-cors tqdm

# Download adb
mkdir -p adb
curl -O https://googledownloads.cn/android/repository/platform-tools-latest-darwin.zip
unzip platform-tools-latest-darwin.zip
mv platform-tools adb