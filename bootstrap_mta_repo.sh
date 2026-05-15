#!/usr/bin/env bash
set -euo pipefail

# =========================================================
# MTA SOLOLÁ · BOOTSTRAP PUERCO v0.1
# Crea una repo estática de alto nivel para comenzar el
# Atlas Agroclimático y el sistema diario de estaciones.
#
# Uso:
#   mkdir mta-solola && cd mta-solola
#   bash bootstrap_mta_repo.sh
#   python3 -m http.server 8080 -d docs
#   abrir http://localhost:8080
# =========================================================

mkdir -p \
  docs/assets/css \
  docs/assets/js \
  docs/assets/img \
  docs/data \
  docs/atlas \
  docs/estaciones \
  scripts \
  archive/raw_pages \
  archive/snapshots \
  reports

cat > README.md <<'EOF'
# Plataforma Agroclimática de Sololá · MTA

Prototipo inicial para una plataforma diaria de monitoreo agroclimático:

- Inventario de estaciones meteorológicas.
- Consulta diaria de fuentes institucionales autorizadas.
- Atlas de mapas interactivos.
- Fichas de estaciones.
- Créditos por institución.
- Base para boletines agroclimáticos.

## Correr local

```bash
python3 -m http.server 8080 -d docs
```

Abrir:

```text
http://localhost:8080
```

## Primeros archivos importantes

```text
docs/index.html                 Página inicial
docs/atlas/index.html           Atlas agroclimático
docs/estaciones/index.html      Mapa/listado de estaciones
docs/data/fuentes_estaciones.json
docs/data/map_catalog.json
scripts/auditar_fuentes.py
```
EOF

cat > docs/assets/css/mta-theme.css <<'EOF'
:root {
  --font-display: "Lora", Georgia, serif;
  --font-body: "Sora", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-data: "JetBrains Mono", Consolas, monospace;

  --ink: #0e2433;
  --navy: #17314f;
  --lake-900: #0f3a53;
  --lake-700: #176680;
  --lake-500: #2a9db7;
  --lake-100: #e6f5f7;
  --rain-700: #1f6fb2;
  --rain-500: #4aa3df;
  --forest-700: #2f7a62;
  --forest-100: #eaf7ef;
  --maize-500: #e7b94f;
  --earth-500: #b47a4c;
  --coffee-600: #7a4b34;
  --page: #f6f8f3;
  --surface: #ffffff;
  --surface-soft: #f1f7f4;
  --line: #d7e5df;
  --muted: #708391;
  --text-soft: #3b5363;

  --risk-normal: #2f7a62;
  --risk-watch: #d5a11e;
  --risk-high: #d66a2a;
  --risk-extreme: #a33b35;

  --radius: 26px;
  --shadow: 0 18px 44px rgba(14,36,51,.10), 0 4px 12px rgba(14,36,51,.05);
  --wrap: min(1480px, calc(100vw - 32px));
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font-body);
  color: var(--ink);
  background:
    radial-gradient(circle at 12% 6%, rgba(42,157,183,.22), transparent 28%),
    radial-gradient(circle at 88% 10%, rgba(47,122,98,.18), transparent 32%),
    linear-gradient(180deg, #fbfcf8 0%, var(--page) 100%);
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  background-image:
    linear-gradient(rgba(23,49,79,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23,49,79,.035) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,.55), transparent 78%);
}
a { color: inherit; }
.wrap { width: var(--wrap); margin: 0 auto; }

