/* ---------------------------------------------------------------------------
   SCS Marine Data Tool — web prototype frontend logic (multi-page v0.2).

   One shared script.  Each page sets <body data-page="...">; the dispatcher
   below runs the matching initializer.  Charts and data remain text
   placeholders — the mock JSON comes from the FastAPI backend (webapp/app.py).
--------------------------------------------------------------------------- */

"use strict";

const $ = (id) => document.getElementById(id);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/* ---------------- shared: active nav ---------------- */
function initNav() {
  const page = document.body.dataset.page;
  const link = document.querySelector(`.main-nav a[data-nav="${page}"]`);
  if (link) link.classList.add("active");
}

/* ---------------- home ---------------- */
function initHome() {
  getJSON("/api/datasets").then((reg) => {
    const s = reg.stats;
    if (!s) return;
    $("stat-datasets").textContent = s.n_datasets;
    $("stat-files").textContent = s.n_files;
    $("stat-spatial").textContent = s.spatial;
    $("stat-temporal").textContent = s.temporal;
  }).catch(() => {});
}

/* ---------------- database ---------------- */
function initDatabase() {
  let datasets = [];
  const state = { q: "", source: "", sortKey: "name", sortAsc: true };

  const fmtSpatial = (d) =>
    `${d.spatial.lon.min}–${d.spatial.lon.max}°E, ${d.spatial.lat.min}–${d.spatial.lat.max}°N`;

  const fmtVertical = (d) =>
    d.vertical.type === "depth"
      ? `depth ${d.vertical.range[0]}–${d.vertical.range[1]} m (${d.vertical.layers} 层)`
      : `${d.vertical.type} (${d.vertical.layers} 层)`;

  const sortVal = (d, key) => {
    if (key === "resolution") return d.resolution.default;
    if (key === "temporal") return d.temporal.start;
    return String(d[key] || "").toLowerCase();
  };

  function apply() {
    const rows = datasets.filter((d) => {
      const hay = [d.name, d.source, ...d.keywords, ...d.variables].join(" ").toLowerCase();
      if (state.q && !hay.includes(state.q)) return false;
      if (state.source && d.source !== state.source) return false;
      return true;
    });
    rows.sort((a, b) => {
      const av = sortVal(a, state.sortKey), bv = sortVal(b, state.sortKey);
      if (typeof av === "number" && typeof bv === "number")
        return state.sortAsc ? av - bv : bv - av;
      return state.sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
    render(rows);
  }

  function render(rows) {
    const tbody = $("db-tbody");
    tbody.innerHTML = "";
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-hint">无匹配数据集</td></tr>';
    }
    rows.forEach((d) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="name-cell">${d.name}</td>
        <td>${d.source}</td>
        <td>${d.variables.join(", ")}</td>
        <td>${fmtSpatial(d)}</td>
        <td>${d.temporal.start} → ${d.temporal.end}</td>
        <td>${d.resolution.default}°</td>
        <td>${fmtVertical(d)}</td>
        <td class="ops">
          <a class="link" href="/download?id=${encodeURIComponent(d.id)}">下载</a>
          <button class="link" data-view="${d.id}">查看</button>
        </td>`;
      tbody.appendChild(tr);
    });
    $("db-count").textContent = `共 ${rows.length} 条`;
  }

  getJSON("/api/datasets").then((reg) => {
    datasets = reg.datasets;
    const srcs = [...new Set(datasets.map((d) => d.source))];
    const sel = $("db-source");
    srcs.forEach((s) => sel.add(new Option(s, s)));
    apply();
  });

  $("db-search").addEventListener("input", (e) => {
    state.q = e.target.value.trim().toLowerCase(); apply();
  });
  $("db-source").addEventListener("change", (e) => {
    state.source = e.target.value; apply();
  });
  $("db-reset").addEventListener("click", () => {
    $("db-search").value = ""; $("db-source").value = "";
    state.q = ""; state.source = ""; apply();
  });

  $$("#db-table th[data-sort]").forEach((th) => th.addEventListener("click", () => {
    const k = th.dataset.sort;
    if (state.sortKey === k) state.sortAsc = !state.sortAsc;
    else { state.sortKey = k; state.sortAsc = true; }
    apply();
  }));

  $("db-tbody").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-view]");
    if (!btn) return;
    const d = datasets.find((x) => x.id === btn.dataset.view);
    if (!d) return;
    alert(
      `数据集：${d.name}\n来源：${d.source}\n关键词：${d.keywords.join(", ")}\n` +
      `变量：${d.variables.join(", ")}\n分辨率：${d.resolution.default}°`
    );
  });
}

/* ---------------- upload ---------------- */
function initUpload() {
  const drop = $("drop-zone");
  const input = $("file-input");
  const tbody = $("upload-tbody");
  let rows = 0;

  const ACCEPT = {
    ".nc": "NetCDF", ".nc4": "NetCDF", ".h5": "HDF5", ".hdf5": "HDF5",
    ".csv": "CSV", ".tsv": "TSV", ".xlsx": "Excel", ".xls": "Excel",
    ".geojson": "GeoJSON", ".shp": "Shapefile", ".tif": "GeoTIFF", ".tiff": "GeoTIFF",
    ".fa": "FASTA", ".fasta": "FASTA", ".biom": "BIOM",
  };

  const ext = (name) => {
    const i = name.lastIndexOf(".");
    return i >= 0 ? name.slice(i).toLowerCase() : "";
  };

  function addFiles(files) {
    if (rows === 0) tbody.innerHTML = "";
    for (const f of files) {
      const e = ext(f.name);
      const ok = e in ACCEPT;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${f.name}</td>
        <td>${f.size ? (f.size / 1024).toFixed(1) + " KB" : "—"}</td>
        <td>${ok ? ACCEPT[e] : "未知格式"}</td>
        <td class="${ok ? "ok" : "bad"}">${ok ? "格式校验通过（待入库）" : "暂不支持该格式"}</td>`;
      tbody.appendChild(tr);
      rows++;
    }
  }

  input.addEventListener("change", () => { addFiles(input.files); input.value = ""; });
  drop.addEventListener("click", () => input.click());
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("dragover"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("dragover"));
  drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("dragover"); addFiles(e.dataTransfer.files); });
}

