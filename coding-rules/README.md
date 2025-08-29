# Coding Rules System

This directory contains technology-specific coding rules that are automatically injected into LLM prompts when relevant technologies are detected.

## How It Works

1. **Technology Detection**: The system analyzes user prompts for technology keywords and patterns
2. **Automatic Injection**: When technologies are detected, corresponding rule files are automatically included in the LLM context
3. **Rule Application**: The LLM follows these rules when generating code or solutions

## Available Rules

- `react.md` - React/JSX development guidelines
- `python.md` - Python coding standards and best practices
- `flask.md` - Flask web framework specific rules
- `javascript.md` - Modern JavaScript development guidelines

## Creating New Rules

To create a new rule file:

1. Create a new `.md` file in this directory (e.g., `django.md`)
2. Follow the naming convention: `technology.md`
3. Include comprehensive guidelines for that technology
4. The system will automatically load and use the new rules

## Rule File Structure

Each rule file should include:

- **Project Structure**: Recommended folder/file organization
- **Code Style**: Formatting and naming conventions
- **Best Practices**: Technology-specific recommendations
- **Performance**: Optimization guidelines
- **Testing**: Testing strategies and frameworks
- **Dependencies**: Package management guidelines

## Technology Detection

The system detects technologies using pattern matching on:

- Keywords (e.g., "react", "flask", "python")
- File extensions (e.g., ".py", ".jsx", ".ts")
- Framework-specific terms (e.g., "useState", "app.route", "import")
- Command patterns (e.g., "pip install", "npm install")

## Example Usage

When a user types: "Create a React application with TypeScript"

The system will automatically:
1. Detect "react" and "typescript" technologies
2. Load `react.md` and `typescript.md` rule files
3. Inject these rules into the LLM prompt
4. Generate code following the specified guidelines

## Benefits

- **Consistent Code Quality**: Ensures generated code follows best practices
- **Framework Adherence**: Follows specific framework conventions
- **Reduced Errors**: Prevents common mistakes and anti-patterns
- **Educational**: Teaches users proper coding standards
- **Customizable**: Easy to modify or add new technology rules
