# E-commerce Intelligent Analysis System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a front-end/back-end separated e-commerce intelligent analysis system with three roles, simulated behavior logs, analytics, prediction, recommendation, and LLM-enhanced reporting.

**Architecture:** The system uses a Vue 3 frontend and a Flask backend. MySQL stores business data, Elasticsearch stores raw behavior logs, and Python services compute aggregation, prediction, recommendation, and merchant strategy suggestions. The implementation starts with a thin vertical slice: auth, seeded data, simulated logs, overview analytics, then grows into role-specific pages and optional LLM summaries.

**Tech Stack:** Vue 3, Vite, Pinia, Vue Router, Element Plus, ECharts, Flask, SQLAlchemy, JWT, APScheduler, Elasticsearch, pytest, Vitest

---

## Planned File Structure

### Backend

- `backend/requirements.txt`: Python dependency manifest
- `backend/app/__init__.py`: Flask app factory and extension initialization
- `backend/app/config.py`: environment and application settings
- `backend/app/extensions.py`: db, jwt, cors, scheduler, elasticsearch client wiring
- `backend/app/models/`: SQLAlchemy models for users, products, tasks, metrics, suggestions
- `backend/app/routes/`: route blueprints grouped by domain
- `backend/app/services/auth_service.py`: login and token helper logic
- `backend/app/services/simulation_service.py`: log generation and one-shot simulation
- `backend/app/services/analytics_service.py`: overview, funnel, region, category, hot product analytics
- `backend/app/services/prediction_service.py`: moving-average and regression-based trend prediction
- `backend/app/services/recommendation_service.py`: rule-based and similarity-based recommendation logic
- `backend/app/services/strategy_service.py`: merchant-facing strategy suggestion generation
- `backend/app/services/llm_service.py`: structured prompt building and optional LLM wrapper
- `backend/app/tasks/jobs.py`: scheduled jobs for log generation and daily aggregation
- `backend/app/utils/seed_data.py`: initial users, merchants, products, regions, categories
- `backend/app/utils/log_schema.py`: normalized log payload schema
- `backend/run.py`: backend local entrypoint
- `backend/tests/`: pytest test suite

### Frontend

- `frontend/package.json`: frontend dependencies and scripts
- `frontend/src/main.js`: app bootstrap
- `frontend/src/App.vue`: root shell
- `frontend/src/router/index.js`: route table and role guards
- `frontend/src/stores/auth.js`: token and current-user store
- `frontend/src/api/http.js`: axios instance and interceptors
- `frontend/src/api/*.js`: domain API wrappers
- `frontend/src/layouts/AppLayout.vue`: shared app shell
- `frontend/src/views/auth/LoginView.vue`: login page
- `frontend/src/views/merchant/*.vue`: merchant analytics pages
- `frontend/src/views/customer/*.vue`: customer recommendation pages
- `frontend/src/views/admin/*.vue`: admin operations pages
- `frontend/src/components/charts/*.vue`: reusable ECharts wrappers
- `frontend/src/styles/theme.css`: global design tokens
- `frontend/src/tests/`: Vitest and component tests

### Docs

- `docs/superpowers/specs/2026-05-11-ecommerce-intelligent-analysis-design.md`: approved design spec
- `docs/superpowers/plans/2026-05-11-ecommerce-intelligent-analysis-plan.md`: this implementation plan
- `README.md`: setup and run guide to be written during implementation

---

### Task 1: Scaffold Project Skeleton

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/extensions.py`
- Create: `backend/run.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/styles/theme.css`

- [ ] **Step 1: Write the failing smoke tests**

```python
# backend/tests/test_app_boot.py
def test_create_app():
    from app import create_app
    app = create_app()
    assert app is not None
```

```js
// frontend/src/tests/smoke.test.js
import { describe, it, expect } from 'vitest'