/* ---------------- download (data preview + download) ---------------- */
function initDownload() {
  let registry = null;   // /api/datasets
  let catalogs = null;   // /api/catalogs
  let detail = null;
  const catState = {};   // catId -> { db, filters }

  const dsSel   = $("dataset-select");
  const varSel  = $("var-select");
  const depthSel= $("depth-select");
  const timeSel = $("time-select");
  const cmapSel = $("cmap-select");
  const regionSel = $("region-select");
  const nIn = $("n-input"), sIn = $("s-input"), eIn = $("e-input"), wIn = $("w-input");
  const autoChk = $("range-auto"), vminIn = $("vmin-input"), vmaxIn = $("vmax-input");
  const mapPh = $("pane-map");

  function currentRegionLabel() {
    if (regionSel.value !== "custom") return regionSel.value;
    return `自定义 (N ${nIn.value}°, S ${sIn.value}°, E ${eIn.value}°, W ${wIn.value}°)`;
  }

  function currentRangeLabel() {
    return autoChk.checked ? "自动" : `${vminIn.value || "?"}–${vmaxIn.value || "?"}`;
  }

  function collectOverlays() {
    if (!catalogs) return [];
    const labels = [];
    for (const [catId, st] of Object.entries(catState)) {
      if (!st.db) continue;
      const db = catalogs[catId].databases.find((d) => d.id === st.db);
      const cn = (catalogs[catId].label || catId).split(" ")[0];
      labels.push(`${cn}（${db ? db.name : st.db}）`);
    }
    return labels;
  }

  function update() {
    if (!detail) return;
    const v = detail.variables.find((x) => x.name === varSel.value);
    const varName = v ? v.label : varSel.value;
    let html = `
      <span class="ph-title">Data preview placeholder</span>
      <span class="ph-desc">将在此预览 ${detail.source} · ${varName}</span>
      <span class="ph-desc">${timeSel.value} · ${depthSel.value} · ${currentRegionLabel()}</span>
      <span class="ph-desc">色标 ${cmapSel.value} · 数值范围 ${currentRangeLabel()}</span>`;
    const overlays = collectOverlays();
    if (overlays.length) html += `<span class="ph-desc">叠加 Overlay：${overlays.join("；")}</span>`;
    mapPh.innerHTML = html;
  }

  function refreshCategory(catId, details) {
    const st = catState[catId];
    const stateEl = details.querySelector('[data-role="state"]');
    const selEl = details.querySelector('[data-role="selected"]');
    if (!st.db) {
      stateEl.textContent = "未选择";
      stateEl.classList.remove("picked");
      selEl.hidden = true;
    } else {
      const dbName = details.querySelector(".cat-db").selectedOptions[0].textContent;
      const parts = [dbName];
      details.querySelectorAll(".cat-filter").forEach((fs) => { if (fs.value) parts.push(fs.value); });
      stateEl.textContent = "已选";
      stateEl.classList.add("picked");
      selEl.hidden = false;
      selEl.textContent = "当前：" + parts.join(" · ");
    }
    update();
  }

  function buildCatalogPanel(container, catId, cat) {
    catState[catId] = { db: "", filters: {} };

    const filtersHtml = Object.entries(cat.filters).map(([key, f]) => `
      <label class="field">${f.label}
        <select class="cat-filter" data-cat="${catId}" data-key="${key}" disabled>
          <option value="">— 选择 —</option>
          ${f.options.map((o) => `<option>${o}</option>`).join("")}
        </select>
      </label>`).join("");

    const details = document.createElement("details");
    details.className = "param-group" + (cat.core === false ? " simple" : "");
    details.dataset.cat = catId;
    details.innerHTML = `
      <summary>${cat.label} <span class="cat-state" data-role="state">未选择</span></summary>
      <div class="pg-body">
        <label class="field">数据版本 Database
          <select class="cat-db" data-cat="${catId}">
            <option value="">— 选择数据库 —</option>
            ${cat.databases.map((d) => `<option value="${d.id}">${d.name}</option>`).join("")}
          </select>
        </label>
        ${filtersHtml}
        <p class="cat-selected" data-role="selected" hidden></p>
      </div>`;
    container.appendChild(details);

    details.querySelector(".cat-db").addEventListener("change", () => {
      const st = catState[catId];
      st.db = details.querySelector(".cat-db").value;
      details.querySelectorAll(".cat-filter").forEach((fs) => {
        fs.disabled = !st.db;
        if (!st.db) fs.value = "";
      });
      if (!st.db) st.filters = {};
      refreshCategory(catId, details);
    });
    details.querySelectorAll(".cat-filter").forEach((fs) => {
      fs.addEventListener("change", () => {
        catState[catId].filters[fs.dataset.key] = fs.value;
        refreshCategory(catId, details);
      });
    });
  }

  function renderCatalogPanels() {
    const container = $("category-panels");
    container.innerHTML = "";
    const core = Object.entries(catalogs).filter(([, c]) => c.core !== false);
    const simple = Object.entries(catalogs).filter(([, c]) => c.core === false);

    core.forEach(([catId, cat]) => buildCatalogPanel(container, catId, cat));

    if (simple.length) {
      const head = document.createElement("div");
      head.className = "cat-group-head";
      head.textContent = "附加展示 Additional · 简单展示（非核心）";
      container.appendChild(head);
      simple.forEach(([catId, cat]) => buildCatalogPanel(container, catId, cat));
    }
  }

  function loadDataset(id) {
    getJSON(`/api/dataset/${encodeURIComponent(id)}`).then((d) => {
      detail = d;

      varSel.innerHTML = "";
      d.variables.forEach((v) => varSel.add(new Option(`${v.label} (${v.units})`, v.name)));

      depthSel.innerHTML = "";
      d.depth_labels.forEach((x) => depthSel.add(new Option(x, x)));

      timeSel.innerHTML = "";
      d.time_labels.forEach((x) => timeSel.add(new Option(x, x)));

      nIn.value = d.spatial.lat.max;
      sIn.value = d.spatial.lat.min;
      eIn.value = d.spatial.lon.max;
      wIn.value = d.spatial.lon.min;
      regionSel.value = "custom";

      varSel.disabled = false;
      depthSel.disabled = false;
      timeSel.disabled = false;

      update();
    });
  }

  getJSON("/api/datasets").then((reg) => {
    registry = reg;

    dsSel.innerHTML = "";
    reg.datasets.forEach((d) => dsSel.add(new Option(d.name, d.id)));

    regionSel.innerHTML = "";
    regionSel.add(new Option("— 自定义 Custom —", "custom"));
    reg.preset_regions.forEach((r) => regionSel.add(new Option(r.name, r.name)));

    cmapSel.innerHTML = "";
    reg.color_styles.forEach((c) => cmapSel.add(new Option(c, c)));
    cmapSel.value = "Spectral_r";

    // Preselect dataset when arriving from the database "下载" link (?id=...).
    const presetId = new URLSearchParams(location.search).get("id");
    if (presetId && reg.datasets.some((d) => d.id === presetId)) {
      dsSel.value = presetId;
      loadDataset(presetId);
    }
  });

  getJSON("/api/catalogs").then((cats) => {
    catalogs = cats.catalogs;
    renderCatalogPanels();
  });

  dsSel.addEventListener("change", () => loadDataset(dsSel.value));

  const refresh = () => update();
  [varSel, depthSel, timeSel, cmapSel].forEach((el) => el.addEventListener("change", refresh));

  regionSel.addEventListener("change", () => {
    const name = regionSel.value;
    const r = name !== "custom" && registry ? registry.preset_regions.find((x) => x.name === name) : null;
    if (r) { nIn.value = r.north; sIn.value = r.south; eIn.value = r.east; wIn.value = r.west; }
    refresh();
  });

  [nIn, sIn, eIn, wIn].forEach((el) => el.addEventListener("input", () => {
    regionSel.value = "custom"; refresh();
  }));

  autoChk.addEventListener("change", () => {
    vminIn.disabled = autoChk.checked;
    vmaxIn.disabled = autoChk.checked;
    refresh();
  });
  [vminIn, vmaxIn].forEach((el) => el.addEventListener("input", refresh));

  $("plot-btn").addEventListener("click", refresh);

  // Tabs (preview / time series / table) — placeholders for now.
  const tabs = $$(".tab");
  const panes = { map: $("pane-map"), ts: $("pane-ts"), table: $("pane-table") };
  tabs.forEach((t) => t.addEventListener("click", () => {
    tabs.forEach((x) => x.classList.remove("active"));
    t.classList.add("active");
    Object.values(panes).forEach((p) => { p.hidden = true; });
    panes[t.dataset.tab].hidden = false;
  }));
}

