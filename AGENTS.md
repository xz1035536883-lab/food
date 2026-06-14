# AGENTS.md — Food Calorie Recognition Mini-Program

## Project Overview

WeChat mini-program for photo-based food calorie recognition + weight loss planning.

| Layer | Tech |
|-------|------|
| Frontend | WeChat Mini-Program (native WXML/WXSS/JS) |
| Backend | Python FastAPI + SQLAlchemy + SQLite |
| AI | Baidu AI dish recognition (`v2/dish`) |
| Auth | JWT (manual login, no auto-login) |

## Project Structure

```
food/
├── backend/                  # Python FastAPI
│   ├── app/
│   │   ├── main.py           # Entry + startup (DB init, migration, seeding)
│   │   ├── config.py         # Settings (env vars)
│   │   ├── database.py       # SQLAlchemy engine
│   │   ├── models/           # user.py, food.py, diet_record.py
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── routers/          # auth.py, food.py, diet_record.py
│   │   ├── services/         # auth_service.py, recognition_service.py, plan_service.py
│   │   └── utils/            # response.py (success/fail helpers)
│   ├── data/seed_foods.py    # ~200 preset food items
│   └── .env                  # Credentials (ignored by git)
├── miniapp/                  # WeChat Mini-Program
│   ├── app.js                # Global state + login()
│   ├── app.json/wxss         # Config + global styles
│   ├── utils/
│   │   ├── api.js            # HTTP wrapper (no auto-login on 401)
│   │   └── util.js           # Date, formatting helpers
│   └── pages/
│       ├── index/            # Photo taking / image selection
│       ├── result/           # Recognition results + save
│       ├── record/           # Diet records list + daily summary
│       └── profile/          # User info, body data, weight loss plan
└── AGENTS.md                 # This file
```

## Key Architecture Decisions

### Login Flow (Manual, not Auto)

- `app.js` **does NOT** auto-login in `onLaunch()` — only restores cached token/user from storage
- Login happens only when user clicks "授权登录" on the **profile page**
- `app.login()` returns a Promise, with cached promise pattern (10s TTL) to prevent duplicate calls
- On 401 from any API, `api.js` rejects with "请先登录" — does NOT auto-trigger login

### No API Calls Without Login

Every page that calls authenticated APIs MUST guard with `app.isLoggedIn()`:

```javascript
// ✅ Correct — login guard in load function
async loadData() {
    if (!app.isLoggedIn()) return;
    // ... API calls
}

// ✅ Correct — login guard before action
async recognizeFood(filePath) {
    if (!app.isLoggedIn()) {
        wx.showToast({ title: '请先去「我的」授权登录', icon: 'none' });
        return;
    }
    // ... API call
}
```

### Data Flow

```
Login:  用户点"授权登录" → app.login() → wx.login → POST /api/auth/login → JWT token + userInfo
Show:   onShow → syncUserInfo() → read from app.globalData / storage → setData
Save:   setData locally → api.updateProfile() → store response in globalData + storage
```

`syncUserInfo()` is SYNCHRONOUS — reads from cache only, no network calls.

### Baidu AI Dish Recognition

- Token: OAuth2 `client_credentials` grant, cached 30 days
- API: `POST aip.baidubce.com/rest/2.0/image-classify/v2/dish`
- Rate limiter: enforces 1.5s between calls (free tier QPS=1)
- Returns: `name`, `calorie` (per 100g), `probability`, `has_calorie`
- Local DB matching supplements protein/fat/carbs/fiber

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/auth/login | No | Exchange wx.login code for JWT |
| GET | /api/auth/profile | Yes | Get user profile |
| POST | /api/auth/profile | Yes | Update profile |
| GET | /api/auth/plan | Yes | Generate weight loss plan |
| POST | /api/food/recognize | Yes | Upload image → food recognition |
| GET | /api/food/search?keyword= | Yes | Search foods |
| GET | /api/record?record_date=&meal_type= | Yes | Get diet records |
| POST | /api/record | Yes | Add diet record |
| DELETE | /api/record/{id} | Yes | Delete record |
| GET | /api/record/summary?record_date= | Yes | Daily calorie summary |

## Running Locally

```bash
# Backend
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
# Open miniapp/ in WeChat DevTools
# Settings → uncheck "validate domain" for local dev
```

## Configuration (.env)

Required env vars in `backend/.env`:
- `BAIDU_API_KEY` / `BAIDU_SECRET_KEY` — Baidu AI credentials
- `WECHAT_APP_ID` / `WECHAT_APP_SECRET` — WeChat mini-program
- `JWT_SECRET` — JWT signing key

## Rules

- Never auto-login — login is user-initiated from profile page only
- Never call an authenticated API without `app.isLoggedIn()` guard
- `syncUserInfo()` is sync-only, no network
- `api.js` 401 → reject, don't re-login
- All API errors show user-facing toast (`.catch(() => {})` only for non-critical slider changes)
