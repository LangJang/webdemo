"""
FastAPI web prototype for the Data Information Portal.

Multi-page UI (home / database / upload / chart), academic-minimal style,
Chinese-primary with English terms.  Self-contained: no ``src`` imports;
data and charts are mock JSON + text placeholders.

Wire real data later by replacing the mock endpoints with calls to
``src.core.*`` — the route/page structure is already in place.
"""
# python -m uvicorn app:app --host 0.0.0.0 --port 8000

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Data Information Portal — Web Demo", version="0.2.0")

# ---------------------------------------------------------------------------
# Mock registry — mirrors the shape of the real ``config.yaml`` entries.
# ---------------------------------------------------------------------------

# Canonical variable → (display label, units).  A tiny hardcoded mirror of
# ``src.core.canonical.CANONICAL_VARIABLES`` (kept here to stay decoupled).
CANONICAL_VARS: dict[str, tuple[str, str]] = {
    "temperature":      ("Potential Temperature", "°C"),
    "salinity":         ("Salinity", "PSU"),
    "u_current":        ("Eastward Current", "m s⁻¹"),
    "v_current":        ("Northward Current", "m s⁻¹"),
    "w_velocity":       ("Vertical Velocity", "m s⁻¹"),
    "chlorophyll":      ("Chlorophyll-a", "mg m⁻³"),
    "dissolved_oxygen": ("Dissolved Oxygen", "mmol m⁻³"),
    "nitrate":          ("Nitrate", "mmol m⁻³"),
    "phosphate":        ("Phosphate", "mmol m⁻³"),
    "silicate":         ("Dissolved Silicate", "mmol m⁻³"),
    "ph":               ("pH", ""),
}

MOCK_DATASETS: list[dict] = [
    {
        "id": "scsio-std",
        "name": "SCSIO 标准化（0–400 m, 0.05°）",
        "source": "SCSIO-Standard",
        "keywords": ["temperature", "salinity", "current", "velocity", "scsio", "standardized"],
        "variables": ["temperature", "salinity", "u_current", "v_current", "w_velocity"],
        "resolution": {"default": 0.05, "available": [0.05, 0.1, 0.25]},
        "spatial": {"lon": {"min": 90.12, "max": 133.78}, "lat": {"min": 0.80, "max": 30.38}},
        "temporal": {"start": "2023-01-01", "end": "2023-01-31", "frequency": "daily"},
        "vertical": {"type": "depth", "layers": 14, "range": [0, 400]},
    },
    {
        "id": "cmems-do-chl",
        "name": "CMEMS 标准化 — 溶解氧 & 叶绿素（0–400 m, 0.05°）",
        "source": "CMEMS",
        "keywords": ["chlorophyll", "oxygen", "dissolved oxygen", "cmems", "standardized"],
        "variables": ["chlorophyll", "dissolved_oxygen"],
        "resolution": {"default": 0.05, "available": [0.05, 0.1, 0.25]},
        "spatial": {"lon": {"min": 90.0, "max": 134.5}, "lat": {"min": -0.5, "max": 30.0}},
        "temporal": {"start": "2023-01-01", "end": "2023-12-31", "frequency": "daily"},
        "vertical": {"type": "depth", "layers": 14, "range": [0, 400]},
    },
    {
        "id": "cmems-nutrients",
        "name": "CMEMS 标准化 — 营养盐（0–400 m, 0.05°）",
        "source": "CMEMS",
        "keywords": ["nitrate", "phosphate", "silicate", "nutrient", "cmems", "standardized"],
        "variables": ["nitrate", "phosphate", "silicate"],
        "resolution": {"default": 0.05, "available": [0.05, 0.1, 0.25]},
        "spatial": {"lon": {"min": 90.0, "max": 134.5}, "lat": {"min": -0.5, "max": 30.0}},
        "temporal": {"start": "2023-01-01", "end": "2023-12-31", "frequency": "daily"},
        "vertical": {"type": "depth", "layers": 14, "range": [0, 400]},
    },
    {
        "id": "cmems-ph",
        "name": "CMEMS 标准化 — pH（0–400 m, 0.05°）",
        "source": "CMEMS",
        "keywords": ["ph", "acidity", "cmems", "standardized"],
        "variables": ["ph"],
        "resolution": {"default": 0.05, "available": [0.05, 0.1, 0.25]},
        "spatial": {"lon": {"min": 90.0, "max": 134.5}, "lat": {"min": -0.5, "max": 30.0}},
        "temporal": {"start": "2023-01-01", "end": "2023-12-31", "frequency": "daily"},
        "vertical": {"type": "depth", "layers": 14, "range": [0, 400]},
    },
    {
        "id": "scsio-raw",
        "name": "SCSIO 原始日平均（sigma 坐标）",
        "source": "SCSIO",
        "keywords": ["temperature", "salinity", "current", "scsio", "sigma", "raw"],
        "variables": ["temperature", "salinity", "u_current", "v_current"],
        "resolution": {"default": 0.05, "available": [0.05, 0.1, 0.25]},
        "spatial": {"lon": {"min": 90.12, "max": 133.78}, "lat": {"min": 0.80, "max": 30.38}},
        "temporal": {"start": "2023-01-01", "end": "2023-01-31", "frequency": "daily"},
        "vertical": {"type": "sigma", "layers": 45, "range": []},
    },
]