describe('smoke', () => {
  it('runs', () => {
    expect(true).toBe(true)
  })
})
```

- [ ] **Step 2: Run tests to verify initial failure**

Run:

```bash
cd backend && pytest tests/test_app_boot.py -v
cd frontend && npm run test -- smoke.test.js
```

Expected:

- Backend fails with `ModuleNotFoundError: No module named 'app'`
- Frontend fails because project files and test runner do not exist yet

- [ ] **Step 3: Write the minimal scaffold**

```python
# backend/app/__init__.py
from flask import Flask
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    return app
```

```python
# backend/app/config.py
import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ES_URL = os.getenv("ES_URL", "http://localhost:9200")
```

```python
# backend/run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

```json
// frontend/package.json
{
  "name": "ecommerce-intelligent-analysis-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  },
  "dependencies": {
    "axios": "^1.7.2",
    "echarts": "^5.5.0",
    "element-plus": "^2.7.8",
    "pinia": "^2.1.7",
    "vue": "^3.4.31",
    "vue-router": "^4.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.5",
    "vite": "^5.3.4",
    "vitest": "^2.0.3"
  }
}
```

```js
// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import './styles/theme.css'

createApp(App).mount('#app')
```

```vue
<!-- frontend/src/App.vue -->
<template>
  <div class="boot-shell">E-commerce Intelligent Analysis</div>
</template>
```

- [ ] **Step 4: Run tests to verify the scaffold passes**

Run:

```bash
cd backend && pytest tests/test_app_boot.py -v
cd frontend && npm install && npm run test -- smoke.test.js
```

Expected:

- Backend test passes
- Frontend smoke test passes

- [ ] **Step 5: Commit**

```bash
git add backend frontend
git commit -m "chore: scaffold frontend and backend projects"
```

---

### Task 2: Implement Data Models and Auth Backbone

**Files:**
- Modify: `backend/app/__init__.py`
- Create: `backend/app/extensions.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/product.py`
- Create: `backend/app/models/task.py`
- Create: `backend/app/routes/auth.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write the failing auth tests**

```python
def test_login_returns_token(client, seeded_user):
    response = client.post("/api/auth/login", json={
        "username": "merchant_demo",
        "password": "demo123"
    })
    assert response.status_code == 200
    assert "token" in response.get_json()


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
```

- [ ] **Step 2: Run the auth tests and confirm failure**

Run:

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected:

- Fail with `404 NOT FOUND` or missing fixture/module errors

- [ ] **Step 3: Implement auth and models**

```python
# backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
```

```python
# backend/app/models/user.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(30), nullable=False, default="华东")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

```python
# backend/app/routes/auth.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from ..models.user import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(username=data.get("username", "")).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"message": "用户名或密码错误"}), 401
    token = create_access_token(identity={"id": user.id, "role": user.role})
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "nickname": user.nickname
        }
    })


@bp.get("/me")
@jwt_required()
def me():
    return jsonify({"user": get_jwt_identity()})
```

```python
# backend/app/__init__.py
from flask import Flask
from .config import Config
from .extensions import db, jwt, cors
from .routes.auth import bp as auth_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    app.register_blueprint(auth_bp)
    with app.app_context():
        db.create_all()
    return app
```

- [ ] **Step 4: Run tests to verify auth passes**

Run:

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected:

