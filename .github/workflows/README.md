# GitHub Workflows

This directory contains GitHub Actions workflows for automating the shepp-lambda-mcp package.

## Publish to PyPI

The `publish-to-pypi.yml` workflow automatically publishes the package to PyPI when changes are pushed to the `main` branch.

### Triggers

The workflow runs when:
- Code is pushed to the `main` branch
- Changes are made to:
  - `awslabs/**` (source code)
  - `pyproject.toml` (package configuration)
  - `uv.lock` (dependencies)
- Manually triggered via workflow_dispatch

### Requirements

This workflow uses a **PyPI API Token** stored in GitHub Secrets for authentication.

#### Setup Instructions

1. **Get your PyPI API Token**:
   - Go to PyPI Account Settings: https://pypi.org/manage/account/
   - Scroll to "API tokens" section
   - Click "Add API token"
   - Give it a name (e.g., "GitHub Actions - shepp-lambda-mcp")
   - Set scope to "Project: shepp-lambda-mcp" (recommended) or "Entire account"
   - Click "Add token"
   - **IMPORTANT**: Copy the token immediately (starts with `pypi-`)
   - You won't be able to see it again!

2. **Add Token to GitHub Secrets**:
   - Go to your GitHub repository
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI token (the one starting with `pypi-`)
   - Click "Add secret"

3. **Verify Setup**:
   - The workflow will now use `${{ secrets.PYPI_API_TOKEN }}` to authenticate
   - No additional permissions needed in the workflow

### Workflow Steps

1. **Checkout code**: Clones the repository
2. **Set up Python**: Installs Python 3.11
3. **Install uv**: Installs the uv package manager
4. **Build package**: Builds the distribution packages (wheel and sdist)
5. **Publish to PyPI**: Uploads to PyPI using trusted publishing

### Features

- **Skip existing**: Won't fail if the version already exists on PyPI
- **Automatic versioning**: Uses version from `awslabs/lambda_tool_mcp_server/__init__.py`
- **Secure**: No API tokens needed, uses OpenID Connect
- **Fast**: Uses uv for fast dependency resolution and building

### Manual Trigger

You can manually trigger the workflow:
1. Go to Actions tab in GitHub
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Select the branch (usually `main`)
5. Click "Run workflow"

### Troubleshooting

**Error: "Invalid or non-existent authentication information"**
- Verify the `PYPI_API_TOKEN` secret is set correctly in GitHub
- Check that the token hasn't expired or been revoked
- Ensure the token has the correct scope (project or account)
- Try regenerating the token on PyPI and updating the secret

**Error: "Version already exists"**
- Update the version in `awslabs/lambda_tool_mcp_server/__init__.py`
- The workflow will skip publishing if the version exists (won't fail)

**Error: "Permission denied"**
- Check repository settings → Actions → General → Workflow permissions
- Ensure "Read and write permissions" is enabled for workflows
- Verify the `PYPI_API_TOKEN` secret exists and is accessible

### Version Management

Before pushing to main:
1. Update version in `awslabs/lambda_tool_mcp_server/__init__.py`
2. Update `CHANGELOG.md` with changes
3. Commit and push to main
4. Workflow will automatically publish the new version

### Testing

To test the build locally before pushing:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Build the package
uv build

# Check the built packages
ls -la dist/
```

The built packages will be in the `dist/` directory.