# Mirrors ``config.yaml`` ``preset_regions`` and ``color_styles``.
PRESET_REGIONS: list[dict] = [
    {"name": "Original range",   "north": 30.0, "south": -0.5, "east": 134.5, "west": 90.0},
    {"name": "South China Sea",  "north": 25.0, "south": -0.5, "east": 122.0, "west": 99.0},
    {"name": "Northern SCS",     "north": 25.0, "south": 16.0, "east": 122.0, "west": 105.0},
    {"name": "Nansha (Spratly)", "north": 12.0, "south": 3.0,  "east": 118.0, "west": 108.0},
    {"name": "Xisha (Paracel)",  "north": 18.0, "south": 15.0, "east": 113.0, "west": 110.0},
    {"name": "Beibu Gulf",       "north": 22.0, "south": 17.0, "east": 110.0, "west": 105.0},
]

COLOR_STYLES: list[str] = [
    "viridis", "plasma", "inferno", "turbo",
    "Spectral_r", "RdYlBu_r", "coolwarm", "Greens", "Blues",
]

# Secondary data sources (overlays).  Each follows the same two-level logic
# as "Basic Map": pick a data version/database first, then refine with filters.
CATALOGS: dict = {
    "physical_ocean": {
        "label": "物理海洋结构 Physical Oceanography",
        "databases": [
            {"id": "po-roms-2023",  "name": "ROMS 物理海洋结构（2023）"},
            {"id": "po-cmems-2023", "name": "CMEMS 物理海洋结构（2023）"},
        ],
        "filters": {
            "structure": {"label": "结构要素 Structure", "options": ["流场矢量 Current vectors", "等值线 Contours", "锋面 Fronts", "涡旋 Eddies"]},
            "layer":     {"label": "层次 Layer", "options": ["表层 Surface", "50 m", "100 m", "底层 Bottom"]},
        },
    },
    "fishery": {
        "label": "捕捞信息 Fishery",
        "databases": [
            {"id": "fishery-2026", "name": "2026 渔业捕捞数据库"},
            {"id": "fishery-2025", "name": "2025 渔业捕捞数据库"},
        ],
        "filters": {
            "species": {"label": "鱼种 Species", "options": ["金枪鱼 Tuna", "鲐鱼 Mackerel", "沙丁鱼 Sardine", "鱿鱼 Squid"]},
            "gear":    {"label": "捕捞方式 Gear", "options": ["拖网 Trawl", "围网 Purse seine", "刺网 Gillnet", "延绳钓 Longline"]},
            "area":    {"label": "海域范围 Sea area", "options": ["北部湾 Beibu Gulf", "南海北部 Northern SCS", "南沙 Nansha"]},
        },
    },
    "edna": {
        "label": "eDNA 数据 eDNA",
        "databases": [
            {"id": "edna-2026", "name": "2026 eDNA 数据库"},
            {"id": "edna-2024", "name": "2024 eDNA 数据库"},
        ],
        "filters": {
            "rank":   {"label": "分类等级 Rank", "options": ["门 Phylum", "纲 Class", "目 Order", "科 Family", "属 Genus", "种 Species"]},
            "layer":  {"label": "采样水层 Layer", "options": ["表层 Surface", "中层 Mid-water", "底层 Bottom"]},
            "metric": {"label": "统计指标 Metric", "options": ["丰度 Abundance", "丰富度 Richness", "香农多样性 Shannon"]},
        },
    },
    "ship": {
        "label": "船舶采样 Ship sampling",
        "databases": [
            {"id": "ship-2026", "name": "2026 船舶采样数据库"},
            {"id": "ship-2025", "name": "2025 船舶采样数据库"},
        ],
        "filters": {
            "cruise":    {"label": "航次 Cruise", "options": ["SCS-2026-01", "SCS-2026-02", "SCS-2025-01"]},
            "station":   {"label": "站位 Station", "options": ["全部站位 All", "断面 A Transect A", "断面 B Transect B"]},
            "parameter": {"label": "观测要素 Parameter", "options": ["温盐 CTD", "营养盐 Nutrients", "溶解氧 DO", "叶绿素 Chl-a"]},
        },
    },
    "nightlights": {
        "label": "卫星夜光图 Nighttime lights",
        "core": False,
        "databases": [
            {"id": "nl-viirs-2023", "name": "VIIRS 月合成夜光（2023）"},
            {"id": "nl-dmsp-2013", "name": "DMSP-OLS 稳定灯光（2013）"},
        ],
        "filters": {
            "composite": {"label": "合成周期 Composite", "options": ["月度 Monthly", "年度 Annual"]},
            "month":     {"label": "月份 Month", "options": ["1 月", "4 月", "7 月", "10 月"]},
        },
    },
    "ais": {
        "label": "船舶 AIS 数据 Ship AIS",
        "core": False,
        "databases": [
            {"id": "ais-2026", "name": "2026 船舶 AIS 轨迹"},
            {"id": "ais-2025", "name": "2025 船舶 AIS 轨迹"},
        ],
        "filters": {
            "vessel_type": {"label": "船舶类型 Vessel type", "options": ["货船 Cargo", "渔船 Fishing", "油轮 Tanker"]},
            "window":      {"label": "时间窗口 Window", "options": ["日 Daily", "周 Weekly", "月 Monthly"]},
        },
    },
}

