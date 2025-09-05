# 📦 PyPI Release Guide for XandAI

This guide explains how to configure and use the automated PyPI publishing workflow.

## 🔧 Initial Setup

### 1. PyPI Account Setup

1. Create accounts on both:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [Test PyPI](https://test.pypi.org/account/register/) (testing)

2. Generate API tokens:
   - Go to Account Settings → API tokens
   - Create a new token with scope "Entire account" or specific to your project
   - **Save the token securely** - you won't see it again!

### 2. GitHub Repository Secrets

Add the following secrets to your GitHub repository:

**Repository Settings → Secrets and variables → Actions**

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `PYPI_API_TOKEN` | `pypi-...` | Your PyPI API token for production releases |
| `TEST_PYPI_API_TOKEN` | `pypi-...` | Your Test PyPI API token for testing (optional) |

### 3. Repository Settings

1. **Enable Actions**: Go to Settings → Actions → General
   - Allow all actions and reusable workflows
   - Allow GitHub Actions to create and approve pull requests

2. **Branch Protection** (recommended):
   - Protect main branch
   - Require status checks to pass
   - Require branches to be up to date

## 🚀 Making a Release

### Method 1: Command Line (Recommended)

```bash
# 1. Ensure you're on main branch and up to date
git checkout main
git pull origin main

# 2. Update version in setup.py
# Edit setup.py and change version="2.1.0" to your new version

# 3. Create and push tag
git add setup.py
git commit -m "Bump version to v2.1.1"
git tag -a v2.1.1 -m "Release v2.1.1"
git push origin main
git push origin v2.1.1
```

### Method 2: GitHub Web Interface

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Click "Choose a tag" → Type new tag (e.g., `v2.1.1`)
4. Select "Create new tag on publish"
5. Fill in release title and description
6. Click "Publish release"

## 🔄 Workflow Process

When you push a tag, the workflow will:

1. **Test Phase** (runs on Python 3.8, 3.9, 3.10, 3.11):
   - Install dependencies
   - Run linting (flake8)
   - Check code formatting (black, isort)
   - Run tests (pytest)
   - Test package installation

2. **Build Phase**:
   - Build source distribution and wheel
   - Validate package with twine
   - Upload build artifacts

3. **Publish Phase** (only for tags):
   - Download build artifacts
   - Publish to PyPI using API token
   - Create GitHub release with artifacts

## 🧪 Testing Releases

### Test on Test PyPI First

To test with Test PyPI before production:

1. Uncomment this line in `workflow.yml`:
   ```yaml
   # repository-url: https://test.pypi.org/legacy/
   ```

2. Change the secret name to `TEST_PYPI_API_TOKEN`

3. Make a test release with a pre-release tag:
   ```bash
   git tag v2.1.1-rc1
   git push origin v2.1.1-rc1
   ```

4. Test installation:
   ```bash
   pip install -i https://test.pypi.org/simple/ xandai==2.1.1rc1
   ```

### Manual Testing

Before making a release, test locally:

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Build package locally
python -m build

# Check package
twine check dist/*

# Test local installation
pip install dist/xandai-*.whl
```

## 📋 Pre-Release Checklist

- [ ] Update version in `setup.py`
- [ ] Update `README.md` if needed
- [ ] Run tests locally: `pytest`
- [ ] Check code quality: `flake8 .` and `black --check .`
- [ ] Test package build: `python -m build`
- [ ] Test installation: `pip install dist/xandai-*.whl`
- [ ] Update changelog/release notes
- [ ] Commit version bump
- [ ] Create and push tag

## 🔍 Monitoring Releases

### Check Workflow Status

1. Go to Actions tab in your repository
2. Click on the latest "Build and Publish to PyPI" run
3. Monitor each job (Test → Build → Publish → Create Release)

### Verify PyPI Release

1. Check your package page: `https://pypi.org/project/xandai/`
2. Verify the new version is listed
3. Test installation: `pip install xandai==<new_version>`

## 🐛 Troubleshooting

### Common Issues

1. **"Package already exists"**
   - Each version can only be uploaded once
   - Bump version and try again

2. **"Authentication failed"**
   - Check API token is correct
   - Ensure token has proper permissions
   - Token might be expired

3. **"Tests failed"**
   - Fix failing tests before release
   - Check Python compatibility

4. **"Build failed"**
   - Check dependencies in `requirements.txt`
   - Verify `setup.py` configuration

### Debug Mode

Enable debug output by adding to workflow:
```yaml
- name: Debug info
  run: |
    python --version
    pip list
    ls -la dist/
```

## 🔒 Security Best Practices

1. **Protect Tokens**:
   - Never commit API tokens to code
   - Use GitHub repository secrets
   - Rotate tokens periodically

2. **Trusted Publishing** (Advanced):
   - Configure PyPI trusted publisher
   - Remove API token requirement
   - Enhanced security

3. **Branch Protection**:
   - Protect main branch
   - Require reviews for releases
   - Prevent direct pushes

## 📚 Additional Resources

- [PyPI Documentation](https://packaging.python.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Packaging Guide](https://packaging.python.org/en/latest/)
- [Semantic Versioning](https://semver.org/)

## 📞 Support

If you encounter issues:
1. Check the Actions tab for detailed error logs
2. Review this guide for common solutions
3. Create an issue in the repository
4. Check PyPI status page for service issues
