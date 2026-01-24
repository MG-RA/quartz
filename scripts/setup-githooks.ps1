$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
  throw "Not in a git repository."
}

Push-Location $repoRoot
try {
  git config core.hooksPath .githooks
  Write-Host "Configured git hooks path to .githooks for this repo."
  Write-Host "Hooks active: pre-commit will run registry build + lint."
} finally {
  Pop-Location
}