/* ---------------- achievements ---------------- */
function initAchievements() {
  const grid = $("ach-grid");
  const modal = $("ach-modal");
  const detailEl = $("ach-detail");
  const closeBtn = $("ach-close");
  let items = [];

  function render() {
    grid.innerHTML = "";
    items.forEach((a) => {
      const card = document.createElement("article");
      card.className = "ach-card";
      card.dataset.id = a.id;
      card.innerHTML = `
        <div class="ach-cover" style="background: linear-gradient(135deg, ${a.cover_color}, ${a.cover_color}cc)">
          <span class="ach-cover-tag">${a.tag}</span>
        </div>
        <div class="ach-body">
          <h3>${a.title}</h3>
          <p class="ach-intro">${a.intro}</p>
          <div class="ach-tags">${a.tags.map((t) => `<span>${t}</span>`).join("")}</div>
        </div>`;
      card.addEventListener("click", () => open(a));
      grid.appendChild(card);
    });
  }

  function open(a) {
    detailEl.innerHTML = `
      <div class="ach-cover ach-cover-lg" style="background: linear-gradient(135deg, ${a.cover_color}, ${a.cover_color}cc)">
        <span class="ach-cover-tag">${a.tag}</span>
      </div>
      <h2>${a.title}</h2>
      <p class="ach-intro">${a.intro}</p>
      <div class="ach-entries">
        ${a.entries.map((e) => `
          <div class="ach-entry">
            <div class="ach-entry-body">
              <h4>${e.title}</h4>
              <p>${e.desc}</p>
            </div>
            <button class="btn" data-dl="${e.download}">下载</button>
          </div>`).join("")}
      </div>`;
    modal.hidden = false;
  }

  detailEl.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-dl]");
    if (btn) alert(`下载待接入：${btn.dataset.dl}`);
  });
  closeBtn.addEventListener("click", () => { modal.hidden = true; });
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.hidden = true; });

  getJSON("/api/achievements").then((res) => {
    items = res.achievements;
    render();
  });
}

/* ---------------- dispatcher ---------------- */
const PAGES = {
  home: initHome,
  database: initDatabase,
  upload: initUpload,
  download: initDownload,
  achievements: initAchievements,
};

document.addEventListener("DOMContentLoaded", () => {
  initNav();
  const fn = PAGES[document.body.dataset.page];
  if (fn) fn();
});
