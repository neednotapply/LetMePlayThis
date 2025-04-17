#!/usr/bin/env python3

import os
import sys
import subprocess

def install_requirements():
    """
    Installs Python dependencies from requirements.txt (in same folder).
    """
    here = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(here, "requirements.txt")

    if not os.path.isfile(req_file):
        print(f"No requirements.txt found at: {req_file}")
        return

    print(f"Upgrading pip and installing dependencies from {req_file}...")
    try:
        # upgrade pip itself
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        # install all requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_requirements()
    print("Finished installing. You can now run python bot.py (if no errors above).")
