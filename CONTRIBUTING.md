# Contributing to XandAI-CLI

First off—thank you for considering contributing! Whether you aim to fix bugs, suggest improvements, or expand features, your support helps make XandAI-CLI stronger and more reliable.

---

##  Code of Conduct

Please follow our [Code of Conduct](#) to maintain an inclusive, respectful, and positive community for all contributors.

---

## How You Can Contribute

### 1. Report Bugs
- Use GitHub Issues to report any bugs.
- Include details such as:
  - XandAI-CLI version (`pip show xandai-cli` or equivalent)
  - Operating system and environment details
  - Steps to reproduce the issue
  - Expected vs. actual behavior
  - Any logs or error messages, and stack traces if available

### 2. Suggest Enhancements
- Submit enhancement requests as issues.
- Describe the proposed feature or improvement, its benefits, and potential implementation approach.

### 3. Submit Pull Requests
- Fork the repository and create a feature branch.
- Ensure your contributions align with the project’s clean, modular architecture and error-handling standards :contentReference[oaicite:1]{index=1}.
- Before committing:
  - Run existing tests and ensure no regressions.
  - Follow existing code style (e.g. formatting, naming conventions).
  - Update `README.md`, `usage.md`, or add tests/documentation where relevant.

### 4. Documentation Updates
- Improvements to `README.md`, `usage.md`, or in-code documentation are valuable!
- Always ensure updates are clear, accurate, and helpful.

---

## Branching & Versioning Strategy

- We use a simple `main` branch—create your pull requests targeting `main`.
- New contributions should be backward-compatible. Major changes may warrant version bumps and release notes.
- Version management via **semantic versioning** is encouraged (e.g., `v1.0.0` → `v1.1.0` for enhancements).

---

## Development Setup

To get started locally:

```bash
git clone https://github.com/XandAI-project/Xandai-CLI.git
cd Xandai-CLI
pip install -e .
