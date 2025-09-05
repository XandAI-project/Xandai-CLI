#!/usr/bin/env python3
print("Interactive script started...")
try:
    name = input("What's your name? ")
    age = int(input("What's your age? "))
    print(f"Hello {name}! You are {age} years old.")
    print("This script required user input!")
except (EOFError, KeyboardInterrupt):
    print("Input was interrupted or unavailable.")
    print("This script needs interactive mode to work properly.")
