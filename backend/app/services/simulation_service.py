import random
from datetime import datetime, timedelta
from uuid import uuid4

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..models.product import Product
from ..models.task import Task
from ..models.user import User
from ..utils.log_schema import ACTION_WEIGHTS, DEVICE_TYPES, LOG_ACTIONS, SOURCE_CHANNELS
from ..utils.seed_data import seed_demo_data


class SimulationMemoryStore:
    def __init__(self):
        self.logs = []

    def save(self, logs):
        self.logs.extend(logs)


simulation_memory_store = SimulationMemoryStore()


class SimulationService:
    VALID_CUSTOMER_ACTION_TYPES = {"view", "favorite", "cart", "purchase"}

    def ensure_seed_data(self):
        seed_demo_data()

    def generate_once(self, users, products, batch_size=50):
        actions = list(LOG_ACTIONS)
        action_weights = [ACTION_WEIGHTS[action] for action in actions]
        logs = []
        entities = []

        for _ in range(batch_size):
            user = random.choice(users)
            product = random.choice(products)
            action = random.choices(actions, weights=action_weights, k=1)[0]
            timestamp = datetime.utcnow()
            log = {
                "log_id": str(uuid4()),
                "user_id": user.id,
                "merchant_id": product.merchant_id,
                "product_id": product.id,
                "product_name": product.name,
                "category": product.category,
                "brand": product.brand,
                "price": float(product.price),
                "action_type": action,
                "region": user.region,
                "device_type": random.choice(DEVICE_TYPES),
                "source_channel": random.choice(SOURCE_CHANNELS),
                "session_id": str(uuid4()),
                "stay_duration": random.randint(5, 180),
                "is_new_user": user.created_at >= datetime.utcnow() - timedelta(days=30),
                "timestamp": timestamp.isoformat(timespec="seconds"),
            }
            logs.append(log)
            entities.append(
                BehaviorLog(
                    log_id=log["log_id"],
                    user_id=log["user_id"],
                    merchant_id=log["merchant_id"],
                    product_id=log["product_id"],
                    product_name=log["product_name"],
                    category=log["category"],
                    brand=log["brand"],
                    price=log["price"],
                    action_type=log["action_type"],
                    region=log["region"],
                    device_type=log["device_type"],
                    source_channel=log["source_channel"],
                    session_id=log["session_id"],
                    stay_duration=log["stay_duration"],
                    is_new_user=log["is_new_user"],
                    timestamp=timestamp,
                )
            )

        db.session.add_all(entities)
        db.session.commit()
        return logs

    def generate_once_from_db(self, batch_size=50):
        self.ensure_seed_data()
        users = User.query.filter_by(role="customer").all()
        products = Product.query.all()
        if not users or not products:
            return []
        return self.generate_once(users=users, products=products, batch_size=batch_size)

    def generate_scheduled_batch(self, batch_size=100):
        logs = self.generate_once_from_db(batch_size=batch_size)
        return len(logs)

    def generate_bulk_from_db(self, batch_size=2000):
        return self.generate_once_from_db(batch_size=batch_size)

    def record_customer_action(self, user, product, action_type):
        if action_type not in self.VALID_CUSTOMER_ACTION_TYPES:
            raise ValueError("不支持的用户行为")

        timestamp = datetime.utcnow()
        log = {
            "log_id": str(uuid4()),
            "user_id": user.id,
            "merchant_id": product.merchant_id,
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category,
            "brand": product.brand,
            "price": float(product.price),
            "action_type": action_type,
            "region": user.region,
            "device_type": random.choice(DEVICE_TYPES),
            "source_channel": "customer_page",
            "session_id": str(uuid4()),
            "stay_duration": random.randint(5, 180),
            "is_new_user": user.created_at >= datetime.utcnow() - timedelta(days=30),
            "timestamp": timestamp.isoformat(timespec="seconds"),
        }
        entity = BehaviorLog(
            log_id=log["log_id"],
            user_id=log["user_id"],
            merchant_id=log["merchant_id"],
            product_id=log["product_id"],
            product_name=log["product_name"],
            category=log["category"],
            brand=log["brand"],
            price=log["price"],
            action_type=log["action_type"],
            region=log["region"],
            device_type=log["device_type"],
            source_channel=log["source_channel"],
            session_id=log["session_id"],
            stay_duration=log["stay_duration"],
            is_new_user=log["is_new_user"],
            timestamp=timestamp,
        )
        db.session.add(entity)
        db.session.commit()
        return log

    def list_tasks(self):
        self.ensure_seed_data()
        tasks = Task.query.filter_by(task_type="simulation").order_by(Task.id.asc()).all()
        return [
            {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "task_type": task.task_type,
                "lastRunAt": task.last_run_at.isoformat(timespec="seconds") if task.last_run_at else "未执行",
            }
            for task in tasks
        ]

    def start_simulation(self, task_name="scheduled_simulation", batch_size=100):
        self.ensure_seed_data()
        task = Task.query.filter_by(name=task_name, task_type="simulation").first()
        if task is None:
            task = Task(name=task_name, task_type="simulation", status="idle")
            db.session.add(task)
            db.session.flush()

        generated_count = self.generate_scheduled_batch(batch_size=batch_size)
        task.status = "running"
        task.last_run_at = datetime.utcnow()
        db.session.commit()
        return {
            "generated_count": generated_count,
            "task": {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "lastRunAt": task.last_run_at.isoformat(timespec="seconds"),
            },
        }

    def stop_simulation(self, task_name="scheduled_simulation"):
        self.ensure_seed_data()
        task = Task.query.filter_by(name=task_name, task_type="simulation").first()
        if task is None:
            task = Task(name=task_name, task_type="simulation", status="stopped")
            db.session.add(task)
            db.session.flush()

        task.status = "stopped"
        task.last_run_at = datetime.utcnow()
        db.session.commit()
        return {
            "task": {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "lastRunAt": task.last_run_at.isoformat(timespec="seconds"),
            }
        }
