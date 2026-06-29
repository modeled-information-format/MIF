---
name: Daily Documentation Review
description: |
  Daily review of repository documentation validity against github.com, githubnext.com, and gh-aw resources.
on:
  schedule:
    - cron: 'daily'
  workflow_dispatch:

permissions:
  contents: read
  issues: read

network:
  allowed:
    - "*.github.com"
    - "github.com"
    - "*.githubnext.com"
    - "githubnext.com"
    - "api.github.com"
    - "github.blog"

sandbox:
  agent: awf  # Migrated from deprecated network setting
engine:
  id: copilot

timeout-minutes: 60

tools:
  bash:
    - ls
    - find
    - grep
    - cat
  edit: {}
  web-fetch: {}
  cache-memory:

safe-outputs:
  create-pull-request:
    title-prefix: "docs: "
    draft: false
---

# Daily Documentation Review

## Context
This workflow performs a daily review of the repository's documentation to ensure accuracy and freshness. It validates content against authoritative external sources.

## Instructions
1. **Initialize**: Read from your memory to see which files and links were checked recently.
2. **Scan Documentation**: Read through the `docs/` directory and `README.md`.
3. **Verify Claims**: For each key technical claim or feature description:
   - **Skip** if verified successfully within the last 3 days (check memory).
   - otherwise use `web-fetch` to check `github.com` and `githubnext.com` pages for the latest information.
   - Check the `github/gh-aw` project for updates if relevant.
4. **Report Findings**:
   - If inaccuracies are found, **edit the files** to correct them.
   - Create a **Pull Request** with the fixes. Use the `create-pull-request` tool.
   - If all documentation is up-to-date, output a summary of checks performed.
5. **Update Memory**: Record the current date for the files/claims verified in this run.

## External Verification
Use `web-fetch` to confirm details. Prioritize official GitHub sources.
If you need to check a specific URL, use `web-fetch`.