#!/bin/bash
set -e

echo "🚀 Yangilanish boshlandi..."

# 1. Virtual muhitni faollashtirish
source venv/bin/activate

# 2. Yangi kutubxonalarni o'rnatish
pip install --upgrade pip
pip install -r requirements.txt

# 3. Bazaga o'zgarishlarni (migratsiyani) qo'llash
alembic upgrade head

# 4. FastAPI xizmatini qayta ishga tushirish (restart)
sudo systemctl restart taskmanager.service

# 5. Sog'lomlik tekshiruvi (GET /health) - Imtihon talabi!
sleep 3
echo "🔍 Health check tekshirilmoqda..."
curl -f http://127.0.0.1:8000/health || (echo "❌ Health check failed!" && exit 1)

echo "✅ Loyiha muvaffaqiyatli yangilandi va serverda to'liq ishlamoqda!"
