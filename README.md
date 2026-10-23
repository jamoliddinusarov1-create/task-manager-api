# 🚀 Task Manager API — Shaxsiy Loyihalar va Vazifalar Boshqaruvi

**Muallif:** Jamoliddin O‘sarov  
**Loyiha:** Imtihon loyihasi #6 — Task Manager API  
**Texnologiyalar:** FastAPI • SQLAlchemy 2.0 • Pydantic v2 • Alembic • PostgreSQL • JWT • Pytest • GitHub Actions • AWS EC2 • Nginx • Systemd

---

## 📌 1. Loyiha haqida va Asosiy Imkoniyatlar

Task Manager API — har bir foydalanuvchiga o‘zining shaxsiy loyihalari va ularga tegishli vazifalarini to‘liq boshqarish imkoniyatini beruvchi xavfsiz, yuqori unumdorlikka ega backend tizimi.

### 🛡️ Xavfsizlik va Rollar (Multi-tenancy / IDOR Himoyasi)
- **Qat'iy izolyatsiya:** Har bir foydalanuvchi faqat o‘ziga tegishli loyihalar va vazifalarni ko‘ra oladi, tahrirlaydi yoki o‘chiradi.
- **Server-side tekshiruv:** So‘rovdagi `user_id` yoki boshqa parametrlarga ko‘r-ko‘rona ishonilmaydi. Hamma ruxsatlar faqatgina kriptografik jihatdan imzolangan JWT token orqali aniqlanadi.
- **Maxfiylik:** Boshqa foydalanuvchiga tegishli resursga murojaat qilinganda resurs mavjudligini ham bildirmaslik uchun qat’iy `404 Not Found` qaytariladi.

### 💼 Muhim Biznes Qoidalari
1. **Ustuvorlik (Priority) bo'yicha maxsus saralash:**
   - Ustuvorlik darajalari: `low`, `medium`, `high`.
   - Saralash alifbo bo'yicha emas, balki qat'iy mantiqiy tartibda: `high` ➔ `medium` ➔ `low`.
2. **Loyihani o'chirish himoyasi (409 Conflict):**
   - Ichida vazifasi (Task) mavjud bo‘lgan loyihani o‘chirish so‘ralganda, tizim bog'langan ma'lumotlar yo'qolmasligi uchun `409 Conflict` xatoligini qaytaradi.
3. **Muddati o‘tgan vazifalar (Overdue):**
   - Faqat `deadline < hozirgi vaqt` VA `bajarilmagan` (hali yopilmagan) vazifalar overdue hisoblanadi.
   - Bajarilgan eski vazifalar hech qachon overdue ro‘yxatiga kirmaydi! Vaqtlar `UTC` timezone bilan aniq hisoblanadi.
4. **Vazifa statusi:**
   - Vazifa bajarilgan deb belgilanganda `completed_at` joriy UTC vaqt bilan to‘ldiriladi.
   - Vazifa qayta ochilganda `completed_at = null` qilib tozalanadi.
5. **Shaxsiy statistika:**
   - Foydalanuvchining jami, bajarilgan, bajarilmagan va muddati o‘tgan vazifalar soni alohida statistika endpointida taqdim etiladi.

---

## 🗄️ 2. Ma'lumotlar Bazasi Modellari (ERD)

- **User:** `id`, `email` (unique, index), `hashed_password`, `full_name`, `is_active`, `created_at`, `updated_at`.
- **Project:** `id`, `name`, `description`, `user_id` (FK ➔ `users.id`), `created_at`, `updated_at`.
- **Task:** `id`, `title`, `description`, `priority` (Enum), `deadline` (DateTime TZ), `completed_at` (Nullable DateTime TZ), `project_id` (FK ➔ `projects.id`), `user_id` (FK ➔ `users.id`), `created_at`, `updated_at`.

---

## ⚙️ 3. O‘rnatish va Mahalliy Ishga Tushirish (Arch Linux / Linux)

### 1. Repozitoriyni klonlash:
```bash
git clone https://github.com/USERNAME/task-manager-api.git
cd task-manager-api
```

### 2. Virtual muhit yaratish va kutubxonalarni o‘rnatish:
```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Muhit o‘zgaruvchilarini sozlash:
```bash
cp .env.example .env
# .env faylini ochib bazangiz paroli va SECRET_KEY ni kiriting
```

### 4. PostgreSQL bazasini tayyorlash:
```bash
sudo -u postgres psql -c "CREATE USER task_user WITH PASSWORD 'task_password';"
sudo -u postgres psql -c "CREATE DATABASE task_db OWNER task_user;"
sudo -u postgres psql -c "CREATE DATABASE task_test_db OWNER task_user;"
```

### 5. Alembic migratsiyalarini qo‘llash:
```bash
alembic upgrade head
```

### 6. Serverni ishga tushirish:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Swagger UI: `http://localhost:8000/docs`  
Health Check: `http://localhost:8000/health`

---

## 🧪 4. Avtomatik Testlar (Pytest)

Loyiha uchun 18 dan ortiq qamrovli testlar yozilgan. Ular registratsiya, JWT xavfsizligi, muddati o'tgan tokenlar, ikki foydalanuvchi o'rtasidagi ma'lumotlar izolyatsiyasi, 409 xatoliklar, overdue mantiqi va saralashni to'liq tekshiradi:

