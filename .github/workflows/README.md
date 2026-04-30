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

This workflow uses **Trusted Publishing** (OpenID Connect) for secure authentication with PyPI. No API tokens are stored in GitHub secrets.

#### Setup Instructions

1. **Configure PyPI Trusted Publisher**:
   - Go to your PyPI project: https://pypi.org/manage/project/shepp-lambda-mcp/settings/
   - Navigate to "Publishing" section
   - Click "Add a new publisher"
   - Fill in the following details:
     - **PyPI Project Name**: `shepp-lambda-mcp`
     - **Owner**: Your GitHub username or organization
     - **Repository name**: `shepp-lambda-mcp`
     - **Workflow name**: `publish-to-pypi.yml`
     - **Environment name**: (leave blank)
   - Click "Add"

2. **Verify Permissions**:
   - The workflow requires `id-token: write` permission (already configured)
   - The workflow requires `contents: read` permission (already configured)

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

**Error: "Trusted publishing exchange failure"**
- Verify the trusted publisher is configured correctly on PyPI
- Check that the workflow name matches exactly: `publish-to-pypi.yml`
- Ensure the repository name and owner are correct

**Error: "Version already exists"**
- Update the version in `awslabs/lambda_tool_mcp_server/__init__.py`
- The workflow will skip publishing if the version exists (won't fail)

**Error: "Permission denied"**
- Verify the workflow has `id-token: write` permission
- Check repository settings → Actions → General → Workflow permissions

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
