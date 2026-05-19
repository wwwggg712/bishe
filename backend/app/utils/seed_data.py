import json
import os
from decimal import Decimal
from urllib.parse import quote

from ..extensions import db
from ..models.product import Product
from ..models.task import Task
from ..models.user import User


DEMO_USERS = (
    {
        "username": "admin_demo",
        "password": "demo123",
        "role": "admin",
        "nickname": "Admin Demo",
        "region": "华北",
    },
    {
        "username": "merchant_demo",
        "password": "demo123",
        "role": "merchant",
        "nickname": "Merchant Demo",
        "region": "华东",
    },
    {
        "username": "customer_demo",
        "password": "demo123",
        "role": "customer",
        "nickname": "Customer Demo",
        "region": "华南",
    },
)

DEMO_PRODUCTS = (
    {
        "name": "轻量跑鞋",
        "category": "运动鞋",
        "brand": "CloudStep",
        "price": Decimal("299.00"),
        "stock": 120,
    },
    {
        "name": "透气训练T恤",
        "category": "运动服饰",
        "brand": "CloudStep",
        "price": Decimal("129.00"),
        "stock": 200,
    },
    {
        "name": "智能运动手环",
        "category": "智能设备",
        "brand": "PulseOne",
        "price": Decimal("399.00"),
        "stock": 80,
    },
    {
        "name": "健身瑜伽垫",
        "category": "健身器材",
        "brand": "HomeFit",
        "price": Decimal("89.00"),
        "stock": 160,
    },
    {
        "name": "竞速碳板跑鞋",
        "category": "运动鞋",
        "brand": "AeroRun",
        "price": Decimal("699.00"),
        "stock": 48,
    },
    {
        "name": "缓震越野跑鞋",
        "category": "运动鞋",
        "brand": "TrailPeak",
        "price": Decimal("459.00"),
        "stock": 76,
    },
    {
        "name": "速干压缩短裤",
        "category": "运动服饰",
        "brand": "MotionLab",
        "price": Decimal("159.00"),
        "stock": 168,
    },
    {
        "name": "加绒训练卫衣",
        "category": "运动服饰",
        "brand": "UrbanSprint",
        "price": Decimal("239.00"),
        "stock": 112,
    },
    {
        "name": "GPS 运动手表",
        "category": "智能设备",
        "brand": "PulseOne",
        "price": Decimal("899.00"),
        "stock": 42,
    },
    {
        "name": "骨传导运动耳机",
        "category": "智能设备",
        "brand": "SoundFly",
        "price": Decimal("329.00"),
        "stock": 94,
    },
    {
        "name": "可调节哑铃组",
        "category": "健身器材",
        "brand": "PowerCore",
        "price": Decimal("599.00"),
        "stock": 36,
    },
    {
        "name": "折叠壶铃",
        "category": "健身器材",
        "brand": "HomeFit",
        "price": Decimal("219.00"),
        "stock": 88,
    },
    {
        "name": "轻量徒步背包",
        "category": "户外装备",
        "brand": "TrailPeak",
        "price": Decimal("269.00"),
        "stock": 73,
    },
    {
        "name": "防风冲锋衣",
        "category": "户外装备",
        "brand": "WildCamp",
        "price": Decimal("499.00"),
        "stock": 51,
    },
    {
        "name": "露营保温水壶",
        "category": "户外装备",
        "brand": "WildCamp",
        "price": Decimal("119.00"),
        "stock": 146,
    },
    {
        "name": "乳清蛋白粉",
        "category": "营养补给",
        "brand": "NutriMax",
        "price": Decimal("259.00"),
        "stock": 134,
    },
    {
        "name": "电解质能量胶",
        "category": "营养补给",
        "brand": "FuelGo",
        "price": Decimal("89.00"),
        "stock": 220,
    },
    {
        "name": "高蛋白代餐棒",
        "category": "营养补给",
        "brand": "NutriMax",
        "price": Decimal("69.00"),
        "stock": 198,
    },
    {
        "name": "家用跳绳垫",
        "category": "居家运动",
        "brand": "HomeFit",
        "price": Decimal("99.00"),
        "stock": 158,
    },
    {
        "name": "弹力阻力带套装",
        "category": "居家运动",
        "brand": "FlexPro",
        "price": Decimal("79.00"),
        "stock": 204,
    },
    {
        "name": "智能健腹轮",
        "category": "居家运动",
        "brand": "CoreUp",
        "price": Decimal("149.00"),
        "stock": 91,
    },
    {
        "name": "跑步腰包",
        "category": "配件周边",
        "brand": "AeroRun",
        "price": Decimal("79.00"),
        "stock": 176,
    },
    {
        "name": "防滑运动袜",
        "category": "配件周边",
        "brand": "CloudStep",
        "price": Decimal("39.00"),
        "stock": 260,
    },
    {
        "name": "快拆运动水杯",
        "category": "配件周边",
        "brand": "MotionLab",
        "price": Decimal("59.00"),
        "stock": 183,
    },
    {
        "name": "平衡训练半球",
        "category": "健身器材",
        "brand": "PowerCore",
        "price": Decimal("179.00"),
        "stock": 67,
    },
    {
        "name": "户外折叠登山杖",
        "category": "户外装备",
        "brand": "TrailPeak",
        "price": Decimal("189.00"),
        "stock": 84,
    },
    {
        "name": "筋膜放松滚轴",
        "category": "居家运动",
        "brand": "FlexPro",
        "price": Decimal("89.00"),
        "stock": 132,
    },
    {
        "name": "运动发带套装",
        "category": "配件周边",
        "brand": "UrbanSprint",
        "price": Decimal("49.00"),
        "stock": 210,
    },
)

