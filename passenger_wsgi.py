import os
import sys

# تحديد مسار المشروع
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

# تفعيل settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# تهيئة Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
