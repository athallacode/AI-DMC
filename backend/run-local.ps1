# Jalankan backend di host dengan pipeline asli (OCR + Ollama lokal). Database lewat: docker compose up -d db
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $PSScriptRoot
# Variabel sistem mengalahkan .env. OLLAMA_HOST sistem bisa berisi alamat bind server (0.0.0.0:11434),
# jadi nilainya ditimpa khusus untuk proses ini dengan nilai dari .env.
$ollamaHost = (Select-String -Path "$root\.env" -Pattern '^OLLAMA_HOST=(.+)$').Matches[0].Groups[1].Value
$env:OLLAMA_HOST = $ollamaHost
$env:PYTHONPATH = $root
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = 'True'
$python = "$root\.venv\Scripts\python.exe"
& $python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m app.seed
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
