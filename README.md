# 食物热量识别小程序

AI 拍照识别食物，自动计算热量和营养成分，搭配减重计划功能。

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Python FastAPI + SQLite + SQLAlchemy |
| 前端 | 微信小程序 |
| AI | 百度 AI 菜品识别 API |
| 部署 | Docker + Nginx + Let's Encrypt |

## 项目结构

```
food/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 入口，数据库初始化
│   │   ├── config.py        # 配置
│   │   ├── database.py      # SQLAlchemy 引擎
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic 请求/响应
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务逻辑
│   │   └── utils/           # 工具
│   ├── data/seed_foods.py   # 预置食物数据（~200种）
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── miniapp/                 # 微信小程序
│   ├── app.js               # 全局状态 + 登录
│   ├── pages/               # 页面
│   │   ├── index/           # 拍照/选图
│   │   ├── result/          # 识别结果
│   │   ├── record/          # 饮食记录
│   │   ├── plan/            # 减重计划
│   │   └── profile/         # 个人中心
│   └── utils/               # 工具函数
└── deploy/                  # 部署
    ├── nginx.conf           # Nginx + SSL 配置模板
    └── deploy.sh            # 自动部署脚本
```

## 本地开发

### 后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 WECHAT_APP_ID、WECHAT_APP_SECRET 等

# 启动
uvicorn app.main:app --reload --port 8000
```

API 文档: http://localhost:8000/docs

### 小程序

1. 下载 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 导入项目，选择 `miniapp/` 目录
3. 开发阶段勾选"不校验合法域名"

## Docker 部署

```bash
cd backend

# 创建 .env 文件（生产环境配置）
# WECHAT_APP_ID=xxx
# WECHAT_APP_SECRET=xxx
# ...

# 构建并启动
docker compose up -d --build

# 查看状态
docker compose ps
docker compose logs -f
```

## 部署到服务器

见 `deploy/` 目录下的 `deploy.sh` 和 `nginx.conf`。

部署要求：
- 微信小程序要求 HTTPS + 域名
- 阿里云海外服务器（泰国节点）免 ICP 备案

```bash
# 一键部署
./deploy/deploy.sh <服务器IP>
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 微信登录 |
| POST | `/api/food/recognize` | 上传图片识别食物 |
| GET  | `/api/food/search` | 搜索食物 |
| GET  | `/api/food/list` | 食物列表 |
| GET  | `/api/diet-record/daily` | 当日饮食记录 |
| POST | `/api/diet-record/add` | 添加饮食记录 |
| POST | `/api/weight-record/add` | 添加体重记录 |
| GET  | `/api/weight-record/list` | 体重记录列表 |
| GET  | `/api/health` | 健康检查 |
