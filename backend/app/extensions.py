from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover - fallback for minimal local setup
    class _InMemoryJob:
        def __init__(self, job_id, func, trigger, kwargs):
            self.id = job_id
            self.func = func
            self.trigger = trigger
            self.kwargs = kwargs


    class BackgroundScheduler:
        def __init__(self):
            self._jobs = {}
            self.running = False

        def add_job(
            self,
            func,
            trigger=None,
            id=None,
            replace_existing=False,
            **kwargs,
        ):
            if id is None:
                raise ValueError("job id is required")
            if not replace_existing and id in self._jobs:
                raise ValueError(f"job {id} already exists")
            self._jobs[id] = _InMemoryJob(id, func, trigger, kwargs)
            return self._jobs[id]

        def get_job(self, job_id):
            return self._jobs.get(job_id)

        def get_jobs(self):
            return list(self._jobs.values())

        def start(self):
            self.running = True

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
scheduler = BackgroundScheduler()