# Achievement showcase (成果展示): image placeholder + intro + download entries.
ACHIEVEMENTS: list[dict] = [
    {
        "id": "ach-fishery-spatiotemporal",
        "title": "南海渔业捕捞时空格局数据集",
        "cover_color": "#b26a2f",
        "tag": "渔业",
        "intro": "南海主要渔场渔获量、物种组成与捕捞努力量的时空分布数据集。",
        "tags": ["渔业", "捕捞", "时空格局"],
        "entries": [
            {"title": "渔获量网格数据", "desc": "分鱼种、分渔具的月渔获量网格（CSV/NetCDF）。", "download": "catch_grid_2023.nc"},
            {"title": "物种组成表", "desc": "主要经济鱼种渔获组成统计表（CSV）。", "download": "species_composition.csv"},
            {"title": "捕捞努力量", "desc": "捕捞努力量（作业天数/网次）分布数据。", "download": "fishing_effort.nc"},
        ],
    },
    {
        "id": "ach-edna-biodiversity",
        "title": "南海 eDNA 生物多样性图谱",
        "cover_color": "#7a4fb2",
        "tag": "eDNA",
        "intro": "基于环境 DNA 的南海鱼类与浮游生物多样性调查结果。",
        "tags": ["eDNA", "生物多样性", "调查"],
        "entries": [
            {"title": "OTU/ASV 丰度表", "desc": "采样站点 OTU/ASV 丰度表（BIOM/CSV）。", "download": "otu_table.biom"},
            {"title": "群落多样性指数", "desc": "各站点 α/β 多样性指数统计表。", "download": "diversity_indices.csv"},
            {"title": "采样站点元数据", "desc": "采样站位、时间、深度等元数据（CSV）。", "download": "edna_station_meta.csv"},
        ],
    },
    {
        "id": "ach-ais-shipping",
        "title": "船舶 AIS 航运与捕捞活动分析",
        "cover_color": "#8a2f3f",
        "tag": "AIS",
        "intro": "基于 AIS 数据的南海船舶密度、航运通道与捕捞活动分析。",
        "tags": ["AIS", "航运", "捕捞活动"],
        "entries": [
            {"title": "船舶密度网格", "desc": "分船舶类型的月度密度网格（GeoTIFF）。", "download": "ais_density.tif"},
            {"title": "轨迹匿名化数据", "desc": "脱敏后的船舶轨迹采样数据（CSV）。", "download": "ais_tracks_sample.csv"},
            {"title": "分析报告", "desc": "航运与捕捞活动时空分析报告（PDF）。", "download": "ais_report.pdf"},
        ],
    },
]

STATS: dict = {
    "n_datasets": len(MOCK_DATASETS),
    "n_files": len(MOCK_DATASETS),
    "spatial": "90–134.5°E · -0.5–30.4°N",
    "temporal": "2023-01-01 → 2023-12-31",
}

