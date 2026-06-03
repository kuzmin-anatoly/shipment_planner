const vehiclePresets = {
  "40ft": { name: "Контейнер 40 ft", max_length: 12.03, max_width: 2.35, max_height: 2.39, max_volume: 67.7, max_weight: 26500 },
  "20ft": { name: "Контейнер 20 ft", max_length: 5.9, max_width: 2.35, max_height: 2.39, max_volume: 33.1, max_weight: 28200 },
  truck: { name: "Трак", max_length: 13.6, max_width: 2.45, max_height: 2.7, max_volume: 82, max_weight: 20000 },
  "sprinter": { name: "Mercedes Sprinter", max_length: 4.3, max_width: 1.8, max_height: 1.9, max_volume: 14.0, max_weight: 1500 },
  "gazelle": { name: "ГАЗель Next", max_length: 3.2, max_width: 1.9, max_height: 1.9, max_volume: 10.5, max_weight: 1500 },
  "fuso": { name: "Mitsubishi Fuso", max_length: 5.0, max_width: 2.1, max_height: 2.1, max_volume: 22.0, max_weight: 5000 },
  all: { name: "ALL", max_length: 1, max_width: 1, max_height: 1, max_volume: 1, max_weight: 1 },
};

const state = {
  boxes: [],
  boxesSource: null,
  vehicles: [createVehicle("40ft")],
  lastPlanRequest: null,
  lastPlanResult: null,
  activeResultContainer: null,
  selectedExpanded: false,
  excludedExpanded: false,
  selectedSortField: "sort_score",
  selectedSortDirection: "desc",
  excludedSortField: "sort_score",
  excludedSortDirection: "desc",
};

const boxesStatus = document.querySelector("#boxesStatus");
const boxCountBadge = document.querySelector("#boxCountBadge");
const boxesTableBody = document.querySelector("#boxesTableBody");
const boxSummary = document.querySelector("#boxSummary");
const plannerForm = document.querySelector("#plannerForm");
const csvFileInput = document.querySelector("#csvFileInput");
const addContainerButton = document.querySelector("#addContainerButton");
const containerList = document.querySelector("#containerList");
const exportExcelButton = document.querySelector("#exportExcelButton");
const planButton = document.querySelector("#planButton");
const planStatusBadge = document.querySelector("#planStatusBadge");
const planWarnings = document.querySelector("#planWarnings");
const metricsCards = document.querySelector("#metricsCards");
const directionSummary = document.querySelector("#directionSummary");
const containerPlans = document.querySelector("#containerPlans");
const activeContainerBadge = document.querySelector("#activeContainerBadge");
const selectedTable = document.querySelector("#selectedTable");
const selectedTableBody = document.querySelector("#selectedTableBody");
const excludedTable = document.querySelector("#excludedTable");
const excludedTableBody = document.querySelector("#excludedTableBody");
const selectedCountBadge = document.querySelector("#selectedCountBadge");
const excludedCountBadge = document.querySelector("#excludedCountBadge");
const toggleSelectedRows = document.querySelector("#toggleSelectedRows");
const toggleExcludedRows = document.querySelector("#toggleExcludedRows");
const sortByAmount = document.querySelector("#sortByAmount");
const sortByVolume = document.querySelector("#sortByVolume");
const sortByWeight = document.querySelector("#sortByWeight");
const tabs = [...document.querySelectorAll("[data-tab-target]")];
const tabPanels = [...document.querySelectorAll(".tab-panel")];

function createVehicle(presetKey = "40ft") {
  const preset = vehiclePresets[presetKey];
  return {
    presetKey,
    name: preset.name,
    direction: "",
    max_length: preset.max_length,
    max_width: preset.max_width,
    max_height: preset.max_height,
    max_volume: preset.max_volume,
    max_weight: preset.max_weight,
  };
}

function setBadge(node, text, tone) {
  node.textContent = text;
  node.className = `badge ${tone}`;
}

function numberFormat(value, fractionDigits = 2) {
  return new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 0,
    maximumFractionDigits: fractionDigits,
  }).format(value ?? 0);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function availableDirections() {
  return [...new Set(state.boxes.map((box) => (box.direction || "").trim()).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right, "ru"));
}

