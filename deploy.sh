#!/bin/bash
# Ushbu skript AWS EC2 serverida yangi kodni avtomatik ishga tushirish (Deploy) uchun xizmat qiladi.
# Har safar GitHub Actions dan deploy buyrug'i kelganda bajariladi.

# Xatolik yuz berganda skriptni darhol to'xtatish (set -e)
set -e

echo "🚀 Yangilanish boshlandi..."

# 1. Virtual muhitni (venv) faollashtirish
source venv/bin/activate

# 2. Yangi kutubxonalarni o'rnatish yoki yangilash
pip install --upgrade pip
pip install -r requirements.txt

# 3. PostgreSQL ma'lumotlar bazasiga yangi migratsiyalarni qo'llash
alembic upgrade head

# 4. FastAPI xizmatini (Systemd daemon) qayta ishga tushirish (Restart)
sudo systemctl restart taskmanager.service

# 5. Sog'lomlik tekshiruvi (GET /health) - Imtihon talabi!
sleep 3
echo "🔍 Health check tekshirilmoqda..."
curl -f http://127.0.0.1:8001/health || (echo "❌ Health check failed!" && exit 1)

echo "✅ Loyiha muvaffaqiyatli yangilandi va serverda to'liq ishlamoqda!"