.header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 18px;
  min-height: 78px;
  padding: 12px 28px;
  color: #fff;
  background: linear-gradient(135deg, var(--lake-900), var(--lake-700) 55%, var(--lake-500));
  box-shadow: 0 14px 34px rgba(13,39,67,.18);
}
.brand {
  display: flex;
  align-items: center;
  gap: 13px;
  text-decoration: none;
  min-width: 270px;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: #fff;
  color: var(--lake-900);
  font-weight: 900;
  box-shadow: 0 8px 20px rgba(0,0,0,.16);
}
.brand small {
  display: block;
  font-size: .72rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  opacity: .76;
  font-weight: 900;
}
.brand strong { display: block; line-height: 1.1; }
.nav {
  display: flex;
  gap: 6px;
  margin-left: auto;
  overflow-x: auto;
  scrollbar-width: none;
}
.nav::-webkit-scrollbar { display: none; }
.nav a {
  text-decoration: none;
  color: rgba(255,255,255,.86);
  padding: 10px 12px;
  border-radius: 999px;
  white-space: nowrap;
  font-weight: 800;
  font-size: .88rem;
}
.nav a:hover, .nav a[aria-current="page"] { background: rgba(255,255,255,.14); color: #fff; }

.hero { padding: clamp(46px, 8vw, 94px) 0 48px; }
.hero-grid { display: grid; grid-template-columns: 1fr .95fr; gap: 28px; align-items: center; }
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: .72rem;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--lake-700);
  font-weight: 950;
}
.eyebrow::before { content: ""; width: 28px; height: 2px; border-radius: 999px; background: var(--maize-500); }
h1, h2, h3 { margin: 0; color: var(--navy); line-height: 1.05; letter-spacing: -.035em; }
h1 { margin-top: 14px; font-family: var(--font-display); font-size: clamp(2.45rem, 5.2vw, 5.35rem); max-width: 12ch; }
h2 { font-family: var(--font-display); font-size: clamp(1.6rem, 3vw, 2.7rem); }
h3 { font-size: clamp(1.12rem, 1.6vw, 1.45rem); }
p { color: var(--text-soft); line-height: 1.7; }
.lead { font-size: clamp(1.05rem, 1.5vw, 1.25rem); max-width: 64ch; }

.actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 10px 18px;
  border: 0;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 900;
  cursor: pointer;
}
.btn-primary { color: #fff; background: var(--lake-700); box-shadow: var(--shadow); }
.btn-soft { color: var(--lake-900); background: var(--lake-100); }
.btn-ghost { color: var(--navy); background: rgba(255,255,255,.72); border: 1px solid var(--line); }

.grid { display: grid; gap: 16px; }
.kpi-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.card {
  position: relative;
  border: 1px solid rgba(215,229,223,.92);
  border-radius: var(--radius);
  background: linear-gradient(180deg, rgba(255,255,255,.97), rgba(246,250,248,.94));
  box-shadow: var(--shadow);
  overflow: hidden;
}
.card::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(135deg, rgba(255,255,255,.6), transparent 42%);
}
.card-body { position: relative; z-index: 1; padding: 22px; }
.kpi-value {
  display: block;
  margin: 16px 0 8px;
  font-family: var(--font-data);
  font-size: clamp(2rem, 4vw, 4rem);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -.06em;
  color: var(--lake-900);
}
.kpi-label {
  display: block;
  color: var(--muted);
  font-size: .74rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  font-weight: 950;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: .73rem;
  text-transform: uppercase;
  letter-spacing: .08em;
  font-weight: 950;
}
.badge::before { content: ""; width: 8px; height: 8px; border-radius: 99px; background: currentColor; }
.badge-normal { color: var(--risk-normal); background: rgba(47,122,98,.12); }
.badge-watch { color: #9a6d0a; background: rgba(213,161,30,.17); }
.badge-high { color: var(--risk-high); background: rgba(214,106,42,.14); }

.section { padding: 52px 0; }
.section-head { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 22px; }
.section-head p { max-width: 72ch; }

/* Gráficos tipo tarjeta, inspirados en dashboards limpios de estaciones */
.vm-chart {
  min-height: 340px;
  padding: 18px;
  border-radius: 28px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}
.vm-chart-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}
.vm-chart-title { font-weight: 950; color: var(--navy); }
.vm-chart-meta { color: var(--muted); font-size: .82rem; }
.vm-bars {
  height: 210px;
  display: flex;
  align-items: end;
  gap: 8px;
  padding: 16px 4px 0;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(74,163,223,.08), transparent 58%);
}
.vm-bar {
  flex: 1;
  min-width: 10px;
  border-radius: 999px 999px 4px 4px;
  background: linear-gradient(180deg, var(--rain-500), var(--rain-700));
}
.vm-chart-foot {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
  color: var(--muted);
  font-size: .78rem;
}

