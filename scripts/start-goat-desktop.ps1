param(
  [switch]$Check
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SrcPath = Join-Path $RepoRoot "src"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $VenvPython) {
  $Python = $VenvPython
} else {
  $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if (-not $PythonCommand) {
    throw "Python was not found. Install Python 3.12+ or create .venv before starting GOAT Desktop."
  }
  $Python = $PythonCommand.Source
}

if (-not (Test-Path -LiteralPath (Join-Path $SrcPath "goat_desktop\__main__.py"))) {
  throw "GOAT Desktop source path is missing: $SrcPath"
}

$oldPythonPath = $env:PYTHONPATH
if ($oldPythonPath) {
  $env:PYTHONPATH = "$SrcPath;$oldPythonPath"
} else {
  $env:PYTHONPATH = $SrcPath
}

if ($Check) {
  [pscustomobject]@{
    ok = $true
    repoRoot = $RepoRoot
    python = $Python
    pythonPathStartsWithSrc = $env:PYTHONPATH.StartsWith($SrcPath)
    module = "goat_desktop"
    entry = "goat_desktop.__main__:main"
  } | ConvertTo-Json -Compress
  exit 0
}

& $Python -m goat_desktop
exit $LASTEXITCODE
