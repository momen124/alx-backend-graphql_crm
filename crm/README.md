# CRM Celery Setup and Usage

1. **Install Redis**

On Ubuntu:
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server.service
sudo systemctl start redis-server.service

2. **Install dependencies**

pip install -r requirements.txt

3. **Run migrations**

python manage.py migrate

4. **Start Celery worker**

celery -A crm worker -l info

5. **Start Celery beat scheduler**

celery -A crm beat -l info

6. **Verify logs**

Check `/tmp/crm_report_log.txt` for the weekly report logs.

---

You can configure and customize schedules via `CELERY_BEAT_SCHEDULE` in `crm/settings.py`.