# Placeholder time/depth labels (no real data is loaded in the prototype).
_TIME_LABELS: list[str] = [
    (date(2023, 1, 1) + timedelta(days=i)).isoformat() for i in range(31)
]
_DEPTH_LABELS: list[str] = [
    f"{d} m" for d in [0, 20, 40, 60, 80, 100, 120, 140, 160, 200, 250, 300, 350, 400]
]

# Standard upload templates (CSV), downloadable from /api/templates/{kind}.
_TEMPLATES: dict[str, dict] = {
    "fishery": {
        "filename": "fishery_catch_template.csv",
        "content": (
            "# 渔业捕捞数据上传模板（必填列 + 示例行）\n"
            "# lat/纬度, lon/经度, date/日期(YYYY-MM-DD), species/物种, gear/渔具, catch_kg/渔获量(kg)\n"
            "lat,lon,date,species,gear,catch_kg\n"
            "18.5,107.2,2023-05-12,Decapterus maruadsi,trawl,1250.5\n"
            "19.1,108.3,2023-05-12,Rastrelliger kanagurta,gillnet,480.0\n"
        ),
    },
    "station": {
        "filename": "station_observation_template.csv",
        "content": (
            "# 站点观测数据上传模板（必填列 + 示例行）\n"
            "# station_id/站点编号, lat, lon, datetime/时间, variable/变量, value/数值, unit/单位\n"
            "station_id,lat,lon,datetime,variable,value,unit\n"
            "SCS-01,11.20,114.00,2023-06-01T12:00:00,temperature,28.4,degC\n"
            "SCS-01,11.20,114.00,2023-06-01T12:00:00,salinity,33.8,PSU\n"
        ),
    },
    "edna": {
        "filename": "edna_otu_table_template.csv",
        "content": (
            "# eDNA OTU/ASV 丰度表上传模板（必填列 + 示例行）\n"
            "# sample_id/样本编号, lat, lon, depth_m/采样深度, taxon/分类单元, abundance/丰度\n"
            "sample_id,lat,lon,depth_m,taxon,abundance\n"
            "EDNA-001,17.5,110.0,5,Clupeidae,320\n"
            "EDNA-001,17.5,110.0,5,Carangidae,87\n"
        ),
    },
}


def _resolve_variables(names: list[str]) -> list[dict]:
    """Attach display label + units to each canonical variable name."""
    out = []
    for name in names:
        label, units = CANONICAL_VARS.get(name, (name, ""))
        out.append({"name": name, "label": label, "units": units})
    return out


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "home.html")


@app.get("/database")
def database() -> FileResponse:
    return FileResponse(STATIC_DIR / "database.html")


@app.get("/upload")
def upload() -> FileResponse:
    return FileResponse(STATIC_DIR / "upload.html")


@app.get("/download")
def download() -> FileResponse:
    return FileResponse(STATIC_DIR / "download.html")


@app.get("/achievements")
def achievements() -> FileResponse:
    return FileResponse(STATIC_DIR / "achievements.html")


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/datasets")
def list_datasets() -> dict:
    """Return the mock dataset registry + UI presets (colors, regions, stats)."""
    return {
        "datasets": MOCK_DATASETS,
        "preset_regions": PRESET_REGIONS,
        "color_styles": COLOR_STYLES,
        "stats": STATS,
    }


@app.get("/api/catalogs")
def list_catalogs() -> dict:
    """Return secondary-source catalogs (version → filters) for the download page."""
    return {"catalogs": CATALOGS}


@app.get("/api/achievements")
def list_achievements() -> dict:
    """Return the achievement showcase entries."""
    return {"achievements": ACHIEVEMENTS}


@app.get("/api/dataset/{dataset_id}")
def dataset_detail(dataset_id: str) -> dict:
    """Return one dataset's metadata plus placeholder time/depth labels."""
    ds = next((d for d in MOCK_DATASETS if d["id"] == dataset_id), None)
    if ds is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset id: {dataset_id}")
    return {
        **ds,
        "variables": _resolve_variables(ds["variables"]),
        "time_labels": _TIME_LABELS,
        "depth_labels": _DEPTH_LABELS,
    }


@app.get("/api/templates/{kind}")
def download_template(kind: str) -> Response:
    """Return a standard CSV upload template for a given data type."""
    tpl = _TEMPLATES.get(kind)
    if tpl is None:
        raise HTTPException(status_code=404, detail=f"Unknown template: {kind}")
    return Response(
        content=tpl["content"],
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{tpl["filename"]}"'},
    )


# Mount static assets LAST so they do not shadow the API routes.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