.map-layout {
  display: grid;
  grid-template-columns: 310px 1fr 360px;
  gap: 14px;
  min-height: min(760px, calc(100vh - 150px));
}
.panel {
  border: 1px solid var(--line);
  border-radius: 24px;
  background: rgba(255,255,255,.9);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.panel-head { padding: 16px 18px; background: var(--surface-soft); border-bottom: 1px solid var(--line); }
.panel-body { padding: 16px 18px; }
.map-canvas {
  min-height: 640px;
  border: 1px solid var(--line);
  border-radius: 30px;
  background:
    radial-gradient(circle at 44% 42%, rgba(42,157,183,.36), transparent 12%),
    radial-gradient(circle at 58% 58%, rgba(47,122,98,.26), transparent 18%),
    linear-gradient(135deg, #dff2f6, #eef7ef);
  box-shadow: var(--shadow);
  position: relative;
  overflow: hidden;
}
.fake-solola {
  position: absolute;
  inset: 10% 13%;
  border-radius: 48% 52% 46% 54% / 54% 42% 58% 46%;
  background: rgba(255,255,255,.52);
  border: 2px solid rgba(15,58,83,.22);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.45);
}
.station-dot {
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 99px;
  background: var(--maize-500);
  border: 3px solid #fff;
  box-shadow: 0 4px 12px rgba(14,36,51,.25);
  cursor: pointer;
}
.station-dot:hover { transform: scale(1.16); }
.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 16px;
  background: var(--surface-soft);
  border: 1px solid #e6f0eb;
}
.layer-item strong { color: var(--navy); font-size: .9rem; }
.layer-item small { color: var(--muted); }
.credit {
  display: flex;
  flex-wrap: wrap;
  gap: 7px 10px;
  margin-top: 14px;
  color: var(--muted);
  font-size: .76rem;
}
.credit span {
  display: inline-flex;
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(255,255,255,.76);
  border: 1px solid var(--line);
}

