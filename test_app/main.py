#!/usr/bin/env python3
"""
Test Application
================

A simple test application for demonstrating the build system.
"""

import argparse
import sys
from datetime import datetime


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="Test Application")
    parser.add_argument("--version", action="version", version="1.0.0")
    parser.add_argument("--name", default="World", help="Name to greet")
    parser.add_argument("--count", type=int, default=1, help="Number of greetings")

    args = parser.parse_args()

    print(f"Hello {args.name}!")
    print(f"Current time: {datetime.now()}")
    print(f"Python version: {sys.version}")

    for i in range(args.count):
        print(f"Greeting {i+1}: Hello {args.name}!")

    print("Application completed successfully!")


if __name__ == "__main__":
    main()