function renderDirectionOptions(selectedDirection) {
  const directions = [...availableDirections()];
  if (selectedDirection && !directions.includes(selectedDirection)) {
    directions.unshift(selectedDirection);
  }
  const options = [`<option value="" ${!selectedDirection ? "selected" : ""}>Любое</option>`];
  directions.forEach((direction) => {
    options.push(`<option value="${escapeHtml(direction)}" ${selectedDirection === direction ? "selected" : ""}>${escapeHtml(direction)}</option>`);
  });
  return options.join("");
}

function renderPresetOptions(vehicle) {
  const options = [
    ["40ft", "Контейнер 40 ft"],
    ["20ft", "Контейнер 20 ft"],
    ["truck", "Трак"],
    ["sprinter", "Mercedes Sprinter"],
    ["gazelle", "ГАЗель Next"],
    ["fuso", "Mitsubishi Fuso"],
    ["all", "ALL"],
    ["custom", "Свои параметры"],
  ];
  return options
    .map(([value, label]) => `<option value="${value}" ${vehicle.presetKey === value ? "selected" : ""}>${label}</option>`)
    .join("");
}

function assignDefaultVehicleDirections() {
  if (state.vehicles.some((vehicle) => vehicle.presetKey === "all")) return;
  const directions = availableDirections();
  if (!directions.length) return;

  const usedDirections = new Set(
    state.vehicles
      .map((vehicle) => (vehicle.direction || "").trim())
      .filter(Boolean),
  );

  state.vehicles.forEach((vehicle) => {
    if ((vehicle.direction || "").trim()) return;
    const nextDirection = directions.find((direction) => !usedDirections.has(direction)) || directions[0];
    vehicle.direction = nextDirection;
    usedDirections.add(nextDirection);
  });
}

function normalizeVehicleDirections() {
  if (state.vehicles.some((vehicle) => vehicle.presetKey === "all")) return;
  const directions = availableDirections();
  if (!directions.length) return;
  state.vehicles.forEach((vehicle, index) => {
    const current = (vehicle.direction || "").trim();
    if (current) return;
    vehicle.direction = directions[index % directions.length];
  });
}