.table-wrap { overflow: auto; border: 1px solid var(--line); border-radius: 22px; background: #fff; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 13px 14px; border-bottom: 1px solid #e9f1ed; text-align: left; }
th { color: var(--navy); background: var(--surface-soft); font-size: .74rem; letter-spacing: .1em; text-transform: uppercase; }
td { color: var(--text-soft); font-size: .92rem; }

@media (max-width: 1100px) {
  .hero-grid, .map-layout { grid-template-columns: 1fr; }
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .nav { display: none; }
  .brand { min-width: 0; }
  .kpi-grid { grid-template-columns: 1fr; }
  .section-head { display: block; }
}
EOF

cat > docs/data/fuentes_estaciones.json <<'EOF'
{
  "version": "0.1-puerco",
  "actualizado": null,
  "nota": "Inventario semilla. Revisar, depurar duplicados y completar coordenadas.",
  "fuentes": [
    {
      "id": "vivamos_mejor",
      "nombre": "Asociación Vivamos Mejor",
      "tipo": "institucion_participante",
      "metodo_consulta": "pagina_web_autorizada",
      "frecuencia_minima": "diaria",
      "url_publica": "https://www.vivamosmejor.org.gt/sitio/estaciones-meteorologicas-solola/",
      "credito_base": "Datos: Asociación Vivamos Mejor. Visualización y procesamiento: Mesa Agroclimática de Sololá.",
      "estaciones": [
        { "id": "vm_oficina_central_panajachel", "nombre": "Estación Oficina Central", "municipio": "Panajachel", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] },
        { "id": "vm_casa_santa_rita_santa_lucia_utatlan", "nombre": "Estación Casa Santa Rita", "municipio": "Santa Lucía Utatlán", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] },
        { "id": "vm_coatitlan_santiago_atitlan", "nombre": "Estación CoAtitlán R.L.", "municipio": "Santiago Atitlán", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] },
        { "id": "vm_lomas_atitlan_san_andres", "nombre": "Estación Lomas de Atitlán", "municipio": "San Andrés Semetabaj", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] },
        { "id": "vm_cedracc_santa_cruz", "nombre": "Estación CEDRACC", "municipio": "Santa Cruz La Laguna", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] },
        { "id": "vm_santa_clara_tv_cable", "nombre": "Estación Santa Clara TV Cable", "municipio": "Santa Clara La Laguna", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] },
        { "id": "vm_chuacruz_pujujil", "nombre": "Caserío Chuacruz", "municipio": "Aldea Pujujil I, Sololá", "estado": "mantenimiento", "variables": [] },
        { "id": "vm_efa_solola", "nombre": "Estación Escuela de Formación Agrícola", "municipio": "Sololá", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] }
      ]
    },
    {
      "id": "insivumeh",
      "nombre": "INSIVUMEH",
      "tipo": "institucion_participante_oficial",
      "metodo_consulta": "pagina_web_autorizada",
      "frecuencia_minima": "diaria",
      "url_publica": "https://insivumeh.gob.gt/",
      "credito_base": "Datos: INSIVUMEH. Visualización y procesamiento: Mesa Agroclimática de Sololá.",
      "estaciones": [
        { "id": "insivumeh_el_capitan", "nombre": "El Capitán", "municipio": "por_verificar", "estado": "por_verificar", "variables": ["precipitacion"] },
        { "id": "insivumeh_el_tablon", "nombre": "El Tablón", "municipio": "Sololá", "estado": "por_verificar", "variables": ["precipitacion", "temperatura", "humedad", "viento"] },
        { "id": "insivumeh_santiago_atitlan", "nombre": "Santiago Atitlán", "municipio": "Santiago Atitlán", "estado": "por_verificar", "variables": ["precipitacion"] }
      ]
    },
    {
      "id": "amsclae",
      "nombre": "AMSCLAE",
      "tipo": "institucion_participante",
      "metodo_consulta": "pagina_web_autorizada_o_documentos",
      "frecuencia_minima": "diaria_si_hay_datos_publicados",
      "url_publica": "https://www.amsclae.gob.gt/",
      "credito_base": "Datos: AMSCLAE. Visualización y procesamiento: Mesa Agroclimática de Sololá.",
      "estaciones": []
    },
    {
      "id": "icc",
      "nombre": "Instituto Privado de Investigación sobre Cambio Climático - ICC",
      "tipo": "institucion_participante",
      "metodo_consulta": "pagina_web_autorizada",
      "frecuencia_minima": "diaria_si_aplica",
      "url_publica": "https://www.icc.org.gt/es/clima/",
      "credito_base": "Datos: ICC. Visualización y procesamiento: Mesa Agroclimática de Sololá.",
      "estaciones": []
    }
  ]
}
EOF

