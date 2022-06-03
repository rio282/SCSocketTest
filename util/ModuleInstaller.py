#!/usr/bin/env python3
import os


def install_modules() -> None:
    # install modules
    print("[*] Beginning module installation.")
    os.system("pip install -r requirements.txt")

    # clear screen
    os.system(f"{'cls' if os.name == 'nt' else 'clear'}")
    print("[*] Installed modules.")
