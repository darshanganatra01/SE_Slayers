import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

def make_celery(app_name=__name__):
    broker = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    celery = Celery(
        app_name,
        broker=broker,
        backend=backend,
        include=['app.api.ai_feature.tasks']
    )
    return celery

celery_app = make_celery("se_slayers_celery")
