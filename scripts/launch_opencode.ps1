$ErrorActionPreference = "Stop"

$ollama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollama)) {
  $ollama = "ollama"
}

& $ollama launch opencode --model qwen2.5:3b
