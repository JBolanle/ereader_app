# Repo

Help me manage the GitHub repository using gh CLI.

## View Repository Info

```bash
# View repo details
gh repo view

# View in browser
gh repo view --web

# View specific sections
gh repo view --json name,description,url
```

## Create a New Repository

### From current directory
```bash
# Create and push existing local repo
gh repo create [name] --source=. --push

# Options
gh repo create [name] \
  --source=. \
  --push \
  --private \           # or --public
  --description "Description here"
```

### Create empty repo on GitHub
```bash
gh repo create [name] --private
```

### Create from template
```bash
gh repo create [name] --template owner/template-repo
```

## Clone a Repository

```bash
# Clone by name (from your account or org)
gh repo clone [name]

# Clone any repo
gh repo clone owner/repo

# Clone and cd into it
gh repo clone [name] -- --depth=1  # shallow clone
```

## Fork a Repository

```bash
# Fork and clone
gh repo fork owner/repo --clone

# Fork only (don't clone)
gh repo fork owner/repo
```

## Repository Settings

### View current settings
```bash
gh repo view --json isPrivate,defaultBranchRef,description
```

### Edit settings
```bash
# Change description
gh repo edit --description "New description"

# Change visibility
gh repo edit --visibility private
gh repo edit --visibility public

# Enable/disable features
gh repo edit --enable-issues=true
gh repo edit --enable-wiki=false
```

### Manage topics/tags
```bash
gh repo edit --add-topic python,ereader,learning
gh repo edit --remove-topic old-topic
```

## Branch Protection (if you have admin access)

View in browser to configure:
```bash
gh repo view --web
# Then go to Settings > Branches
```

## Collaborators

```bash
# List collaborators
gh api repos/{owner}/{repo}/collaborators

# Add collaborator (opens browser)
gh repo view --web
# Then go to Settings > Collaborators
```

## Releases

```bash
# List releases
gh release list

# Create a release
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes here"

# Create release from tag
gh release create v1.0.0 --generate-notes

# Upload assets to release
gh release upload v1.0.0 ./dist/*.whl
```

## Repository Secrets (for CI/CD)

```bash
# List secrets
gh secret list

# Set a secret
gh secret set SECRET_NAME

# Set from file
gh secret set SECRET_NAME < secret.txt
```

## GitHub Actions

```bash
# List workflows
gh workflow list

# View workflow runs
gh run list

# View specific run
gh run view [run-id]

# Watch a run in progress
gh run watch

# Re-run a failed workflow
gh run rerun [run-id]
```

## Quick Links

```bash
# Open repo in browser
gh repo view --web

# Open issues
gh issue list --web

# Open pull requests
gh pr list --web

# Open actions
gh run list --web

# Open specific file in browser
gh browse src/ereader/models/book.py
```

## Sync Fork with Upstream

```bash
# Sync your fork
gh repo sync

# Sync specific branch
gh repo sync --branch main
```

## Archive/Delete

```bash
# Archive (read-only, reversible)
gh repo archive

# Delete (irreversible!)
gh repo delete [name] --yes
```

## What Would You Like to Do?

Tell me:
- Set up a new repo?
- Configure settings?
- Manage releases?
- Check CI/CD status?
