#!/usr/bin/env python3
"""
Script de teste para verificar se comandos interativos funcionam
"""

print("🧪 Testing XandAI interactive command handling...")

# Criar um script Python simples que não precisa de input
print("Creating simple script...")

# Primeiro: script não-interativo (deve funcionar normalmente)
with open("example/script-testing/hello_simple.py", "w") as f:
    f.write('''#!/usr/bin/env python3
print("Hello from XandAI!")
print("This is a non-interactive script.")
import math
result = math.sqrt(16)
print(f"Square root of 16 is: {result}")
''')

print("✅ Created hello_simple.py (non-interactive)")

# Segundo: script interativo (deve ser detectado pelo sistema)
with open("example/script-testing/ask_name.py", "w") as f:
    f.write('''#!/usr/bin/env python3
print("🤖 Interactive script started...")
try:
    name = input("What's your name? ")
    age = int(input("What's your age? "))
    print(f"Hello {name}! You are {age} years old.")
    print("This script required user input!")
except (EOFError, KeyboardInterrupt):
    print("Input was interrupted or unavailable.")
    print("This script needs interactive mode to work properly.")
''')

print("✅ Created ask_name.py (interactive - will be detected)")

print()
print("🎯 Now test the fix:")
print("1. Run: python hello_simple.py  (should work normally)")
print("2. Run: python ask_name.py      (should detect as interactive)")
print("3. Run: python add_numbers.py   (should detect as interactive)")
print()
print("The XandAI CLI should now:")
print("- ✅ Detect interactive commands")
print("- 🎛️  Offer execution mode choice") 
print("- 🖥️  Allow full terminal access when needed")
print("- ⚡ Use shorter timeouts to avoid hanging")
