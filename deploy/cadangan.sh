#!/bin/sh
# Cadangan harian AI-DMC: database (pg_dump dari container db) dan folder storage/.
# Keduanya wajib dicadangkan bersama. Jadwalkan lewat cron root, contoh pukul 02.00:
#   0 2 * * * /opt/ai-dmc/deploy/cadangan.sh >> /var/log/ai-dmc-cadangan.log 2>&1
# Lokasi tujuan bisa diganti: TUJUAN=/media/nas/ai-dmc /opt/ai-dmc/deploy/cadangan.sh
set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
TUJUAN=${TUJUAN:-/mnt/cadangan/ai-dmc}
SIMPAN_HARI=${SIMPAN_HARI:-7}
HARI=$(date +%F)
umask 077

if [ ! -d "$(dirname "$TUJUAN")" ]; then echo "$(date) GAGAL: $(dirname "$TUJUAN") tidak ada. Disk cadangan terpasang?"; exit 1; fi
mkdir -p "$TUJUAN"
cd "$AKAR"

# Tulis ke berkas sementara dulu supaya cadangan setengah jadi tidak terlihat seperti cadangan utuh.
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$TUJUAN/db_$HARI.dump.tmp"
mv "$TUJUAN/db_$HARI.dump.tmp" "$TUJUAN/db_$HARI.dump"
tar czf "$TUJUAN/storage_$HARI.tar.gz.tmp" storage
mv "$TUJUAN/storage_$HARI.tar.gz.tmp" "$TUJUAN/storage_$HARI.tar.gz"

find "$TUJUAN" -name 'db_*.dump' -mtime +"$SIMPAN_HARI" -delete
find "$TUJUAN" -name 'storage_*.tar.gz' -mtime +"$SIMPAN_HARI" -delete

echo "$(date) OK: $(du -h "$TUJUAN/db_$HARI.dump" | cut -f1) database, $(du -h "$TUJUAN/storage_$HARI.tar.gz" | cut -f1) berkas"