cat > docs/data/map_catalog.json <<'EOF'
{
  "version": "0.1-puerco",
  "grupos": [
    {
      "id": "estaciones",
      "titulo": "Estaciones meteorológicas",
      "mapas": [
        { "id": "todas_estaciones", "titulo": "Todas las estaciones", "tipo": "puntos", "dato": "observado", "actualizacion": "diaria" },
        { "id": "estaciones_por_institucion", "titulo": "Estaciones por institución", "tipo": "puntos", "dato": "observado", "actualizacion": "diaria" },
        { "id": "estaciones_activas", "titulo": "Estaciones activas", "tipo": "puntos", "dato": "observado", "actualizacion": "diaria" }
      ]
    },
    {
      "id": "lluvia",
      "titulo": "Lluvia",
      "mapas": [
        { "id": "lluvia_24h", "titulo": "Lluvia últimas 24 horas", "tipo": "raster_vector", "dato": "observado_estimado", "actualizacion": "diaria" },
        { "id": "lluvia_7d", "titulo": "Lluvia últimos 7 días", "tipo": "raster_vector", "dato": "observado_estimado", "actualizacion": "diaria" },
        { "id": "lluvia_mensual", "titulo": "Lluvia acumulada mensual", "tipo": "raster_vector", "dato": "observado_estimado", "actualizacion": "diaria" },
        { "id": "anomalia_lluvia", "titulo": "Anomalía de lluvia", "tipo": "raster_vector", "dato": "estimado", "actualizacion": "diaria" }
      ]
    },
    {
      "id": "riesgos",
      "titulo": "Riesgos agroclimáticos",
      "mapas": [
        { "id": "semaforo_municipal", "titulo": "Semáforo agroclimático municipal", "tipo": "poligonos", "dato": "estimado_validado", "actualizacion": "diaria" },
        { "id": "riesgo_deslizamiento", "titulo": "Riesgo por deslizamientos", "tipo": "poligonos", "dato": "estimado", "actualizacion": "diaria" },
        { "id": "riesgo_sequia", "titulo": "Riesgo por sequía", "tipo": "poligonos", "dato": "estimado", "actualizacion": "diaria" }
      ]
    }
  ]
}
EOF

cat > docs/assets/js/app.js <<'EOF'
async function loadJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`No pude cargar ${path}`);
  return response.json();
}

function flattenStations(data) {
  return data.fuentes.flatMap((fuente) =>
    (fuente.estaciones || []).map((station) => ({
      ...station,
      institucion_id: fuente.id,
      institucion: fuente.nombre,
      credito: fuente.credito_base,
      url_publica: fuente.url_publica
    }))
  );
}