```bash
pytest -v
```

---

## 🌐 5. Asosiy API Endpointlar va Namuna So‘rovlar

### Autentifikatsiya:
- `POST /api/v1/auth/register` — Ro‘yxatdan o‘tish
  ```json
  {
    "email": "jamoliddin@example.com",
    "password": "StrongPassword123!",
    "full_name": "Jamoliddin O'sarov"
  }
  ```
- `POST /api/v1/auth/login` — JWT token olish (JSON yoki OAuth2 Form)
  ```json
  {
    "email": "jamoliddin@example.com",
    "password": "StrongPassword123!"
  }
  ```
- `GET /api/v1/users/me` — Joriy foydalanuvchi profili (`Authorization: Bearer <TOKEN>`)

### Loyihalar (Projects):
- `POST /api/v1/projects` — Yangi loyiha yaratish
- `GET /api/v1/projects?skip=0&limit=20` — Foydalanuvchining barcha loyihalari
- `GET /api/v1/projects/{id}` — Loyiha tafsiloti
- `PUT /api/v1/projects/{id}` — Loyihani tahrirlash
- `DELETE /api/v1/projects/{id}` — O‘chirish (agar vazifasi bo‘lsa `409 Conflict`)

### Vazifalar (Tasks):
- `POST /api/v1/tasks` — Yangi vazifa yaratish
  ```json
  {
    "title": "Alembic migratsiyalarini sozlash",
    "description": "Barcha modellar uchun indeks va jadvallar yaratish",
    "priority": "high",
    "deadline": "2026-10-25T18:00:00Z",
    "project_id": 1
  }
  ```
- `GET /api/v1/tasks?sort_by=priority` — Vazifalarni saralab olish (`high` ➔ `medium` ➔ `low`)
- `GET /api/v1/tasks?completed=false` — Faqat bajarilmaganlarni olish
- `GET /api/v1/tasks/overdue` — Muddati o‘tgan vazifalar ro‘yxati
- `GET /api/v1/tasks/stats` — Statistika (jami, bajarilgan, bajarilmagan, overdue)
- `PATCH /api/v1/tasks/{id}/status` — Statusni o‘zgartirish (`{"completed": true}`)
- `DELETE /api/v1/tasks/{id}` — Vazifani o‘chirish

---

## 🚀 6. CI/CD Pipeline (GitHub Actions)

Loyiha `.github/workflows/ci-cd.yml` fayli orqali to‘liq avtomatlashtirilgan:
1. **Pull Request yoki Push (main):**
   - GitHub Actions da real PostgreSQL servisi ko‘tariladi.
   - Kod sintaksisi va sifati (`flake8`) tekshiriladi.
   - Barcha 18 ta test avtomatik ishga tushadi. Agar bitta test yiqilsa ham, deploy jarayoni darhol to‘xtatiladi.
2. **EC2 Avtomatik Deploy:**
   - Testlar muvaffaqiyatli o‘tgach, SSH orqali AWS EC2 serverga ulanadi.
   - Eng so‘nggi kod olinadi (`git pull origin main`).
   - `alembic upgrade head` orqali yangi migratsiyalar qo‘llanadi.
   - `sudo systemctl restart taskmanager` buyrug‘i bilan backend yangilanadi.
   - `curl -f http://127.0.0.1:8000/health` orqali serverning 100% sog‘lomligi tekshiriladi.

---

## ☁️ 7. AWS EC2 va Nginx Sozlamalari

### Systemd orqali xizmatni uzluksiz yurgizish:
Fayl: `/etc/systemd/system/taskmanager.service`
```ini
[Unit]
Description=FastAPI Task Manager Application Service
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/task-manager-api
EnvironmentFile=/home/ubuntu/task-manager-api/.env
ExecStart=/home/ubuntu/task-manager-api/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```
Xizmatni yoqish:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now taskmanager
```

### Nginx Reverse Proxy:
Fayl: `/etc/nginx/sites-available/taskmanager`
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Nginx ni faollashtirish:
```bash
sudo ln -s /etc/nginx/sites-available/taskmanager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🎯 8. Himoya va Imtihon Ko‘rsatmasi (Live Demo)

Imtihonda o‘qituvchiga amalda ko‘rsatiladigan ssenariy:
1. **Foydalanuvchi 1** ro‘yxatdan o‘tib, o‘zining loyihasi va vazifasini yaratadi.
2. **Foydalanuvchi 2** ro‘yxatdan o‘tadi va Foydalanuvchi 1 ning loyihasini yoki vazifasini ko‘rishga urinadi ➔ Tizim qat'iy `404 Not Found` qaytaradi.
3. Foydalanuvchi 1 vazifasi bor loyihani o‘chirishga uringanda ➔ Tizim `409 Conflict` qaytaradi.
4. O‘tmish sanasi berilgan eski vazifa bajarilgan deb belgilanganda ➔ U `/tasks/overdue` ro‘yxatidan chiqib ketadi (faqat yopilmagan eski vazifalar overdue bo‘ladi).
5. Vazifalar saralanganda ➔ `high` birinchi, keyin `medium`, eng oxirida `low` chiqadi.