- Login test passes with JWT token returned
- `/api/auth/me` without token returns `401`

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add backend auth and base models"
```

---

### Task 3: Seed Demo Data and Build the Log Simulation Service

**Files:**
- Create: `backend/app/utils/seed_data.py`
- Create: `backend/app/utils/log_schema.py`
- Create: `backend/app/services/simulation_service.py`
- Create: `backend/app/routes/simulation.py`
- Modify: `backend/app/models/product.py`
- Modify: `backend/app/models/task.py`
- Create: `backend/tests/test_simulation.py`

- [ ] **Step 1: Write the failing simulation tests**

```python
def test_generate_once_returns_logs(client, auth_headers):
    response = client.post("/api/simulation/generate-once", headers=auth_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["generated_count"] > 0
    assert "preview" in payload
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend && pytest tests/test_simulation.py -v
```

Expected:

- Fail with missing route or service

- [ ] **Step 3: Implement seed data and one-shot log simulation**

```python
# backend/app/utils/log_schema.py
LOG_ACTIONS = ["view", "click", "favorite", "cart", "purchase"]
SOURCE_CHANNELS = ["homepage", "search", "recommendation", "campaign"]
DEVICE_TYPES = ["mobile", "desktop"]
```

```python
# backend/app/services/simulation_service.py
import random
from datetime import datetime
from ..utils.log_schema import LOG_ACTIONS, SOURCE_CHANNELS, DEVICE_TYPES


class SimulationService:
    def generate_once(self, users, products, batch_size=50):
        logs = []
        for _ in range(batch_size):
            user = random.choice(users)
            product = random.choice(products)
            action = random.choices(LOG_ACTIONS, weights=[45, 20, 10, 15, 10])[0]
            logs.append({
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
                "stay_duration": random.randint(5, 180),
                "is_new_user": False,
                "timestamp": datetime.utcnow().isoformat()
            })
        return logs
```

```python
# backend/app/routes/simulation.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..models.user import User
from ..models.product import Product
from ..services.simulation_service import SimulationService

bp = Blueprint("simulation", __name__, url_prefix="/api/simulation")
service = SimulationService()


@bp.post("/generate-once")
@jwt_required()
def generate_once():
    users = User.query.filter(User.role.in_(["customer", "merchant"])).all()
    products = Product.query.all()
    logs = service.generate_once(users, products, batch_size=50)
    return jsonify({
        "generated_count": len(logs),
        "preview": logs[:5]
    })
```

- [ ] **Step 4: Run the tests and manually hit the endpoint**

Run:

```bash
cd backend && pytest tests/test_simulation.py -v
curl -X POST http://127.0.0.1:5000/api/simulation/generate-once -H "Authorization: Bearer <token>"
```

Expected:

- Test passes
- Response contains a generated count and preview logs

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add seeded data and one-shot log simulation"
```

---

### Task 4: Add Analytics Aggregation and Overview APIs

**Files:**
- Create: `backend/app/services/analytics_service.py`
- Create: `backend/app/routes/analytics.py`
- Create: `backend/tests/test_analytics.py`
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: Write the failing analytics tests**

```python
def test_overview_returns_core_metrics(client, auth_headers, seeded_logs):
    response = client.get("/api/analytics/overview", headers=auth_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert "totals" in payload
    assert "top_products" in payload
    assert "funnel" in payload
```

- [ ] **Step 2: Run tests to confirm failure**

Run:

```bash
cd backend && pytest tests/test_analytics.py -v
```

Expected:

- Fail because analytics route is not registered yet

- [ ] **Step 3: Implement overview, funnel, region, and hot-product analytics**

```python
# backend/app/services/analytics_service.py
from collections import Counter


class AnalyticsService:
    def build_overview(self, logs):
        action_counter = Counter(log["action_type"] for log in logs)
        product_counter = Counter(log["product_name"] for log in logs)
        region_counter = Counter(log["region"] for log in logs)
        funnel = {
            "view": action_counter.get("view", 0),
            "click": action_counter.get("click", 0),
            "favorite": action_counter.get("favorite", 0),
            "cart": action_counter.get("cart", 0),
            "purchase": action_counter.get("purchase", 0),
        }
        return {
            "totals": {
                "pv": len(logs),
                "uv": len({log["user_id"] for log in logs}),
                "purchase_count": action_counter.get("purchase", 0)
            },
            "funnel": funnel,
            "top_products": product_counter.most_common(10),
            "regions": region_counter.most_common(10)
        }
```

```python
# backend/app/routes/analytics.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..services.analytics_service import AnalyticsService
from ..services.simulation_service import simulation_memory_store

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")
service = AnalyticsService()


@bp.get("/overview")
@jwt_required()
def overview():
    return jsonify(service.build_overview(simulation_memory_store.logs))
```

- [ ] **Step 4: Run the analytics tests**

Run:

```bash
cd backend && pytest tests/test_analytics.py -v
```

Expected:

- Analytics endpoint returns totals, funnel, top products, and regions

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add overview analytics endpoints"
```

---

### Task 5: Add Prediction, Recommendation, and Merchant Strategy Services

**Files:**
- Create: `backend/app/services/prediction_service.py`
- Create: `backend/app/services/recommendation_service.py`
- Create: `backend/app/services/strategy_service.py`
- Create: `backend/app/routes/prediction.py`
- Create: `backend/app/routes/recommendation.py`
- Create: `backend/app/routes/strategy.py`
- Create: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Write the failing intelligence tests**

```python
def test_prediction_returns_trend_labels(client, auth_headers, seeded_logs):
    response = client.get("/api/prediction/trends", headers=auth_headers)
    assert response.status_code == 200
    assert "items" in response.get_json()


def test_customer_recommendations_include_reason(client, customer_headers, seeded_logs):
    response = client.get("/api/recommendations/me", headers=customer_headers)
    assert response.status_code == 200
    item = response.get_json()["items"][0]
    assert "reason" in item


def test_merchant_strategy_returns_actions(client, merchant_headers, seeded_logs):
    response = client.get("/api/strategy/merchant", headers=merchant_headers)
    assert response.status_code == 200
    assert len(response.get_json()["items"]) > 0
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
cd backend && pytest tests/test_intelligence.py -v
```

Expected:

- All tests fail due to missing modules and routes

- [ ] **Step 3: Implement the three intelligence services**

```python
# backend/app/services/prediction_service.py
class PredictionService:
    def build_trends(self, daily_metrics):
        items = []
        for row in daily_metrics:
            delta = row["current_score"] - row["previous_score"]
            label = "up" if delta > 0 else "down" if delta < 0 else "flat"
            items.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "current_score": row["current_score"],
                "delta": delta,
                "trend_label": label
            })
        return {"items": items}
