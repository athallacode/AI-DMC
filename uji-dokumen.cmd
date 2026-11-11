@echo off
rem Coba pipeline AI asli dari CMD tanpa backend.
rem   uji-dokumen.cmd data\dummy\sk_penguji.pdf   proses satu berkas atau lebih
rem   uji-dokumen.cmd --akurasi                   jalankan evaluasi data\dummy
setlocal
cd /d "%~dp0"
rem Variabel sistem OLLAMA_HOST bisa berisi alamat bind server, jadi ditimpa untuk proses ini saja.
for /f "tokens=1,* delims==" %%a in ('findstr /b "OLLAMA_HOST= OLLAMA_MODEL=" .env') do set "%%a=%%b"
if defined OLLAMA_HOST if "%OLLAMA_HOST:~0,4%"=="http" goto lanjut
set "OLLAMA_HOST=http://localhost:11434"
:lanjut
set "PYTHONPATH=%~dp0."
set "PYTHONIOENCODING=utf-8"
set "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True"
if "%~1"=="--akurasi" (
  ".venv\Scripts\python.exe" -m pipeline.eval.run_eval --data data\dummy --labels data\dummy\labels.csv
) else (
  ".venv\Scripts\python.exe" -m pipeline.main %*
)
