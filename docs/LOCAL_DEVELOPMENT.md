# تشغيل المشروع محلياً بأمان

استخدم إعدادات التطوير المحلية حتى لا يتصل المشروع بقاعدة بيانات السيرفر أو بريد الإنتاج.

## أول تشغيل

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate --run-syncdb --settings=project.settings_local
python manage.py runserver 127.0.0.1:8000 --settings=project.settings_local
```

بعدها افتح:

```text
http://127.0.0.1:8000/
```

## التشغيل اليومي

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8000 --settings=project.settings_local
```

## لماذا هذا آمن؟

- يستخدم SQLite محلياً في `db.local.sqlite3`.
- يستخدم `media_local` للملفات المرفوعة محلياً.
- يطبع رسائل البريد في الـ console بدلاً من إرسالها عبر SMTP.
- يعطّل إعادة التوجيه إلى الدومين الرسمي أثناء التطوير.
- لا يحتاج إلى بيانات قاعدة الإنتاج أو حساب البريد.

## أوامر مفيدة

```powershell
python manage.py createsuperuser --settings=project.settings_local
python manage.py check --settings=project.settings_local
python manage.py test --settings=project.settings_local
```
