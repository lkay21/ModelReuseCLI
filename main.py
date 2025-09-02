#!/usr/bin/env python3
import argparse
import sys
import os

# document this function
def install_dependencies():
    print("Installing dependencies...")
    success = os.system("pip install -r requirements.txt")
    sys.exit(-1 if success else 0)
    
def main():
    parser = argparse.ArgumentParser(description="ModelReuseCLI main entry point")
    parser.add_argument('option', type=str, help="'install' or URL_FILE")
    args = parser.parse_args()
    if args.option == "install":
        install_dependencies()
    else:
        url_file = args.option
        # add processing here

if __name__ == "__main__":
    main()