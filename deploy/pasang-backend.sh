#!/bin/sh
# Pasang atau perbarui backend AI-DMC langsung di Ubuntu (tanpa Docker), lalu jalankan sebagai layanan systemd.
# Jalankan dari akar repo:   sudo sh deploy/pasang-backend.sh
# Tanpa GPU (OCR lewat CPU): sudo PADDLE_CPU=1 sh deploy/pasang-backend.sh
# Versi CUDA lain:           sudo CUDA=cu118 sh deploy/pasang-backend.sh
set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
PENGGUNA=aidmc
PADDLE_VERSI=3.3.1
PADDLEOCR_VERSI=3.7.0
CUDA=${CUDA:-cu126}
PIP="$AKAR/.venv/bin/python -m pip"

if [ "$(id -u)" -ne 0 ]; then echo "Jalankan dengan sudo."; exit 1; fi
if [ ! -f "$AKAR/.env" ]; then echo "Belum ada $AKAR/.env. Salin dari .env.example lalu isi dulu."; exit 1; fi
cd "$AKAR"

echo "== Paket sistem"
apt-get update -q
apt-get install -y -q python3.12 python3.12-venv libgl1 libglib2.0-0 libgomp1

echo "== Akun layanan $PENGGUNA"
if ! id "$PENGGUNA" >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/ai-dmc --create-home --shell /usr/sbin/nologin "$PENGGUNA"
fi
mkdir -p storage
chown "$PENGGUNA:$PENGGUNA" storage
chmod 750 storage
# .env berisi rahasia: hanya pemiliknya (admin server, untuk docker compose) dan akun layanan yang boleh membaca.
chgrp "$PENGGUNA" .env
chmod 640 .env

echo "== Lingkungan Python"
if [ ! -x .venv/bin/python ]; then python3.12 -m venv .venv; fi
$PIP install -q --upgrade pip
$PIP install -q -r backend/requirements.lock -r backend/requirements-pipeline.lock
if [ "${PADDLE_CPU:-0}" = 1 ]; then
  $PIP install -q "paddlepaddle==$PADDLE_VERSI"
else
  $PIP install -q "paddlepaddle-gpu==$PADDLE_VERSI" -i "https://www.paddlepaddle.org.cn/packages/stable/$CUDA/"
fi
$PIP install -q "paddleocr==$PADDLEOCR_VERSI"

echo "== Cek PaddlePaddle"
.venv/bin/python -c "import paddle; paddle.utils.run_check()"

echo "== Layanan systemd dan perintah kelola"
sed "s#/opt/ai-dmc#$AKAR#g" deploy/ai-dmc-backend.service > /etc/systemd/system/ai-dmc-backend.service
sed "s#/opt/ai-dmc#$AKAR#g" deploy/kelola > /usr/local/bin/kelola
chmod 755 /usr/local/bin/kelola
systemctl daemon-reload
systemctl enable ai-dmc-backend
systemctl restart ai-dmc-backend

echo "== Selesai. Cek dengan:"
echo "   systemctl status ai-dmc-backend"
echo "   curl http://127.0.0.1:8000/health"