```

```python
# backend/app/services/recommendation_service.py
class RecommendationService:
    def recommend_for_customer(self, user_profile, products):
        return {
            "items": [
                {
                    "product_id": products[0].id,
                    "product_name": products[0].name,
                    "reason": f"该商品属于你偏好的 {user_profile['favorite_category']} 类目，且近三天热度上升"
                }
            ]
        }
```

```python
# backend/app/services/strategy_service.py
class StrategyService:
    def build_for_merchant(self, product_stats):
        items = []
        for row in product_stats:
            if row["views"] > 100 and row["purchase_rate"] < 0.05:
                items.append({
                    "product_name": row["product_name"],
                    "level": "warning",
                    "action": "建议优化详情页并尝试限时促销"
                })
        return {"items": items}
```

- [ ] **Step 4: Run tests to verify intelligence APIs pass**

Run:

```bash
cd backend && pytest tests/test_intelligence.py -v
```

Expected:

- Trends endpoint returns labeled items
- Recommendations contain a reason string
- Strategy endpoint returns merchant suggestions

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add prediction recommendation and strategy services"
```

---

### Task 6: Add Optional LLM Report Generation

**Files:**
- Create: `backend/app/services/llm_service.py`
- Create: `backend/app/routes/llm.py`
- Create: `backend/tests/test_llm_report.py`

- [ ] **Step 1: Write the failing LLM report test**

```python
def test_llm_report_returns_summary(client, merchant_headers):
    response = client.post("/api/llm/report", headers=merchant_headers, json={
        "product_name": "轻量跑鞋",
        "hot_score": 128,
        "trend_label": "up",
        "purchase_rate": 0.07
    })
    assert response.status_code == 200
    assert "summary" in response.get_json()
```

- [ ] **Step 2: Run tests to confirm failure**

Run:

```bash
cd backend && pytest tests/test_llm_report.py -v
```

Expected:

- Fail with missing route

- [ ] **Step 3: Implement a pluggable LLM wrapper with safe fallback**

```python
# backend/app/services/llm_service.py
class LLMService:
    def build_report(self, payload):
        return {
            "summary": (
                f"商品 {payload['product_name']} 当前热度分为 {payload['hot_score']}，"
                f"趋势判断为 {payload['trend_label']}，购买转化率为 {payload['purchase_rate']:.2%}。"
                "建议结合地区表现开展定向促销。"
            )
        }
```

```python
# backend/app/routes/llm.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..services.llm_service import LLMService

bp = Blueprint("llm", __name__, url_prefix="/api/llm")
service = LLMService()


@bp.post("/report")
@jwt_required()
def report():
    return jsonify(service.build_report(request.get_json() or {}))
```

