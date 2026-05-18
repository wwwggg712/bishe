from datetime import datetime

from flask import current_app

from ..extensions import db, scheduler
from ..models.behavior_log import BehaviorLog
from ..models.task import Task
from ..services.analytics_service import AnalyticsService
from ..services.simulation_service import SimulationService


def run_daily_aggregation():
    service = AnalyticsService()
    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    saved_metrics = service.persist_daily_metrics(logs)
    return {"status": "ok", "saved_metrics": saved_metrics}


def run_scheduled_simulation():
    service = SimulationService()
    task = Task.query.filter_by(name="scheduled_simulation", task_type="simulation").first()
    if task is not None and task.status == "stopped":
        return {"status": "skipped", "generated_count": 0}

    if task is None:
        task = Task(name="scheduled_simulation", task_type="simulation", status="running")
        db.session.add(task)
        db.session.flush()
    else:
        task.status = "running"
        db.session.commit()

    generated_count = service.generate_scheduled_batch()
    task.last_run_at = datetime.utcnow()
    task.status = "success"
    db.session.commit()
    return {"status": "ok", "generated_count": generated_count}


JOB_DEFINITIONS = {
    "scheduled_simulation": {
        "title": "行为日志模拟",
        "task_type": "simulation",
        "schedule": "每1分钟",
        "trigger": "interval",
        "minutes": 1,
        "runner": run_scheduled_simulation,
    },
    "daily_aggregation": {
        "title": "日级聚合",
        "task_type": "analysis",
        "schedule": "每天 00:30",
        "trigger": "cron",
        "hour": 0,
        "minute": 30,
        "runner": run_daily_aggregation,
    },
}


def ensure_job_tasks():
    changed = False

    for job_name, definition in JOB_DEFINITIONS.items():
        task = Task.query.filter_by(name=job_name).first()
        if task is None:
            task = Task(
                name=job_name,
                task_type=definition["task_type"],
                status="idle",
            )
            db.session.add(task)
            changed = True

    if changed:
        db.session.commit()


def register_jobs():
    app = current_app._get_current_object()

    def wrap_with_app_context(runner):
        def _wrapped():
            with app.app_context():
                return runner()

        return _wrapped

    for job_name, definition in JOB_DEFINITIONS.items():
        if scheduler.get_job(job_name) is not None:
            continue

        kwargs = {
            key: value
            for key, value in definition.items()
            if key in {"minutes", "hour", "minute"}
        }
        scheduler.add_job(
            wrap_with_app_context(definition["runner"]),
            trigger=definition["trigger"],
            id=job_name,
            replace_existing=True,
            **kwargs,
        )


def list_jobs():
    ensure_job_tasks()
    tasks = {task.name: task for task in Task.query.all()}
    items = []

    for job_name, definition in JOB_DEFINITIONS.items():
        task = tasks.get(job_name)
        items.append(
            {
                "name": job_name,
                "title": definition["title"],
                "schedule": definition["schedule"],
                "status": task.status if task else "idle",
                "lastRunAt": (
                    task.last_run_at.isoformat(timespec="seconds")
                    if task and task.last_run_at
                    else "未执行"
                ),
            }
        )

    return items


def execute_job(job_name):
    definition = JOB_DEFINITIONS.get(job_name)
    if definition is None:
        raise KeyError(job_name)

    ensure_job_tasks()
    task = Task.query.filter_by(name=job_name).first()
    task.status = "running"
    db.session.commit()

    try:
        result = definition["runner"]()
        task.status = "success"
        return result
    except Exception:
        task.status = "failed"
        raise
    finally:
        task.last_run_at = datetime.utcnow()
        db.session.commit()
