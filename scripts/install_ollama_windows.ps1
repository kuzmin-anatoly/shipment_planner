$ErrorActionPreference = "Stop"

$installer = Join-Path $env:TEMP "OllamaSetup.exe"
Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer
Start-Process -FilePath $installer -ArgumentList "/S" -Wait

$ollamaPath = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
if (Test-Path $ollamaPath) {
  & $ollamaPath --version
} else {
  Write-Host "Ollama installer finished. Open a new terminal if ollama is not immediately on PATH."
}
