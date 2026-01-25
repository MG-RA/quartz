$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
  throw "Not in a git repository."
}

$irrev = Join-Path $repoRoot "irrev\\.venv\\Scripts\\irrev.exe"
if (-not (Test-Path $irrev)) {
  throw "Missing $irrev. Run: cd irrev; uv sync"
}

$vault = Join-Path $repoRoot "content"
$outDir = Join-Path $vault "meta\\graphs"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$conceptsSvg = Join-Path $outDir "concepts-only.svg"
$allNotesSvg = Join-Path $outDir "all-notes.svg"
$conceptsHtml = Join-Path $outDir "concepts-only.htm"
$allNotesHtml = Join-Path $outDir "all-notes.htm"

& $irrev -v $vault graph --concepts-only --format svg --out $conceptsSvg | Out-Null
& $irrev -v $vault graph --all-notes --format svg --out $allNotesSvg | Out-Null
& $irrev -v $vault graph --concepts-only --format html --out $conceptsHtml | Out-Null
& $irrev -v $vault graph --all-notes --format html --out $allNotesHtml | Out-Null

Write-Host "Wrote:"
Write-Host " - $conceptsSvg"
Write-Host " - $allNotesSvg"
Write-Host " - $conceptsHtml"
Write-Host " - $allNotesHtml"