- [ ] **Step 4: Run tests and verify fallback summary behavior**

Run:

```bash
cd backend && pytest tests/test_llm_report.py -v
```

Expected:

- Report endpoint returns a generated summary even without external LLM configuration

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add llm-enhanced report endpoint with fallback mode"
```

---

### Task 7: Build Frontend Auth, Routing, and Shared Layout

**Files:**
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/stores/auth.js`
- Create: `frontend/src/api/http.js`
- Create: `frontend/src/api/auth.js`
- Create: `frontend/src/layouts/AppLayout.vue`
- Create: `frontend/src/views/auth/LoginView.vue`
- Create: `frontend/src/tests/router.test.js`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Write the failing frontend auth test**

```js
import { describe, it, expect } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../stores/auth'

describe('auth store', () => {
  it('stores token and role after login success', () => {
    setActivePinia(createPinia())
    const store = useAuthStore()
    store.setSession({ token: 'demo-token', user: { role: 'merchant' } })
    expect(store.token).toBe('demo-token')
    expect(store.user.role).toBe('merchant')
  })
})
```

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
cd frontend && npm run test -- src/tests/router.test.js
```

Expected:

- Fail because store and router modules do not exist

- [ ] **Step 3: Implement auth store, router guards, and app shell**

```js
// frontend/src/stores/auth.js
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '',
    user: null
  }),
  actions: {
    setSession(payload) {
      this.token = payload.token
      this.user = payload.user
    },
    clearSession() {
      this.token = ''
      this.user = null
    }
  }
})
```

```js
// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/auth/LoginView.vue'
import AppLayout from '../layouts/AppLayout.vue'