function renderStationsTable(stations, target = "#stations-table") {
  const el = document.querySelector(target);
  if (!el) return;

  el.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Estación</th>
            <th>Institución</th>
            <th>Municipio</th>
            <th>Estado</th>
            <th>Variables</th>
          </tr>
        </thead>
        <tbody>
          ${stations.map(station => `
            <tr>
              <td><strong>${station.nombre}</strong></td>
              <td>${station.institucion}</td>
              <td>${station.municipio || "Por verificar"}</td>
              <td>${station.estado || "por_verificar"}</td>
              <td>${(station.variables || []).join(", ") || "Por verificar"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderFakeStationDots(stations, target = "#station-map") {
  const el = document.querySelector(target);
  if (!el) return;

  const positions = [
    [24, 34], [38, 28], [51, 43], [66, 34],
    [31, 58], [45, 66], [61, 61], [72, 54],
    [19, 49], [54, 23], [80, 44]
  ];

  const dots = stations.slice(0, 11).map((station, index) => {
    const [left, top] = positions[index] || [50, 50];
    return `<button class="station-dot" style="left:${left}%;top:${top}%;" title="${station.nombre} · ${station.institucion}" data-station="${station.id}"></button>`;
  }).join("");

  el.innerHTML = `<div class="fake-solola"></div>${dots}`;

  el.querySelectorAll(".station-dot").forEach((dot) => {
    dot.addEventListener("click", () => {
      const station = stations.find(s => s.id === dot.dataset.station);
      const detail = document.querySelector("#map-detail");
      if (!detail || !station) return;
      detail.innerHTML = `
        <h3>${station.nombre}</h3>
        <p><strong>Institución:</strong> ${station.institucion}</p>
        <p><strong>Municipio:</strong> ${station.municipio || "Por verificar"}</p>
        <p><strong>Estado:</strong> ${station.estado || "por verificar"}</p>
        <p><strong>Variables:</strong> ${(station.variables || []).join(", ") || "Por verificar"}</p>
        <div class="credit"><span>${station.credito}</span></div>
      `;
    });
  });
}

function renderMapCatalog(catalog, target = "#layer-list") {
  const el = document.querySelector(target);
  if (!el) return;

  el.innerHTML = catalog.grupos.map(group => `
    <div style="margin-bottom:18px">
      <h3 style="margin-bottom:10px">${group.titulo}</h3>
      ${group.mapas.map(map => `
        <div class="layer-item">
          <div>
            <strong>${map.titulo}</strong><br>
            <small>${map.dato} · ${map.actualizacion}</small>
          </div>
          <input type="checkbox" ${map.id === "todas_estaciones" ? "checked" : ""}>
        </div>
      `).join("")}
    </div>
  `).join("");
}

function renderDemoChart(target = "#demo-chart") {
  const el = document.querySelector(target);
  if (!el) return;
  const values = [18, 42, 25, 61, 74, 38, 58, 83, 46, 65, 31, 52];
  el.innerHTML = `
    <div class="vm-chart">
      <div class="vm-chart-head">
        <div>
          <div class="vm-chart-title">Lluvia diaria · demo visual</div>
          <div class="vm-chart-meta">Estilo base para gráficas de estaciones</div>
        </div>
        <span class="badge badge-normal">Observado</span>
      </div>
      <div class="vm-bars">
        ${values.map(v => `<div class="vm-bar" style="height:${v}%"></div>`).join("")}
      </div>
      <div class="vm-chart-foot">
        <span>Fuente: institución participante</span>
        <span>Procesamiento: MTA Sololá</span>
      </div>
    </div>
  `;
}

async function bootHome() {
  const fuentes = await loadJSON("data/fuentes_estaciones.json");
  const catalog = await loadJSON("data/map_catalog.json");
  const stations = flattenStations(fuentes);

  document.querySelector("#station-count").textContent = stations.length;
  document.querySelector("#source-count").textContent = fuentes.fuentes.length;
  document.querySelector("#map-count").textContent = catalog.grupos.reduce((acc, g) => acc + g.mapas.length, 0);

  renderStationsTable(stations);
  renderFakeStationDots(stations);
  renderMapCatalog(catalog);
  renderDemoChart();
}

bootHome().catch((error) => {
  console.error(error);
  const el = document.querySelector("#app-error");
  if (el) el.textContent = error.message;
});
EOF

cat > docs/index.html <<'EOF'
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MTA Sololá · Plataforma Agroclimática</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@600;800&family=Lora:wght@600;700&family=Sora:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/mta-theme.css">
</head>
<body>
  <header class="header">
    <a class="brand" href="/">
      <span class="brand-mark">MTA</span>
      <span>
        <small>Sololá</small>
        <strong>Plataforma Agroclimática</strong>
      </span>
    </a>
    <nav class="nav">
      <a aria-current="page" href="/">Inicio</a>
      <a href="atlas/">Atlas</a>
      <a href="estaciones/">Estaciones</a>
      <a href="#lluvia">Lluvia</a>
      <a href="#riesgos">Riesgos</a>
      <a href="#boletines">Boletines</a>
      <a href="#fuentes">Fuentes</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <div class="wrap hero-grid">
        <div>
          <span class="eyebrow">Actualización diaria · versión semilla</span>
          <h1>Atlas vivo para decidir mejor en el campo.</h1>
          <p class="lead">Inventario, mapas interactivos, estaciones meteorológicas, riesgos y boletines agroclimáticos para el departamento de Sololá.</p>
          <div class="actions">
            <a class="btn btn-primary" href="atlas/">Abrir atlas</a>
            <a class="btn btn-soft" href="estaciones/">Ver estaciones</a>
            <a class="btn btn-ghost" href="#fuentes">Fuentes y créditos</a>
          </div>
        </div>

        <div class="card">
          <div class="card-body">
            <span class="badge badge-watch">Demo técnico</span>
            <h2 style="margin-top:16px">Panel diario</h2>
            <p>Este primer bloque todavía usa datos semilla. La idea es validar estructura, estilo visual y comportamiento antes de conectar extractores reales.</p>
            <div class="grid kpi-grid" style="margin-top:22px">
              <div>
                <span class="kpi-label">Estaciones</span>
                <span id="station-count" class="kpi-value">--</span>
              </div>
              <div>
                <span class="kpi-label">Fuentes</span>
                <span id="source-count" class="kpi-value">--</span>
              </div>
              <div>
                <span class="kpi-label">Mapas</span>
                <span id="map-count" class="kpi-value">--</span>
              </div>
              <div>
                <span class="kpi-label">Frecuencia</span>
                <span class="kpi-value">24h</span>
              </div>
            </div>
            <div class="credit">
              <span>Datos: instituciones participantes</span>
              <span>Visualización: Mesa Agroclimática de Sololá</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap section-head">
        <div>
          <span class="eyebrow">Mapa principal</span>
          <h2>Estaciones y capas iniciales</h2>
        </div>
        <p>Este bloque simula la interacción: clic en estaciones, panel lateral y lista de capas. Después se reemplaza el mapa falso por MapLibre o Leaflet.</p>
      </div>
      <div class="wrap map-layout">
        <aside class="panel">
          <div class="panel-head"><strong>Capas disponibles</strong></div>
          <div id="layer-list" class="panel-body"></div>
        </aside>
        <section id="station-map" class="map-canvas" aria-label="Mapa semilla de estaciones"></section>
        <aside class="panel">
          <div class="panel-head"><strong>Detalle</strong></div>
          <div id="map-detail" class="panel-body">
            <h3>Seleccione una estación</h3>
            <p>Al hacer clic se mostrará institución, municipio, variables, estado y crédito.</p>
          </div>
        </aside>
      </div>
    </section>

    <section id="lluvia" class="section">
      <div class="wrap section-head">
        <div>
          <span class="eyebrow">Gráficas base</span>
          <h2>Estilo visual para datos de estación</h2>
        </div>
        <p>Esta tarjeta define el lenguaje visual de las gráficas: limpia, institucional, con crédito fijo y pensada para lluvia, temperatura, humedad o viento.</p>
      </div>
      <div class="wrap" id="demo-chart"></div>
    </section>

    <section id="fuentes" class="section">
      <div class="wrap section-head">
        <div>
          <span class="eyebrow">Inventario semilla</span>
          <h2>Fuentes y estaciones</h2>
        </div>
        <p>Base inicial para depurar estaciones, completar coordenadas y definir extractores diarios.</p>
      </div>
      <div class="wrap" id="stations-table"></div>
    </section>

    <p id="app-error" class="wrap" style="color:#a33b35"></p>
  </main>

  <script src="assets/js/app.js"></script>
</body>
</html>
EOF

cat > docs/atlas/index.html <<'EOF'
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Atlas Agroclimático · MTA Sololá</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@600;800&family=Lora:wght@600;700&family=Sora:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../assets/css/mta-theme.css">
</head>
<body>
  <header class="header">
    <a class="brand" href="../">
      <span class="brand-mark">MTA</span>
      <span><small>Sololá</small><strong>Atlas Agroclimático</strong></span>
    </a>
    <nav class="nav">
      <a href="../">Inicio</a>
      <a aria-current="page" href="./">Atlas</a>
      <a href="../estaciones/">Estaciones</a>
    </nav>
  </header>
  <main class="section">
    <div class="wrap section-head">
      <div>
        <span class="eyebrow">Muchos mapas</span>
        <h1 style="max-width:16ch">Atlas Agroclimático</h1>
      </div>
      <p>Próximo paso: reemplazar el mapa semilla por MapLibre/Leaflet y conectar capas de lluvia, temperatura, sequía y riesgos.</p>
    </div>
    <div class="wrap map-layout">
      <aside class="panel"><div class="panel-head"><strong>Capas</strong></div><div id="layer-list" class="panel-body"></div></aside>
      <section id="station-map" class="map-canvas"></section>
      <aside class="panel"><div class="panel-head"><strong>Detalle</strong></div><div id="map-detail" class="panel-body"><h3>Seleccione una capa o estación</h3></div></aside>
    </div>
  </main>
  <script src="../assets/js/app.js"></script>
</body>
</html>
EOF

cat > docs/estaciones/index.html <<'EOF'
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Estaciones Meteorológicas · MTA Sololá</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@600;800&family=Lora:wght@600;700&family=Sora:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../assets/css/mta-theme.css">
</head>
<body>
  <header class="header">
    <a class="brand" href="../">
      <span class="brand-mark">MTA</span>
      <span><small>Sololá</small><strong>Estaciones</strong></span>
    </a>
    <nav class="nav">
      <a href="../">Inicio</a>
      <a href="../atlas/">Atlas</a>
      <a aria-current="page" href="./">Estaciones</a>
    </nav>
  </header>
  <main class="section">
    <div class="wrap section-head">
      <div>
        <span class="eyebrow">Inventario</span>
        <h1 style="max-width:16ch">Red de estaciones meteorológicas</h1>
      </div>
      <p>Listado semilla. Se debe completar con coordenadas, URL exacta de cada estación, estado real, variables y método de extracción.</p>
    </div>
    <div class="wrap" id="stations-table"></div>
  </main>
  <script src="../assets/js/app.js"></script>
</body>
</html>
EOF

cat > scripts/auditar_fuentes.py <<'EOF'
#!/usr/bin/env python3
"""
Auditor puerco v0.1
- Lee docs/data/fuentes_estaciones.json
- Consulta cada URL pública autorizada
- Guarda HTML crudo en archive/raw_pages
- Genera reports/auditoria_fuentes.json

No extrae datos todavía. Primero queremos saber:
- si la fuente responde
- cuánto pesa
- cuándo fue consultada
- si falló
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
FUENTES_FILE = ROOT / "docs" / "data" / "fuentes_estaciones.json"
RAW_DIR = ROOT / "archive" / "raw_pages"
REPORT_FILE = ROOT / "reports" / "auditoria_fuentes.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_get(url: str, timeout: int = 25) -> dict:
    req = Request(url, headers={"User-Agent": "MTA-Solola-Auditor/0.1"})
    try:
      with urlopen(req, timeout=timeout) as response:
          body = response.read()
          return {
              "ok": True,
              "status": getattr(response, "status", None),
              "content_type": response.headers.get("content-type"),
              "bytes": len(body),
              "sha256": hashlib.sha256(body).hexdigest(),
              "body": body.decode("utf-8", errors="replace"),
              "error": None,
          }
    except (HTTPError, URLError, TimeoutError) as exc:
      return {
          "ok": False,
          "status": getattr(exc, "code", None),
          "content_type": None,
          "bytes": 0,
          "sha256": None,
          "body": "",
          "error": str(exc),
      }


def main() -> None:
    data = json.loads(FUENTES_FILE.read_text(encoding="utf-8"))
    timestamp = now_iso()
    report = {"timestamp": timestamp, "fuentes": []}

    for fuente in data.get("fuentes", []):
        url = fuente.get("url_publica")
        if not url:
            continue

        result = safe_get(url)
        raw_name = f"{fuente['id']}_{timestamp[:10]}.html"
        raw_path = RAW_DIR / raw_name
        if result["body"]:
            raw_path.write_text(result["body"], encoding="utf-8")

        report["fuentes"].append({
            "id": fuente["id"],
            "nombre": fuente["nombre"],
            "url": url,
            "ok": result["ok"],
            "status": result["status"],
            "content_type": result["content_type"],
            "bytes": result["bytes"],
            "sha256": result["sha256"],
            "archivo_crudo": str(raw_path.relative_to(ROOT)) if result["body"] else None,
            "error": result["error"],
            "consultado_en": timestamp,
        })

    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK · reporte escrito en {REPORT_FILE}")


if __name__ == "__main__":
    main()
EOF
chmod +x scripts/auditar_fuentes.py

cat > .gitignore <<'EOF'
.DS_Store
__pycache__/
*.pyc
archive/raw_pages/*.html
reports/*.json
EOF

echo ""
echo "✅ Repo semilla creada."
echo ""
echo "Siguiente:"
echo "  python3 -m http.server 8080 -d docs"
echo "  open http://localhost:8080"
echo ""
echo "Auditoría diaria manual:"
echo "  python3 scripts/auditar_fuentes.py"
echo ""
