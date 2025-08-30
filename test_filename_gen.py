#!/usr/bin/env python3

from xandai.cli import XandAICLI

# Test the improved filename generation
cli = XandAICLI()

print("Testing filename generation...")

# Test cases that should return None (generic)
result1 = cli._generate_filename('text', 'some random text', 'create a file')
print(f'Generic text: {result1}')

result2 = cli._generate_filename('python', 'print("hello")', 'write some code')  
print(f'Generic python: {result2}')

# Test cases that should work (specific)
result3 = cli._generate_filename('javascript', 'console.log("test")', 'create app.js with hello world')
print(f'Specific JS: {result3}')

result4 = cli._generate_filename('python', 'class UserService:', 'create UserService class')
print(f'Class-based python: {result4}')

result5 = cli._generate_filename('html', '<h1>Home</h1>', 'create index.html homepage')
print(f'HTML homepage: {result5}')

print("Testing complete!")