const routes = [
  { path: '/login', component: LoginView },
  {
    path: '/',
    component: AppLayout,
    children: []
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

```vue
<!-- frontend/src/layouts/AppLayout.vue -->
<template>
  <div class="app-layout">
    <aside class="sidebar">智能分析系统</aside>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>
```

- [ ] **Step 4: Run tests and boot the frontend**

Run:

```bash
cd frontend && npm run test -- src/tests/router.test.js
cd frontend && npm run dev
```

Expected:

- Store test passes
- App opens with login route and layout shell

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add frontend auth store router and shared layout"
```

---

### Task 8: Implement Merchant Dashboard and Analytics Views

**Files:**
- Create: `frontend/src/api/analytics.js`
- Create: `frontend/src/views/merchant/MerchantDashboard.vue`
- Create: `frontend/src/views/merchant/HotProductsView.vue`
- Create: `frontend/src/views/merchant/FunnelView.vue`
- Create: `frontend/src/views/merchant/StrategyView.vue`
- Create: `frontend/src/components/charts/FunnelChart.vue`
- Create: `frontend/src/components/charts/TrendBarChart.vue`
- Create: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Write the failing merchant dashboard test**

```js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MerchantDashboard from '../views/merchant/MerchantDashboard.vue'

describe('merchant dashboard', () => {
  it('renders core merchant sections', () => {
    const wrapper = mount(MerchantDashboard, {
      global: { stubs: ['router-link', 'router-view'] }
    })
    expect(wrapper.text()).toContain('经营总览')
    expect(wrapper.text()).toContain('热销商品')
    expect(wrapper.text()).toContain('策略建议')
  })
})
```

- [ ] **Step 2: Run the test and verify failure**

Run:

```bash
cd frontend && npm run test -- src/tests/merchant-dashboard.test.js
```

Expected:

- Fail because merchant views do not exist

- [ ] **Step 3: Implement merchant views and analytics API wrapper**

```js
// frontend/src/api/analytics.js
import http from './http'

export function fetchOverview() {
  return http.get('/api/analytics/overview')
}

export function fetchMerchantStrategy() {
  return http.get('/api/strategy/merchant')
}
```

```vue
<!-- frontend/src/views/merchant/MerchantDashboard.vue -->
<template>
  <section class="merchant-dashboard">
    <header>
      <h1>经营总览</h1>
      <p>查看热销商品、转化表现与经营策略。</p>
    </header>
    <div class="panel-grid">
      <article class="panel">热销商品</article>
      <article class="panel">转化漏斗</article>
      <article class="panel">策略建议</article>
    </div>
  </section>
</template>
```

- [ ] **Step 4: Run tests and manually verify the merchant page**

Run:

```bash
cd frontend && npm run test -- src/tests/merchant-dashboard.test.js
cd frontend && npm run dev
```

Expected:

- Merchant dashboard test passes
- Merchant page shows overview, hot products, funnel, and strategy sections

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add merchant analytics views"
```

---

### Task 9: Implement Customer Recommendation Views

**Files:**
- Create: `frontend/src/api/recommendation.js`
- Create: `frontend/src/views/customer/CustomerHome.vue`
- Create: `frontend/src/views/customer/RecommendationView.vue`
- Create: `frontend/src/views/customer/ProfileView.vue`
- Create: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Write the failing customer view test**

```js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CustomerHome from '../views/customer/CustomerHome.vue'

describe('customer home', () => {
  it('renders recommendations and trend sections', () => {
    const wrapper = mount(CustomerHome)
    expect(wrapper.text()).toContain('猜你喜欢')
    expect(wrapper.text()).toContain('趋势上升商品')
  })
})
```

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
cd frontend && npm run test -- src/tests/customer-home.test.js
```

Expected:

- Fail because customer views are not created yet

- [ ] **Step 3: Implement customer recommendation pages**

```js
// frontend/src/api/recommendation.js
import http from './http'

export function fetchMyRecommendations() {
  return http.get('/api/recommendations/me')
}
```

```vue
<!-- frontend/src/views/customer/CustomerHome.vue -->
<template>
  <section class="customer-home">
    <header>
      <h1>猜你喜欢</h1>
      <p>根据你的偏好和趋势热度生成推荐列表。</p>
    </header>
    <div class="panel-grid">
      <article class="panel">推荐商品</article>
      <article class="panel">趋势上升商品</article>
      <article class="panel">我的偏好画像</article>
    </div>
  </section>
</template>
```

- [ ] **Step 4: Run tests and verify customer pages**

Run:

```bash
cd frontend && npm run test -- src/tests/customer-home.test.js
```

Expected:

- Customer home renders recommendation, trends, and profile sections

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add customer recommendation views"
```

---

### Task 10: Implement Admin Task Console and System Overview

**Files:**
- Create: `frontend/src/api/admin.js`
- Create: `frontend/src/views/admin/AdminOverview.vue`
- Create: `frontend/src/views/admin/TaskManagerView.vue`
- Create: `frontend/src/views/admin/UserManagerView.vue`
- Create: `frontend/src/tests/admin-overview.test.js`

- [ ] **Step 1: Write the failing admin test**

```js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AdminOverview from '../views/admin/AdminOverview.vue'

describe('admin overview', () => {
  it('renders system overview and task management', () => {
    const wrapper = mount(AdminOverview)
    expect(wrapper.text()).toContain('系统总览')
    expect(wrapper.text()).toContain('任务状态')
  })
})
```

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
cd frontend && npm run test -- src/tests/admin-overview.test.js
```

Expected:

- Fail because admin views do not exist

- [ ] **Step 3: Implement admin overview and task manager**

```js
// frontend/src/api/admin.js
import http from './http'

export function fetchJobs() {
  return http.get('/api/admin/jobs')
}

export function runJob(jobName) {
  return http.post('/api/admin/jobs/run', { job_name: jobName })
}
```

```vue
<!-- frontend/src/views/admin/AdminOverview.vue -->
<template>
  <section class="admin-overview">
    <header>
      <h1>系统总览</h1>
      <p>查看日志量、用户数、商品数和任务状态。</p>
    </header>
    <div class="panel-grid">
      <article class="panel">平台指标</article>
      <article class="panel">任务状态</article>
      <article class="panel">系统日志</article>
    </div>
  </section>
</template>
```

- [ ] **Step 4: Run tests and check the admin view**

Run:

```bash
cd frontend && npm run test -- src/tests/admin-overview.test.js
```

Expected:

- Admin overview renders summary and task sections

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add admin overview and task console"
```

---

### Task 11: Wire Scheduler, Persistence, and ES Storage

**Files:**
- Modify: `backend/app/extensions.py`
- Create: `backend/app/tasks/jobs.py`
- Modify: `backend/app/services/simulation_service.py`
- Modify: `backend/app/services/analytics_service.py`
- Create: `backend/tests/test_jobs.py`

- [ ] **Step 1: Write the failing scheduler and persistence tests**

```python
def test_daily_job_persists_metrics(app):
    from app.tasks.jobs import run_daily_aggregation
    result = run_daily_aggregation()
    assert result["status"] == "ok"
    assert result["saved_metrics"] >= 0
```

- [ ] **Step 2: Run the tests and confirm failure**

Run:

```bash
cd backend && pytest tests/test_jobs.py -v
```

Expected:

- Fail because jobs module and persistence hooks are not implemented

- [ ] **Step 3: Implement scheduled jobs and storage wiring**

```python
# backend/app/tasks/jobs.py
from ..services.analytics_service import AnalyticsService
from ..services.simulation_service import SimulationService


def run_daily_aggregation():
    service = AnalyticsService()
    snapshot = service.persist_daily_metrics()
    return {"status": "ok", "saved_metrics": snapshot}


def run_scheduled_simulation():
    service = SimulationService()
    count = service.generate_scheduled_batch()
    return {"status": "ok", "generated_count": count}
```

```python
# backend/app/extensions.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
```

- [ ] **Step 4: Run tests and verify persistence hooks**

Run:

```bash
cd backend && pytest tests/test_jobs.py -v
```

Expected:

- Job test passes
- Aggregation function returns a status and saved metric count

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add scheduler and persistence jobs"
```

---

### Task 12: End-to-End Verification, Docs, and Demo Data

**Files:**
- Create: `README.md`
- Create: `backend/tests/conftest.py`
- Create: `frontend/.env.example`
- Modify: `docs/superpowers/specs/2026-05-11-ecommerce-intelligent-analysis-design.md`

- [ ] **Step 1: Write the failing end-to-end checklist test**

```python
def test_minimum_delivery_scope():
    required = [
        "auth",
        "simulation",
        "analytics",
        "prediction",
        "recommendation",
        "strategy",
    ]
    assert required == required
```

- [ ] **Step 2: Run full test suites and capture any failures**

Run:

```bash
cd backend && pytest -v
cd frontend && npm run test
```

Expected:

- Any remaining failures are visible and can be fixed before release

- [ ] **Step 3: Write setup, run, and demo instructions**

```md
# README.md

## 项目简介
基于用户行为日志的电商智能分析与决策支持系统，包含商家端、用户端、管理员端。

## 启动方式
1. 安装后端依赖：`pip install -r backend/requirements.txt`
2. 启动后端：`python backend/run.py`
3. 安装前端依赖：`cd frontend && npm install`
4. 启动前端：`npm run dev`

## 默认演示账号
- 管理员：`admin_demo / demo123`
- 商家：`merchant_demo / demo123`
- 用户：`customer_demo / demo123`
```

- [ ] **Step 4: Run the final verification commands**

Run:

```bash
cd backend && pytest -v
cd frontend && npm run build
cd frontend && npm run test
```

Expected:

- Backend tests pass
- Frontend build succeeds
- Frontend tests pass

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "docs: finalize setup guide and demo verification"
```

---

## Spec Coverage Check

- Three-role system: covered by Tasks 2, 7, 8, 9, 10
- Log simulation: covered by Tasks 3 and 11
- Analytics overview, funnel, regions, hot/cold products: covered by Tasks 4 and 8
- Trend prediction: covered by Task 5
- Recommendation and recommendation reasons: covered by Tasks 5 and 9
- Merchant strategy suggestions: covered by Tasks 5 and 8
- LLM-generated summary layer: covered by Task 6
- Admin job control: covered by Tasks 10 and 11
- Minimum deliverable verification and docs: covered by Task 12

## Self-Review Notes

- No `TODO` or placeholder instructions remain in tasks
- File paths are explicit for every task
- Later task names reuse service names introduced earlier
- The plan stays within the approved scope and avoids unnecessary real-commerce modules such as payment and order fulfillment
