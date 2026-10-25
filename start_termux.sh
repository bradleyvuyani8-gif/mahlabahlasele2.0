#!/usr/bin/env bash
set -e

echo "Requesting Termux storage permissions..."
termux-setup-storage || true

echo "Updating Termux environment packages..."
pkg update && pkg upgrade -y

echo "Installing essential system dependencies..."
pkg install -y git python clang make libffi openssl

REPO_DIR="$HOME/mahlabahlasele"

if [ ! -d "$REPO_DIR" ]; then
    echo "Cloning repository..."
    git clone https://github.com/yourusername/mahlabahlasele.git "$REPO_DIR"
fi

cd "$REPO_DIR"

echo "Synchronizing latest commits..."
git pull origin main

chmod +x run.sh
bash run.sh

