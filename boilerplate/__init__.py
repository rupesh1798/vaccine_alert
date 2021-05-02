import os

from dotenv import load_dotenv

PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(PROJECT_BASE_DIR, '.env'))

from .celery import app as celery_app

__all__ = ('celery_app',)