DEMO_TASKS = (
    {
        "name": "scheduled_simulation",
        "task_type": "simulation",
        "status": "idle",
    },
    {
        "name": "daily_aggregation",
        "task_type": "analysis",
        "status": "idle",
    },
)

_IMAGE_OVERRIDES = None


def _load_image_overrides():
    global _IMAGE_OVERRIDES
    if _IMAGE_OVERRIDES is not None:
        return _IMAGE_OVERRIDES

    mapping_path = os.path.join(os.path.dirname(__file__), "product_images.json")
    if not os.path.exists(mapping_path):
        _IMAGE_OVERRIDES = {}
        return _IMAGE_OVERRIDES

    try:
        with open(mapping_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle) or {}
    except (OSError, json.JSONDecodeError):
        payload = {}

    _IMAGE_OVERRIDES = payload if isinstance(payload, dict) else {}
    return _IMAGE_OVERRIDES


def _demo_image_url(product_name, category):
    overrides = _load_image_overrides()
    override_url = overrides.get(product_name)
    if override_url:
        return override_url

    prompt = quote(
        f"ecommerce product photo, {product_name}, category {category}, studio lighting, white background, high detail"
    )
    return (
        "https://coreva-normal.trae.ai/api/ide/v1/text_to_image"
        f"?prompt={prompt}&image_size=square"
    )

def seed_demo_data():
    created = {"users": 0, "products": 0, "tasks": 0}

    users_by_username = {}
    for payload in DEMO_USERS:
        user = User.query.filter_by(username=payload["username"]).first()
        if user is None:
            user = User(
                username=payload["username"],
                role=payload["role"],
                nickname=payload["nickname"],
                region=payload["region"],
            )
            user.set_password(payload["password"])
            db.session.add(user)
            created["users"] += 1
        users_by_username[payload["username"]] = user

    db.session.flush()

    merchant = users_by_username["merchant_demo"]
    for payload in DEMO_PRODUCTS:
        product = Product.query.filter_by(name=payload["name"]).first()
        if product is None:
            product = Product(
                merchant_id=merchant.id,
                name=payload["name"],
                category=payload["category"],
                brand=payload["brand"],
                price=payload["price"],
                cost_price=(payload["price"] * Decimal("0.60")).quantize(Decimal("0.01")),
                image_url=_demo_image_url(payload["name"], payload["category"]),
                stock=payload["stock"],
            )
            db.session.add(product)
            created["products"] += 1

    for payload in DEMO_TASKS:
        task = Task.query.filter_by(name=payload["name"]).first()
        if task is None:
            task = Task(
                name=payload["name"],
                task_type=payload["task_type"],
                status=payload["status"],
                owner_id=merchant.id,
            )
            db.session.add(task)
            created["tasks"] += 1

    db.session.commit()

    return created
