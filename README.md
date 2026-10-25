# 数据信息门户 — Web 原型

海洋环境数据的 ERDDAP 式网页原型（五页应用：首页 / 数据库 / 数据上传 / 数据下载 / 成果展示）。
纯 UI/逻辑原型：与项目 `src/` 完全解耦，地图与数据均用文字占位符展示。

## 环境要求

- Python 3.9+（推荐 3.11）
- 依赖仅两个：`fastapi`、`uvicorn`

## 安装与运行

```bash
# 1. 新建虚拟环境（可选，推荐）
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务（两种方式任选其一）
#    方式 A：进入本目录运行
python -m uvicorn app:app --host 0.0.0.0 --port 8000

#    方式 B：在本目录的上级目录运行（把 webapp 当作包导入）
python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

浏览器打开 http://127.0.0.1:8000 即可。

## 目录结构

```
webapp/
  __init__.py
  app.py              # FastAPI 应用 + 全部 mock 数据（MOCK_DATASETS/CATALOGS/ACHIEVEMENTS）
  requirements.txt
  README.md
  static/
    home.html         # 封面
    database.html     # 数据库综合展示
    upload.html       # 数据上传
    download.html     # 数据下载（参数设置 + 预览）
    achievements.html # 成果展示
    style.css
    app.js
```

## 说明

- 所有数据接口均为 mock 端点（`/api/datasets`、`/api/dataset/{id}`、`/api/catalogs`、`/api/achievements`、`/api/templates/{kind}`），数据硬编码在 `app.py` 内，不读外部文件。
- 后续接入真实管线：把 `app.py` 里的 mock 端点替换为调用 `src.core` 的真实实现即可，页面结构无需改动。