function activateTab(tabId) {
  tabs.forEach((tab) => {
    const active = tab.dataset.tabTarget === tabId;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  tabPanels.forEach((panel) => {
    panel.classList.toggle("is-active", panel.id === tabId);
  });
}

function sortBoxes(boxes, field, direction) {
  const factor = direction === "asc" ? 1 : -1;
  return [...boxes].sort((left, right) => {
    const a = left[field] ?? "";
    const b = right[field] ?? "";
    if (typeof a === "number" && typeof b === "number") {
      return (a - b) * factor;
    }
    return String(a).localeCompare(String(b), "ru") * factor;
  });
}

function visibleBoxes(boxes, expanded) {
  return expanded ? boxes : boxes.slice(0, 5);
}

function updateExpandButton(button, expanded, total) {
  if (!button) return;
  if (total <= 5) {
    button.hidden = true;
    return;
  }
  button.hidden = false;
  button.textContent = expanded ? "Скрыть ↑" : `Показать все ↓ (${total})`;
}

function renderTableSortState(tableName) {
  const table = tableName === "selected" ? selectedTable : excludedTable;
  if (!table) return;
  const activeField = tableName === "selected" ? state.selectedSortField : state.excludedSortField;
  const activeDirection = tableName === "selected" ? state.selectedSortDirection : state.excludedSortDirection;
  const headers = table.querySelectorAll("[data-table-sort]");
  headers.forEach((header) => {
    const isActive = header.dataset.sortField === activeField;
    header.classList.toggle("is-sorted", isActive);
    const button = header.querySelector(".column-sort");
    if (!button) return;
    button.textContent = isActive ? (activeDirection === "asc" ? "↑" : "↓") : "";
    button.setAttribute("aria-hidden", String(!isActive));
  });
}

function renderTableBody(node, boxes, emptyText, variant = "compact") {
  const columns = { cargo: 10, result: 8, excluded: 5, compact: 5 };
  if (!boxes.length) {
    node.innerHTML = `<tr><td colspan="${columns[variant] || 5}" class="empty">${emptyText}</td></tr>`;
    return;
  }

  if (variant === "cargo") {
    node.innerHTML = boxes.map((box) => `
      <tr>
        <td>${escapeHtml(box.name)}</td>
        <td>${escapeHtml(box.contractor || "")}</td>
        <td>${escapeHtml(box.direction_code || "")}</td>
        <td>${escapeHtml(box.direction)}</td>
        <td>${numberFormat(box.amount)}</td>
        <td>${numberFormat(box.volume, 3)}</td>
        <td>${numberFormat(box.weight, 3)}</td>
        <td>${numberFormat(box.length, 2)}</td>
        <td>${numberFormat(box.width, 2)}</td>
        <td>${numberFormat(box.height, 2)}</td>
      </tr>
    `).join("");
    return;
  }

  if (variant === "result") {
    node.innerHTML = boxes.map((box) => `
      <tr>
        <td>${escapeHtml(box.name)}</td>
        <td>${escapeHtml(box.contractor || "")}</td>
        <td>${escapeHtml(box.direction_code || "")}</td>
        <td>${escapeHtml(box.direction)}</td>
        <td>${numberFormat(box.amount)}</td>
        <td>${numberFormat(box.volume, 3)}</td>
        <td>${numberFormat(box.weight, 3)}</td>
        <td>${numberFormat(box.sort_score, 3)}</td>
      </tr>
    `).join("");
    return;
  }

  if (variant === "excluded") {
    node.innerHTML = boxes.map((box) => `
      <tr>
        <td>${escapeHtml(box.name)}</td>
        <td>${escapeHtml(box.direction)}</td>
        <td>${numberFormat(box.amount)}</td>
        <td>${numberFormat(box.volume, 3)}</td>
        <td>${numberFormat(box.weight, 3)}</td>
      </tr>
    `).join("");
    return;
  }

  node.innerHTML = boxes.map((box) => `
    <tr>
      <td>${escapeHtml(box.name)}</td>
      <td>${escapeHtml(box.direction)}</td>
      <td>${numberFormat(box.amount)}</td>
      <td>${numberFormat(box.volume, 3)}</td>
      <td>${numberFormat(box.weight, 3)}</td>
    </tr>
  `).join("");
}

function renderLoadedBoxes() {
  boxCountBadge.textContent = String(state.boxes.length);
  renderTableBody(boxesTableBody, state.boxes, "Нет загруженных коробок.", "cargo");
  normalizeVehicleDirections();
  assignDefaultVehicleDirections();
  renderVehicleEditors();
  if (!state.boxes.length) {
    boxSummary.textContent = "Нет данных.";
    boxesStatus.textContent = "Коробки еще не загружены.";
    return;
  }
  const directions = state.boxes.reduce((acc, box) => {
    acc[box.direction] = (acc[box.direction] || 0) + 1;
    return acc;
  }, {});
  boxSummary.textContent = `Источник: ${state.boxesSource || "не указан"}. Направления: ${Object.entries(directions).map(([dir, count]) => `${dir}: ${count}`).join(" · ")}`;
  boxesStatus.textContent = `Загружено ${state.boxes.length} коробок. Источник: ${state.boxesSource || "не указан"}.`;
}

function renderVehicleEditors() {
  containerList.innerHTML = state.vehicles.map((vehicle, index) => `
    <article class="container-editor" data-index="${index}">
      <div class="section-head compact-head">
        <h3>Контейнер ${index + 1}</h3>
        <button class="delete-button" type="button" data-action="delete-container" data-index="${index}">Delete</button>
      </div>
      <div class="grid three">
        <label>
          <span>Шаблон</span>
          <select data-field="presetKey" data-index="${index}">
            ${renderPresetOptions(vehicle)}
          </select>
        </label>
        <label>
          <span>Наименование</span>
          <input data-field="name" data-index="${index}" value="${escapeHtml(vehicle.name)}" />
        </label>
        <label>
          <span>Направление</span>
          <select data-field="direction" data-index="${index}">
            ${renderDirectionOptions(vehicle.direction)}
          </select>
        </label>
      </div>
      <div class="grid five">
        <label><span>Макс. длина</span><input data-field="max_length" data-index="${index}" type="number" min="0.01" step="0.01" value="${vehicle.max_length}" /></label>
        <label><span>Макс. ширина</span><input data-field="max_width" data-index="${index}" type="number" min="0.01" step="0.01" value="${vehicle.max_width}" /></label>
        <label><span>Макс. высота</span><input data-field="max_height" data-index="${index}" type="number" min="0.01" step="0.01" value="${vehicle.max_height}" /></label>
        <label><span>Макс. объем</span><input data-field="max_volume" data-index="${index}" type="number" min="0.01" step="0.01" value="${vehicle.max_volume}" /></label>
        <label><span>Макс. вес</span><input data-field="max_weight" data-index="${index}" type="number" min="0.01" step="0.01" value="${vehicle.max_weight}" /></label>
      </div>
    </article>
  `).join("");
}

function renderWarnings(warnings) {
  planWarnings.innerHTML = warnings.length
    ? warnings.map((warning) => `<div class="warning">${escapeHtml(warning)}</div>`).join("")
    : "";
}

function renderMetrics(result) {
  if (!result?.metrics) {
    metricsCards.innerHTML = "";
    directionSummary.textContent = "Результат пока не рассчитан.";
    return;
  }
  const metrics = result.metrics;
  const modeText = result.distribution_mode === "balanced" ? "равномерно" : result.distribution_mode === "all" ? "ALL" : "свободно";
  const cards = [
    { label: "Контейнеров всего", value: result.total_containers },
    { label: "Контейнеров использовано", value: result.used_containers },
    { label: "Режим", value: modeText },
    { label: "Коробок в плане", value: metrics.total_boxes },
    { label: "Стоимость", value: numberFormat(metrics.total_amount) },
    { label: "Объем", value: numberFormat(metrics.total_volume, 3), meta: `${numberFormat(metrics.fill_percent)}%` },
    { label: "Вес", value: numberFormat(metrics.total_weight, 3), meta: `${numberFormat(metrics.weight_percent)}%` },
  ];
  metricsCards.innerHTML = cards.map((card) => `
    <article class="card">
      ${card.meta ? `<em class="card-meta">${escapeHtml(card.meta)}</em>` : ""}
      <span>${escapeHtml(card.label)}</span>
      <strong>${escapeHtml(card.value)}</strong>
    </article>
  `).join("");
  const directionText = Object.entries(result.direction_summary || {}).map(([direction, count]) => `${direction}: ${count}`).join(" · ");
  directionSummary.textContent = directionText
    ? `Сводно по направлениям: ${directionText}. Источник данных: ${result.source}.`
    : `Источник данных: ${result.source}.`;
}

function renderContainerPlans(plans) {
  if (state.lastPlanResult?.distribution_mode === "all") {
    containerPlans.innerHTML = `
      <article class="container-card active-card">
        <div class="section-head">
          <h3>ALL · весь груз списком</h3>
          <span class="badge success">sorted</span>
        </div>
        <p class="muted small">Режим ALL не разбивает груз по контейнерам. Ниже показан единый отсортированный список коробок.</p>
      </article>
    `;
    return;
  }
  containerPlans.innerHTML = plans?.length
    ? plans.map((plan) => `
      <article class="container-card ${state.activeResultContainer === plan.container_no ? "active-card" : ""}" data-container-no="${plan.container_no}">
        <div class="section-head">
          <h3>${escapeHtml(plan.vehicle.name)} · контейнер ${plan.container_no}</h3>
          <span class="badge ${plan.success ? "success" : "warn"}">${plan.success ? "собран" : "частично"}</span>
        </div>
        <p class="muted small">
          Стоимость: ${numberFormat(plan.metrics.total_amount)} ·
          Объем: ${numberFormat(plan.metrics.total_volume, 3)} ·
          Заполнение: ${numberFormat(plan.metrics.fill_percent)}% ·
          Коробок: ${plan.metrics.total_boxes}
        </p>
        <p class="muted small">
          Вес: ${numberFormat(plan.metrics.total_weight, 3)} ·
          От допустимого: ${numberFormat(plan.metrics.weight_percent)}%
        </p>
        ${plan.vehicle.direction ? `<p class="muted small">Направление: ${escapeHtml(plan.vehicle.direction)}</p>` : ""}
      </article>
    `).join("")
    : "";
}

function renderActiveContainerDetails() {
  const result = state.lastPlanResult;
  if (result?.distribution_mode === "all") {
    const sorted = sortBoxes(result.selected_boxes || [], state.selectedSortField, state.selectedSortDirection);
    state.activeResultContainer = null;
    activeContainerBadge.textContent = "ALL";
    renderTableBody(selectedTableBody, visibleBoxes(sorted, state.selectedExpanded), "Груз пока не загружен.", "result");
    updateExpandButton(toggleSelectedRows, state.selectedExpanded, sorted.length);
    renderTableSortState("selected");
    renderContainerPlans([]);
    return;
  }
  if (!result?.container_plans?.length) {
    renderTableBody(selectedTableBody, [], "Выберите контейнер из результата.", "result");
    activeContainerBadge.textContent = "не выбран";
    updateExpandButton(toggleSelectedRows, false, 0);
    renderTableSortState("selected");
    return;
  }
  const active = result.container_plans.find((plan) => plan.container_no === state.activeResultContainer) || result.container_plans[0];
  state.activeResultContainer = active.container_no;
  activeContainerBadge.textContent = `${active.vehicle.name} · ${active.container_no}`;
  const sorted = sortBoxes(active.selected_boxes || [], state.selectedSortField, state.selectedSortDirection);
  renderTableBody(selectedTableBody, visibleBoxes(sorted, state.selectedExpanded), "В контейнер ничего не вошло.", "result");
  updateExpandButton(toggleSelectedRows, state.selectedExpanded, sorted.length);
  renderTableSortState("selected");
  renderContainerPlans(result.container_plans);
}

function renderExcludedDetails() {
  const result = state.lastPlanResult;
  const sorted = sortBoxes(result?.excluded_boxes || [], state.excludedSortField, state.excludedSortDirection);
  renderTableBody(excludedTableBody, visibleBoxes(sorted, state.excludedExpanded), "Исключенных коробок нет.", "excluded");
  updateExpandButton(toggleExcludedRows, state.excludedExpanded, sorted.length);
  renderTableSortState("excluded");
}

function renderPlanResult(result) {
  state.lastPlanResult = result;
  state.activeResultContainer = result.distribution_mode === "all" ? null : result.container_plans?.[0]?.container_no ?? null;
  state.selectedExpanded = false;
  state.excludedExpanded = false;
  state.lastPlanRequest = collectPlanningPayload();
  setBadge(planStatusBadge, result.success ? "успех" : "частично", result.success ? "success" : "warn");
  renderWarnings(result.warnings || []);
  renderMetrics(result);
  renderActiveContainerDetails();
  renderExcludedDetails();
  selectedCountBadge.textContent = String((result.selected_boxes || []).length);
  excludedCountBadge.textContent = String((result.excluded_boxes || []).length);
  activateTab("resultsTab");
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

async function uploadCsvBoxes() {
  const file = csvFileInput.files?.[0];
  if (!file) return;
  boxesStatus.textContent = `Загружаем ${file.name}...`;
  const content = await file.text();
  try {
    const data = await requestJson("/api/shipment-planner/boxes/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, content }),
    });
    state.boxes = data.boxes || [];
    state.boxesSource = `CSV (${data.filename})`;
    renderLoadedBoxes();
    activateTab("cargoTab");
  } catch (error) {
    boxesStatus.textContent = `CSV не загружен: ${error.message}`;
  } finally {
    csvFileInput.value = "";
  }
}

function collectPlanningPayload() {
  assignDefaultVehicleDirections();
  normalizeVehicleDirections();
  const allMode = state.vehicles.some((vehicle) => vehicle.presetKey === "all");
  return {
    vehicles: allMode
      ? [{
          name: "ALL",
          direction: "",
          max_length: 999,
          max_width: 999,
          max_height: 999,
          max_volume: 9999999,
          max_weight: 9999999,
        }]
      : state.vehicles.map((vehicle) => ({
      name: vehicle.name.trim(),
      direction: (vehicle.direction || "").trim(),
      max_length: Number(vehicle.max_length),
      max_width: Number(vehicle.max_width),
      max_height: Number(vehicle.max_height),
      max_volume: Number(vehicle.max_volume),
      max_weight: Number(vehicle.max_weight),
    })),
    min_total_amount: Number(document.querySelector("#minTotalAmount").value),
    min_fill_percent: Number(document.querySelector("#minFillPercent").value),
    distribution_mode: allMode ? "all" : (document.querySelector("#balancedDistribution").checked ? "balanced" : "free"),
    sort_by_amount: sortByAmount.checked,
    sort_by_volume: sortByVolume.checked,
    sort_by_weight: sortByWeight.checked,
    boxes: state.boxes.length ? state.boxes : null,
  };
}

async function runPlanning() {
  if (!state.vehicles.length) {
    renderWarnings(["Добавьте хотя бы один контейнер."]);
    activateTab("containersTab");
    return;
  }
  planButton.disabled = true;
  setBadge(planStatusBadge, "расчет", "accent");
  renderWarnings([]);
  try {
    const payload = collectPlanningPayload();
    const result = await requestJson("/api/shipment-planner/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderPlanResult(result);
  } catch (error) {
    setBadge(planStatusBadge, "ошибка", "danger");
    renderWarnings([`Расчет не выполнен: ${error.message}`]);
  } finally {
    planButton.disabled = false;
  }
}

async function submitPlan(event) {
  event.preventDefault();
  await runPlanning();
}

async function exportExcel() {
  if (!state.lastPlanRequest) {
    renderWarnings(["Сначала выполните расчет, затем выгружайте Excel."]);
    activateTab("resultsTab");
    return;
  }
  exportExcelButton.disabled = true;
  try {
    const response = await fetch("/api/shipment-planner/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.lastPlanRequest),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "shipment-plan.xlsx";
    link.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    renderWarnings([`Экспорт не выполнен: ${error.message}`]);
  } finally {
    exportExcelButton.disabled = false;
  }
}

function addVehicle() {
  state.vehicles.push(createVehicle("40ft"));
  normalizeVehicleDirections();
  assignDefaultVehicleDirections();
  renderVehicleEditors();
}

function updateVehicle(index, field, value) {
  const vehicle = state.vehicles[index];
  if (!vehicle) return;
  if (field === "presetKey") {
    if (value === "custom") {
      vehicle.presetKey = "custom";
      renderVehicleEditors();
      return;
    }
    state.vehicles[index] = {
      presetKey: value,
      ...vehiclePresets[value],
      direction: value === "all" ? "" : (vehicle.direction || ""),
    };
    renderVehicleEditors();
    return;
  }
  vehicle[field] = ["max_length", "max_width", "max_height", "max_volume", "max_weight"].includes(field)
    ? Number(value)
    : value;
}

function removeVehicle(index) {
  state.vehicles = state.vehicles.length === 1
    ? [createVehicle("40ft")]
    : state.vehicles.filter((_, current) => current !== index);
  renderVehicleEditors();
}

function handleColumnSort(tableName, field) {
  if (tableName === "selected") {
    if (state.selectedSortField === field) {
      state.selectedSortDirection = state.selectedSortDirection === "asc" ? "desc" : "asc";
    } else {
      state.selectedSortField = field;
      state.selectedSortDirection = field === "sort_score" ? "desc" : "asc";
    }
    renderActiveContainerDetails();
    return;
  }
  if (state.excludedSortField === field) {
    state.excludedSortDirection = state.excludedSortDirection === "asc" ? "desc" : "asc";
  } else {
    state.excludedSortField = field;
    state.excludedSortDirection = field === "sort_score" ? "desc" : "asc";
  }
  renderExcludedDetails();
}

tabs.forEach((tab) => {
  tab.addEventListener("click", async () => {
    const targetTab = tab.dataset.tabTarget;
    if (targetTab === "resultsTab") {
      await runPlanning();
      return;
    }
    activateTab(targetTab);
  });
});

containerList.addEventListener("input", (event) => {
  const target = event.target;
  if (!target.dataset.field) return;
  updateVehicle(Number(target.dataset.index), target.dataset.field, target.value);
});

containerList.addEventListener("change", (event) => {
  const target = event.target;
  if (!target.dataset.field) return;
  updateVehicle(Number(target.dataset.index), target.dataset.field, target.value);
});

containerList.addEventListener("click", (event) => {
  const target = event.target;
  if (target.dataset.action === "delete-container") removeVehicle(Number(target.dataset.index));
});

containerPlans.addEventListener("click", (event) => {
  const card = event.target.closest("[data-container-no]");
  if (!card) return;
  state.activeResultContainer = Number(card.dataset.containerNo);
  state.selectedExpanded = false;
  renderActiveContainerDetails();
});

document.addEventListener("click", (event) => {
  const header = event.target.closest("[data-table-sort]");
  if (!header) return;
  handleColumnSort(header.dataset.tableSort, header.dataset.sortField);
});

toggleSelectedRows.addEventListener("click", () => {
  state.selectedExpanded = !state.selectedExpanded;
  renderActiveContainerDetails();
});

toggleExcludedRows.addEventListener("click", () => {
  state.excludedExpanded = !state.excludedExpanded;
  renderExcludedDetails();
});

addContainerButton.addEventListener("click", addVehicle);
csvFileInput.addEventListener("change", uploadCsvBoxes);
plannerForm.addEventListener("submit", submitPlan);
exportExcelButton.addEventListener("click", exportExcel);

renderLoadedBoxes();
renderVehicleEditors();
renderTableSortState("selected");
renderTableSortState("excluded");
activateTab("cargoTab");
