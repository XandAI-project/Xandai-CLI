## 🎉 Release v2.1.8

### ✨ Features
- **Improved File Creation Priority**: Now prompts to save file **BEFORE** asking to execute code
- **Enhanced Detection**: Recognizes requests like 'create api in flask', 'make express server', etc.
- **Cursor Command**: Added `cursor` to terminal command interceptors (alongside `code`)
- **Better Code Extraction**: Properly removes XML tags from file content in task mode

### 🐛 Bug Fixes
- Fixed issue where code was asked to run but file was not created
- Fixed code tags (`<code>`) being included in saved files during task mode
- Improved file creation detection to include API/app/framework keywords

### 📦 Installation
```bash
pip install --upgrade xandai-cli
```

### 🔗 Links
- [PyPI Package](https://pypi.org/project/xandai-cli/2.1.8/)
- [Documentation](https://github.com/XandAI-project/XandAI-CLI#readme)

### 🙏 Contributors
Thank you to everyone who contributed to this release!
