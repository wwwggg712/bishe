# 基于用户行为日志的电商智能分析与决策支持系统

## 项目简介

本项目是一个面向毕业设计答辩场景的前后端分离演示系统，围绕电商用户行为日志完成以下最小闭环：

- 三角色登录与权限隔离：管理员、商家、普通用户
- 演示数据初始化：默认账号、商品、任务自动写入本地数据库
- 行为日志模拟：支持一次性生成日志、模拟任务启动/停止与任务状态查看
- 智能分析能力：总览指标、漏斗、地区/类目热点、热销/冷门商品、RFM 用户分层、趋势预测、推荐与商家策略建议
- 管理端控制台：查看系统概览、任务状态、模拟任务控制与用户列表

当前仓库的最小可运行实现以本地 SQLite 为主，适合课程设计、毕设展示和功能验收。

## 目录结构

```text
bishe-finnal/
|- backend/   Flask API、数据模型、任务与 pytest
|- frontend/  Vue 3 + Vite 页面、Pinia、Vitest
`- docs/      设计文档与实施计划
```

## 运行环境

- Python：建议 `3.9+`
- Node.js：建议 `18+`
- npm：建议 `9+`
- 操作系统：已在 Windows 环境完成验证

## 后端环境说明

后端支持读取 `backend/.env` 文件并注入环境变量；如果未提供，则读取系统环境变量；两者都未设置时使用内置默认值。

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `SECRET_KEY` | `dev-secret-key-change-me-1234567890` | Flask 基础密钥 |
| `JWT_SECRET_KEY` | 同 `SECRET_KEY` | JWT 签名密钥 |
| `DATABASE_URL` | `sqlite:///local.db` | 数据库连接；默认在 `backend/instance/local.db` 生成本地库 |
| `CORS_ORIGINS` | `*` | 允许访问 API 的前端来源 |
| `ES_URL` | `http://localhost:9200` | 预留的 Elasticsearch 地址 |
| `AUTO_SEED_DEMO_DATA` | `true` | 首次启动时是否自动写入演示账号、商品和任务 |

如使用 MySQL，本仓库已提供样例文件：

```bash
cd backend
copy .env.example .env
```

说明：

- 当前最小演示流程不要求必须安装 MySQL 或 Elasticsearch。
- 如只做本地答辩演示，直接使用默认配置即可。

## 前端环境说明

前端使用 Vite 环境变量，已提供样例文件 `frontend/.env.example`。

推荐在 `frontend/` 下复制一份：

```bash
copy .env.example .env
```

或手动创建 `.env`：

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
```

当前前端会把所有接口请求发送到 `VITE_API_BASE_URL`，未配置时默认仍回退到 `http://127.0.0.1:5000`。

## 安装与启动

### 1. 启动后端

```bash
cd backend
python -m pip install -r requirements.txt
python run.py
```

默认启动地址：

- API 根地址：`http://127.0.0.1:5000`

首次启动会自动：

- 创建本地 SQLite 数据库
- 初始化 3 个默认演示账号
- 初始化商品与任务数据

### 2. 启动前端

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

默认启动后，在浏览器访问终端输出的本地地址，一般为：

- 前端地址：`http://127.0.0.1:5173`

## 默认演示账号

- 管理员：`admin_demo / demo123`
- 商家：`merchant_demo / demo123`
- 用户：`customer_demo / demo123`

## 最小演示说明

### 演示目标

在最短时间内完成“登录 -> 进入对应角色页面 -> 查看分析结果/推荐结果 -> 触发后台任务”的闭环演示。

### 推荐演示顺序

1. 启动后端与前端。
2. 打开登录页，先使用 `merchant_demo / demo123` 登录。
3. 进入系统后，在左侧导航点击“商家看板”。
4. 查看商家端的经营总览、热销商品、冷门商品、类目热点、用户价值分层、转化漏斗和策略建议。
5. 退出后使用 `customer_demo / demo123` 登录。
6. 查看“推荐首页”“推荐中心”“个人画像”，验证推荐理由和趋势商品。
7. 退出后使用 `admin_demo / demo123` 登录。
8. 进入“系统总览”与“任务管理”，启动或停止模拟任务，手动触发后台任务，查看系统日志与用户列表。

### 最小演示检查点

- 登录成功后可根据角色显示不同导航菜单
- 商家端可加载总览、冷热门商品、类目热点、用户价值分层与策略数据
- 用户端可看到推荐商品、趋势上升商品和偏好画像
- 管理员端可查看任务、模拟任务状态并触发任务执行
- 后端接口在本地可正常响应，前端页面可正常渲染

## 常用验证命令

### 后端测试

```bash
cd backend
python -m pytest -v
```

### 前端测试

```bash
cd frontend
npm run test
```

### 前端构建

```bash
cd frontend
npm run build
```

## 本次验证结果

以下命令已在当前仓库实际执行通过：

```bash
cd backend && python -m pytest -v
cd frontend && npm run test
cd frontend && npm run build
```

结果摘要：

- 后端：`23 passed`
- 前端测试：`6` 个测试文件、`14 passed`
- 前端构建：成功产出 `frontend/dist/`

构建过程存在两类非阻塞告警：

- `@vueuse/core` 的 `/* #__PURE__ */` 注释被 Rollup 移除
- 打包后存在超过 `500 kB` 的 chunk 体积提示

这两项均未导致构建失败，不影响当前最小演示与验收。
