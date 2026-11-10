// @ts-check
/** @typedef {import('./types').Snapshot} Snapshot */
/** @typedef {import('./types').Point} Point */
/** @typedef {import('./types').GPU} GPU */
/** @typedef {import('chart.js').Chart<'line', (number|null)[], string>} LineChart */

/** @type {Record<string, [string,string]>} */
const words = {
  workspace: ["مساحة المراقبة", "MONITORING WORKSPACE"],
  overview: ["نظرة عامة", "Overview"],
  gpuDetails: ["بطاقات الرسوم", "GPU details"],
  serverDetails: ["موارد السيرفر", "Server resources"],
  workloads: ["أحمال الذكاء الاصطناعي", "AI workloads"],
  observer: ["صحة المراقبة", "Monitor health"],
  readOnly: ["مراقبة للقراءة فقط", "Read-only monitoring"],
  theme: ["المظهر", "Theme"],
  connecting: ["جارٍ الاتصال", "Connecting"],
  connected: ["متصل", "Connected"],
  disconnected: ["غير متصل · إعادة المحاولة", "Offline · reconnecting"],
  title: [
    "كل موارد السيرفر، في مكان واحد.",
    "Your server. Every resource. One view.",
  ],
  subtitle: [
    "صورة لحظية للعتاد والأحمال، مع تاريخ يساعدك على فهم التغيّرات.",
    "Live hardware and workload telemetry, with history to understand what changed.",
  ],
  lastUpdate: ["آخر قراءة", "LAST SAMPLE"],
  stale: [
    "القراءات متقادمة؛ تحقق من خدمة جمع البيانات.",
    "Telemetry is stale. Check the collection service.",
  ],
  trends: ["اتجاهات الأداء", "Performance trends"],
  period: ["الفترة", "Period"],
  fiveMinutes: ["آخر 5 دقائق", "Last 5 minutes"],
  oneHour: ["آخر ساعة", "Last hour"],
  oneDay: ["آخر 24 ساعة", "Last 24 hours"],
  oneWeek: ["آخر 7 أيام", "Last 7 days"],
  gpu: ["البطاقة", "GPU"],
  gpuLoad: ["استخدام GPU وVRAM", "GPU & VRAM utilization"],
  thermalPower: ["الحرارة والطاقة", "Temperature & power"],
  cpuRam: ["المعالج والذاكرة", "CPU & RAM"],
  network: ["حركة الشبكة", "Network throughput"],
  alerts: ["التنبيهات النشطة", "Active alerts"],
  noAlerts: [
    "لا توجد تنبيهات نشطة في آخر قراءة.",
    "No active alerts in the latest sample.",
  ],
  a40Note: [
    "تستخدم A40 تبريداً سلبياً يعتمد على تدفق هواء السيرفر. غياب قراءة مروحة البطاقة لا يصف مراوح الهيكل.",
    "A40 uses passive cooling and server airflow. An unavailable GPU fan sensor does not describe chassis fans.",
  ],
  cpu: ["المعالج", "CPU"],
  memory: ["RAM وSwap", "RAM & swap"],
  cores: ["استخدام الأنوية", "Per-core usage"],
  storage: ["التخزين", "Storage"],
  diskIo: [
    "عمليات القرص — حسب الجهاز، دون جمع الطبقات المتداخلة",
    "Disk I/O — per device; overlapping layers are not summed",
  ],
  systemInfo: ["معلومات النظام", "System information"],
  workloadNote: [
    "استخدام GPU مؤشر حمل وليس مقياساً منفرداً لجودة الاستدلال. أسماء النماذج لا تُستنتج من أسماء العمليات.",
    "GPU utilization describes load, not inference quality. Model names are not inferred from processes.",
  ],
  gpuProcesses: ["العمليات التي تستخدم GPU", "GPU processes"],
  processNote: [
    "تُحدَّث العمليات كل 5 ثوانٍ افتراضياً. قد يتجاوز CPU للعملية 100% عند استخدام عدة أنوية.",
    "Processes refresh every 5 seconds by default. Process CPU may exceed 100% across multiple cores.",
  ],
  lmNote: [
    "التكامل اختياري. Tokens/s وTTFT ومعدلات الطلبات غير متاحة عبر قائمة النماذج؛ لا نجمع محتوى المحادثات.",
    "Optional integration. Tokens/s, TTFT and request metrics are unavailable from model listings. Conversation content is never collected.",
  ],
  footer: [
    "قيم غير متاحة تظهر N/A · لا يتحكم النظام في العتاد",
    "Unavailable values are N/A · Hardware is never controlled",
  ],
  noGpu: [
    "لا تتوفر بطاقة GPU قابلة للقراءة حالياً. تستمر مراقبة السيرفر.",
    "No readable GPU is currently available. Server monitoring continues.",
  ],
  empty: ["لا توجد بيانات متاحة", "No data available"],
  historyError: [
    "تعذر تحميل التاريخ؛ تستمر القراءات الحية.",
    "History unavailable; live telemetry continues.",
  ],
  historyNote: [
    "دقة العرض بالثواني؛ الفجوات لا تساوي صفراً",
    "Resolution in seconds; gaps are not zeros",
  ],
  temperature: ["حرارة GPU", "GPU temperature"],
  gpuUsage: ["استخدام GPU", "GPU utilization"],
  vram: ["ذاكرة GPU", "VRAM usage"],
  power: ["طاقة GPU", "GPU power"],
  cpuUsage: ["استخدام CPU", "CPU usage"],
  ramUsage: ["استخدام RAM", "RAM usage"],
  diskUsage: ["استخدام القرص", "Disk usage"],
  networkRate: ["نقل الشبكة", "Network throughput"],
  selectedGpu: ["البطاقة المحددة", "Selected GPU"],
  receive: ["استقبال", "Receive"],
  transmit: ["إرسال", "Transmit"],
  warning: ["تحذير", "Warning"],
  critical: ["حرج", "Critical"],
  ok: ["سليم", "Healthy"],
  degraded: ["قراءة جزئية", "Degraded"],
  unavailable: ["غير متاح", "Unavailable"],
  disabled: ["معطل", "Disabled"],
  initializing: ["تهيئة", "Initializing"],
  yes: ["نعم", "Yes"],
  no: ["لا", "No"],
  name: ["الاسم", "Name"],
  device: ["الجهاز", "Device"],
  mountpoint: ["نقطة الربط", "Mount"],
  filesystem: ["نظام الملفات", "Filesystem"],
  total: ["الإجمالي", "Total"],
  used: ["المستخدم", "Used"],
  free: ["المتاح", "Free"],
  percent: ["النسبة", "Usage"],
  status: ["الحالة", "Status"],
  up: ["متصل", "Up"],
  down: ["متوقف", "Down"],
  addresses: ["العناوين", "Addresses"],
  errors: ["الأخطاء", "Errors"],
  drops: ["الحزم المسقطة", "Drops"],
  start: ["وقت البدء", "Started"],
  type: ["النوع", "Type"],
  coverage: ["تغطية العينات", "Sample coverage"],
  active: ["نشاط تقديري", "Estimated active time"],
  idle: ["خمول مقاس", "Observed idle time"],
  processCount: ["عدد العمليات", "Process count"],
  peak: ["الذروة", "Peak"],
  average: ["المتوسط", "Average"],
  growth: ["تغير VRAM", "VRAM change"],
  sensors: ["حالة الحساسات", "Sensor status"],
  allSensors: ["القياسات المطلوبة متاحة", "Requested measurements available"],
  unknown: ["غير معروف", "Unknown"],
  not_supported: ["غير مدعوم", "Not supported"],
  permission_denied: ["صلاحية غير كافية", "Permission denied"],
  cpuHigh: ["استخدام CPU مرتفع", "CPU usage high"],
  ramHigh: ["استخدام RAM مرتفع", "RAM usage high"],
  gpuMissing: ["بيانات GPU غير متاحة", "GPU data unavailable"],
  diskLow: ["مساحة قرص منخفضة", "Disk space low"],
  networkDown: ["واجهة شبكة متوقفة", "Network interface down"],
  gpuHeat: ["حرارة GPU مرتفعة", "GPU temperature high"],
  gpuMemory: ["ضغط ذاكرة GPU", "GPU memory pressure"],
  gpuPower: ["طاقة GPU قرب الحد", "GPU power near limit"],
  gpuBusy: [
    "استخدام GPU مرتفع · مؤشر حمل",
    "GPU utilization high · load indicator",
  ],
  throttling: ["تباطؤ عتادي مستمر", "Sustained hardware throttling"],
  historyMissing: ["التخزين التاريخي غير متاح", "History storage unavailable"],
  eccError: ["أخطاء ECC غير قابلة للتصحيح", "Uncorrected ECC errors"],
  seconds: ["ثانية", "s"],
  unknownService: ["غير معروف خارج systemd", "Unknown outside systemd"],
};
/** @type {Record<string,string>} */
const fieldArabic = {
  driver: "إصدار التعريف",
  cuda_driver_display: "إصدار CUDA Driver",
  pci_bus_id: "عنوان PCI",
  architecture: "المعمارية",
  persistence_mode: "وضع الاستمرارية",
  compute_mode: "وضع الحوسبة",
  performance_state: "حالة الأداء",
  memory_activity_percent: "نشاط ذاكرة GPU",
  memory_used_bytes: "VRAM المستخدمة",
  memory_free_bytes: "VRAM المتاحة",
  memory_total_bytes: "إجمالي VRAM",
  temperature_c: "الحرارة",
  temperature_max_c: "الحد التشغيلي الحراري",
  temperature_slowdown_c: "حد التباطؤ الحراري",
  temperature_shutdown_c: "حد الإيقاف الحراري",
  power_w: "الطاقة",
  power_limit_w: "حد الطاقة",
  sm_clock_mhz: "تردد SM",
  memory_clock_mhz: "تردد الذاكرة",
  graphics_clock_mhz: "تردد الرسوم",
  fan_percent: "مستشعر المروحة",
  ecc_enabled: "ECC مفعّل",
  ecc_corrected: "ECC مصحح · منذ تهيئة التعريف",
  ecc_uncorrected: "ECC غير مصحح · منذ تهيئة التعريف",
  pcie_generation: "جيل PCIe الحالي",
  pcie_width: "عرض PCIe الحالي",
  pcie_max_generation: "أقصى جيل PCIe",
  pcie_max_width: "أقصى عرض PCIe",
  throttle_reasons: "أسباب خفض التردد",
  physical_cores: "الأنوية الفعلية",
  logical_cores: "الأنوية المنطقية",
  frequency_mhz: "تردد CPU",
  load_average: "متوسط الحمل 1 / 5 / 15 دقيقة",
  total_bytes: "الذاكرة الإجمالية",
  used_bytes: "الذاكرة المستخدمة",
  available_bytes: "الذاكرة المتاحة",
  swap_total_bytes: "إجمالي Swap",
  swap_used_bytes: "Swap المستخدم",
  swap_percent: "استخدام Swap",
  hostname: "اسم السيرفر",
  os: "نظام التشغيل",
  kernel: "النواة",
  python: "إصدار Python",
  boot_time: "وقت الإقلاع",
  uptime_seconds: "مدة التشغيل بالثواني",
  service_status: "حالة خدمة systemd",
  cpu_percent: "CPU للمراقب",
  rss_bytes: "RAM للمراقب",
  collection_latency_ms: "زمن الجمع",
  active_connections: "الاتصالات النشطة",
  dropped_samples: "دورات فائتة",
  replaced_messages: "رسائل استُبدلت للعملاء البطيئين",
  collection_errors: "دورات بأخطاء",
  collection_count: "عدد الدورات",
  collection_error_rate: "نسبة دورات الخطأ",
  api_response_ms: "آخر زمن API · داخلي",
  websocket_send_ms: "آخر زمن إرسال WebSocket · داخلي",
  database_write_bytes: "كتابة SQLite التراكمية",
  database_write_operations: "معاملات SQLite",
};
let language = localStorage.getItem("monitor-language") === "en" ? "en" : "ar";
/** @type {Snapshot|null} */ let latest = null;
/** @type {Point[]} */ let points = [];
/** @type {Map<string,LineChart>} */ const charts = new Map();
/** @type {Map<string,{root:HTMLElement,details:HTMLElement,sensors:HTMLElement}>} */ const gpuViews =
  new Map();
let socket = /** @type {WebSocket|null} */ (null);
let reconnectDelay = 1000;
let receivedAt = 0;
let lastSequence = -1;
let historyRequest = 0;
let historyResolution = 1;

/** @param {string} key */ function tr(key) {
  const pair = words[key];
  return pair
    ? pair[language === "ar" ? 0 : 1]
    : language === "ar"
      ? fieldArabic[key] || key
      : key.replaceAll("_", " ");
}
/** @param {string} id */ function el(id) {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing element ${id}`);
  return node;
}
/** @param {string} id */ function select(id) {
  const node = el(id);
  if (!(node instanceof HTMLSelectElement)) throw new Error("Expected select");
  return node;
}
/** @param {string} tag @param {string} [className] @param {string} [text] */ function node(
  tag,
  className = "",
  text = "",
) {
  const n = document.createElement(tag);
  n.className = className;
  n.textContent = text;
  return n;
}
/** @param {unknown} value @param {string} [unit] @returns {string} */ function display(
  value,
  unit = "",
) {
  if (value === null || value === undefined) return "N/A";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) return "N/A";
    if (unit === "bytes" || unit === "rate") {
      let v = value;
      const units = ["B", "KiB", "MiB", "GiB", "TiB"];
      let i = 0;
      while (Math.abs(v) >= 1024 && i < 4) {
        v /= 1024;
        i++;
      }
      return `${v.toLocaleString("en-US", { maximumFractionDigits: 1 })} ${units[i]}${unit === "rate" ? "/s" : ""}`;
    }
    if (unit === "time") return new Date(value * 1000).toLocaleString(language);
    return `${value.toLocaleString("en-US", { maximumFractionDigits: 1 })}${unit ? " " + unit : ""}`;
  }
  if (typeof value === "boolean") return tr(value ? "yes" : "no");
  if (Array.isArray(value))
    return value.length ? value.map((v) => display(v)).join(" / ") : "—";
  return String(value);
}
/** @param {HTMLElement} target @param {unknown} state */
function changed(target, state) {
  const signature = JSON.stringify([language, state]);
  if (target.dataset.signature === signature) return false;
  target.dataset.signature = signature;
  return true;
}
/** @param {HTMLElement} target @param {import('./types').Status} source */ function badge(
  target,
  source,
) {
  target.textContent = tr(source.status);
  target.className = `badge ${source.status === "unavailable" ? "critical" : ["degraded", "initializing"].includes(source.status) ? "warning" : ""}`;
  target.title = [
    source.error,
    source.timestamp ? display(source.timestamp, "time") : "",
  ]
    .filter(Boolean)
    .join(" · ");
}
/** @param {HTMLElement} target @param {object} data @param {[string,string][]} fields */ function pairs(
  target,
  data,
  fields,
) {
  if (target.childElementCount !== fields.length) {
    target.replaceChildren(
      ...fields.map(() => {
        const dl = node("dl", "pair");
        dl.append(node("dt"), node("dd"));
        return dl;
      }),
    );
  }
  fields.forEach(([key, unit], i) => {
    const pair = target.children[i];
    const value = Reflect.get(data, key);
    if (pair.firstElementChild) pair.firstElementChild.textContent = tr(key);
    const dd = pair.lastElementChild;
    if (dd) {
      dd.textContent = display(value, unit);
      dd.className = value == null ? "missing" : "";
    }
  });
}
/** @param {string} head @param {string} body @param {string[]} headers @param {unknown[][]} rows */ function table(
  head,
  body,
  headers,
  rows,
) {
  const h = el(head);
  if (h.childElementCount !== 1 || h.textContent !== headers.map(tr).join("")) {
    const row = node("tr");
    row.append(...headers.map((x) => node("th", "", tr(x))));
    h.replaceChildren(row);
  }
  const target = el(body);
  if (!rows.length) {
    if (!changed(target, "empty")) return;
    target.replaceChildren();
    const cell = node("td", "empty", tr("empty"));
    cell.setAttribute("colspan", String(headers.length));
    const row = node("tr");
    row.append(cell);
    target.append(row);
    return;
  }
  if (
    target.childElementCount !== rows.length ||
    target.querySelector("[colspan]")
  )
    target.replaceChildren(
      ...rows.map(() => {
        const row = node("tr");
        row.append(...headers.map(() => node("td")));
        return row;
      }),
    );
  delete target.dataset.signature;
  rows.forEach((row, i) =>
    row.forEach((value, j) => {
      const cell = target.children[i]?.children[j];
      if (cell) {
        cell.textContent = display(value);
        cell.setAttribute("title", display(value));
      }
    }),
  );
}
/** @param {string} id @returns {LineChart} */ function makeChart(id) {
  const canvas = el(id);
  if (!(canvas instanceof HTMLCanvasElement)) throw new Error("Missing chart");
  /** @type {import('chart.js').ChartConfiguration<'line',(number|null)[],string>} */
  const config = {
    type: "line",
    data: { labels: [], datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      normalized: true,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: {
          labels: { color: "#91a3bb", boxWidth: 10, font: { size: 10 } },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxTicksLimit: 6, color: "#91a3bb", font: { size: 9 } },
        },
        y: {
          beginAtZero: true,
          grid: { color: "#24324855" },
          ticks: { color: "#91a3bb", font: { size: 9 } },
        },
      },
    },
  };
  const chart = new Chart(canvas, config);
  charts.set(id, chart);
  return chart;
}
/** @param {string} id @param {{label:string,key:string,color:string,axis?:string}[]} series */ function plot(
  id,
  series,
) {
  if (typeof Chart === "undefined") return;
  const chart = charts.get(id) || makeChart(id);
  chart.data.labels = points.map((p) =>
    new Date(p.timestamp * 1000).toLocaleTimeString(language, {
      hour: "2-digit",
      minute: "2-digit",
    }),
  );
  chart.data.datasets = series.map((s) => ({
    label: s.label,
    data: points.map((p) => p.metrics[s.key]?.mean ?? null),
    borderColor: s.color,
    backgroundColor: s.color + "15",
    borderWidth: 1.8,
    pointRadius: 0,
    tension: 0.2,
    fill: false,
    spanGaps: false,
    yAxisID: s.axis || "y",
  }));
  if (chart.options.scales) {
    chart.options.scales.y1 = series.some((s) => s.axis === "y1")
      ? {
          position: "right",
          grid: { drawOnChartArea: false },
          ticks: { color: "#91a3bb" },
        }
      : { display: false };
  }
  chart.update("none");
}
function selectedGPU() {
  return (
    latest?.gpu.devices.find((g) => g.uuid === select("gpu-select").value) ||
    latest?.gpu.devices[0]
  );
}
/** @param {(number|null|undefined)[]} values */ function sum(values) {
  const valid = /** @type {number[]} */ (
    values.filter((v) => typeof v === "number" && Number.isFinite(v))
  );
  return valid.length ? valid.reduce((a, b) => a + b, 0) : null;
}
/** @param {Snapshot} snapshot */ function livePoint(snapshot) {
  /** @type {Record<string,import('./types').Aggregate>} */ const metrics = {};
  /** @param {string} key @param {number|null} value */ const add = (
    key,
    value,
  ) => {
    if (value !== null && Number.isFinite(value))
      metrics[key] = { mean: value, minimum: value, maximum: value, count: 1 };
  };
  add("cpu/usage_percent", snapshot.system.cpu.usage_percent);
  add("ram/percent", snapshot.system.memory.percent);
  for (const gpu of snapshot.gpu.devices) {
    add(`gpu/${gpu.uuid}/gpu_util_percent`, gpu.gpu_util_percent);
    add(`gpu/${gpu.uuid}/vram_percent`, gpu.vram_percent);
    add(`gpu/${gpu.uuid}/temperature_c`, gpu.temperature_c);
    add(`gpu/${gpu.uuid}/power_w`, gpu.power_w);
  }
  for (const n of snapshot.system.network) {
    add(
      `network/${n.name}/receive_bytes_per_second`,
      n.receive_bytes_per_second,
    );
    add(
      `network/${n.name}/transmit_bytes_per_second`,
      n.transmit_bytes_per_second,
    );
  }
  return { timestamp: snapshot.timestamp, metrics };
}
function renderCharts() {
  const gpu = selectedGPU();
  const prefix = `gpu/${gpu?.uuid}/`;
  plot("chart-gpu", [
    { label: "GPU %", key: prefix + "gpu_util_percent", color: "#5ce6c5" },
    { label: "VRAM %", key: prefix + "vram_percent", color: "#79b7ff" },
  ]);
  plot("chart-thermal", [
    { label: "°C", key: prefix + "temperature_c", color: "#ffd08b" },
    { label: "W", key: prefix + "power_w", color: "#b09bff", axis: "y1" },
  ]);
  plot("chart-system", [
    { label: "CPU %", key: "cpu/usage_percent", color: "#79b7ff" },
    { label: "RAM %", key: "ram/percent", color: "#5ce6c5" },
  ]);
  const network = latest?.system.network || [];
  plot(
    "chart-network",
    network.flatMap((n, i) => [
      {
        label: `${n.name} ↓ B/s`,
        key: `network/${n.name}/receive_bytes_per_second`,
        color: i % 2 ? "#b09bff" : "#5ce6c5",
      },
      {
        label: `${n.name} ↑ B/s`,
        key: `network/${n.name}/transmit_bytes_per_second`,
        color: i % 2 ? "#ffd08b" : "#79b7ff",
      },
    ]),
  );
  for (const g of latest?.gpu.devices || [])
    plot(`gpu-chart-${g.uuid}`, [
      {
        label: "GPU %",
        key: `gpu/${g.uuid}/gpu_util_percent`,
        color: "#5ce6c5",
      },
      { label: "VRAM %", key: `gpu/${g.uuid}/vram_percent`, color: "#79b7ff" },
    ]);
}
/** @type {{root:HTMLElement,label:HTMLElement,value:HTMLElement,note:HTMLElement,fill:HTMLElement}[]} */ const summary =
  [];
for (let i = 0; i < 8; i++) {
  const root = node("article", "card");
  const top = node("div", "card-top");
  const label = node("span");
  top.append(
    label,
    node("span", "card-icon", ["◉", "◈", "▥", "ϟ", "▦", "▤", "◴", "↕"][i]),
  );
  const value = node("div", "card-value", "N/A");
  const note = node("div", "card-note");
  const meter = node("div", "meter");
  const fill = node("div", "meter-fill");
  meter.append(fill);
  root.append(top, value, note, meter);
  el("summary").append(root);
  summary.push({ root, label, value, note, fill });
}
/** @param {Snapshot} s */ function renderSummary(s) {
  const gpu = selectedGPU();
  const disk =
    s.system.disks.find((d) => d.mountpoint === "/") || s.system.disks[0];
  const network = sum(
    s.system.network.flatMap((n) => [
      n.receive_bytes_per_second,
      n.transmit_bytes_per_second,
    ]),
  );
  const metrics = [
    {
      key: "temperature",
      value: gpu?.temperature_c,
      unit: "°C",
      pct: null,
      note: gpu?.name,
    },
    {
      key: "gpuUsage",
      value: gpu?.gpu_util_percent,
      unit: "%",
      pct: gpu?.gpu_util_percent,
      note: tr("selectedGpu"),
    },
    {
      key: "vram",
      value: gpu?.vram_percent,
      unit: "%",
      pct: gpu?.vram_percent,
      note: `${display(gpu?.memory_used_bytes, "bytes")} / ${display(gpu?.memory_total_bytes, "bytes")}`,
    },
    {
      key: "power",
      value: gpu?.power_w,
      unit: "W",
      pct: null,
      note: `${tr("power_limit_w")}: ${display(gpu?.power_limit_w, "W")}`,
    },
    {
      key: "cpuUsage",
      value: s.system.cpu.usage_percent,
      unit: "%",
      pct: s.system.cpu.usage_percent,
      note: tr("cpu"),
    },
    {
      key: "ramUsage",
      value: s.system.memory.percent,
      unit: "%",
      pct: s.system.memory.percent,
      note: "RAM",
    },
    {
      key: "diskUsage",
      value: disk?.percent,
      unit: "%",
      pct: disk?.percent,
      note: disk?.mountpoint,
    },
    {
      key: "networkRate",
      value: network,
      unit: "rate",
      pct: null,
      note: tr("receive") + " + " + tr("transmit"),
    },
  ];
  metrics.forEach((m, i) => {
    const view = summary[i];
    view.label.textContent = tr(m.key);
    view.value.textContent = display(m.value, m.unit);
    view.note.textContent = m.note || "N/A";
    view.fill.style.width =
      m.pct == null ? "0%" : `${Math.min(100, Math.max(0, m.pct))}%`;
    view.fill.className = "meter-fill";
    view.fill.parentElement?.setAttribute("aria-hidden", "true");
  });
}
/** @type {[string,string][]} */ const gpuFields = [
  ["driver", ""],
  ["cuda_driver_display", ""],
  ["pci_bus_id", ""],
  ["architecture", ""],
  ["persistence_mode", ""],
  ["compute_mode", ""],
  ["performance_state", ""],
  ["memory_activity_percent", "%"],
  ["memory_used_bytes", "bytes"],
  ["memory_free_bytes", "bytes"],
  ["memory_total_bytes", "bytes"],
  ["temperature_c", "°C"],
  ["temperature_max_c", "°C"],
  ["temperature_slowdown_c", "°C"],
  ["temperature_shutdown_c", "°C"],
  ["power_w", "W"],
  ["power_limit_w", "W"],
  ["sm_clock_mhz", "MHz"],
  ["memory_clock_mhz", "MHz"],
  ["graphics_clock_mhz", "MHz"],
  ["fan_percent", "%"],
  ["ecc_enabled", ""],
  ["ecc_corrected", ""],
  ["ecc_uncorrected", ""],
  ["pcie_generation", ""],
  ["pcie_width", ""],
  ["pcie_max_generation", ""],
  ["pcie_max_width", ""],
  ["throttle_reasons", ""],
];
/** @param {Snapshot} s */ function renderGPUs(s) {
  const target = el("gpus");
  if (!s.gpu.devices.length) {
    for (const [uuid, view] of gpuViews) {
      charts.get(`gpu-chart-${uuid}`)?.destroy();
      charts.delete(`gpu-chart-${uuid}`);
      view.root.remove();
    }
    gpuViews.clear();
    if (changed(target, "empty"))
      target.replaceChildren(node("div", "panel empty", tr("noGpu")));
    return;
  }
  if (!gpuViews.size) {
    target.replaceChildren();
    delete target.dataset.signature;
  }
  for (const [uuid, view] of gpuViews) {
    if (!s.gpu.devices.some((g) => g.uuid === uuid)) {
      view.root.remove();
      gpuViews.delete(uuid);
      charts.get(`gpu-chart-${uuid}`)?.destroy();
      charts.delete(`gpu-chart-${uuid}`);
    }
  }
  for (const g of s.gpu.devices) {
    let view = gpuViews.get(g.uuid);
    if (!view) {
      const root = node("article", "panel");
      const heading = node("div", "panel-heading");
      const identity = node("div");
      identity.append(
        node("h3", "gpu-title", g.name || `GPU ${g.index}`),
        node("div", "gpu-uuid", g.uuid),
      );
      const status = node("span", "badge", g.status);
      heading.append(identity, status);
      const body = node("div", "gpu-details");
      const details = node("div", "details");
      const right = node("div");
      const sensors = node("div", "muted");
      const chartBox = node("div", "chart small");
      const canvas = document.createElement("canvas");
      canvas.id = `gpu-chart-${g.uuid}`;
      canvas.setAttribute("role", "img");
      canvas.setAttribute("aria-label", `GPU ${g.index} utilization`);
      chartBox.append(canvas);
      right.append(node("h4", "", tr("sensors")), sensors, chartBox);
      body.append(details, right);
      root.append(heading, body);
      target.append(root);
      view = { root, details, sensors };
      gpuViews.set(g.uuid, view);
    }
    const title = view.root.querySelector(".gpu-title");
    if (title) title.textContent = g.name || `GPU ${g.index}`;
    const status = view.root.querySelector(".badge");
    if (status instanceof HTMLElement)
      badge(status, {
        status: g.status,
        error: null,
        timestamp: s.timestamp,
        last_success: null,
      });
    pairs(view.details, g, gpuFields);
    if (changed(view.sensors, g.errors))
      view.sensors.replaceChildren(
        ...Object.entries(g.errors).map(([key, reason]) =>
          node("div", "", `${tr(key)}: ${tr(reason)}`),
        ),
      );
    if (!Object.keys(g.errors).length)
      view.sensors.textContent = tr("allSensors");
  }
}
/** @param {Snapshot} s */ function render(s) {
  const selected = select("gpu-select").value;
  const options = s.gpu.devices.map((g) => g.uuid);
  if (
    [...select("gpu-select").options].map((o) => o.value).join("|") !==
    options.join("|")
  ) {
    select("gpu-select").replaceChildren(
      ...s.gpu.devices.map((g) => {
        const option = document.createElement("option");
        option.value = g.uuid;
        option.textContent = `${g.index} · ${g.name || g.uuid}`;
        return option;
      }),
    );
    if (options.includes(selected)) select("gpu-select").value = selected;
  }
  el("hostname").textContent = s.system.info.hostname;
  el("updated").textContent = new Date(s.timestamp * 1000).toLocaleTimeString(
    language,
  );
  badge(el("gpu-status"), s.gpu.source);
  badge(el("system-status"), s.system.source);
  badge(el("process-status"), s.gpu.processes_source);
  badge(el("storage-status"), s.storage);
  badge(el("lm-status"), s.integration.source);
  renderSummary(s);
  renderGPUs(s);
  pairs(el("cpu-details"), s.system.cpu, [
    ["physical_cores", ""],
    ["logical_cores", ""],
    ["frequency_mhz", "MHz"],
    ["load_average", ""],
    ["temperature_c", "°C"],
  ]);
  pairs(el("ram-details"), s.system.memory, [
    ["total_bytes", "bytes"],
    ["used_bytes", "bytes"],
    ["available_bytes", "bytes"],
    ["swap_total_bytes", "bytes"],
    ["swap_used_bytes", "bytes"],
    ["swap_percent", "%"],
  ]);
  pairs(el("system-info"), s.system.info, [
    ["hostname", ""],
    ["os", ""],
    ["kernel", ""],
    ["python", ""],
    ["boot_time", "time"],
    ["uptime_seconds", "s"],
    ["service_status", ""],
  ]);
  const cores = el("cores");
  if (cores.childElementCount !== s.system.cpu.per_core_percent.length)
    cores.replaceChildren(
      ...s.system.cpu.per_core_percent.map(() => node("div", "core")),
    );
  s.system.cpu.per_core_percent.forEach((v, i) => {
    cores.children[i].textContent = `CPU ${i} · ${display(v, "%")}`;
  });
  table(
    "disk-head",
    "disks",
    ["device", "mountpoint", "filesystem", "total", "used", "free", "percent"],
    s.system.disks.map((d) => [
      d.device,
      d.mountpoint,
      d.filesystem,
      display(d.total_bytes, "bytes"),
      display(d.used_bytes, "bytes"),
      display(d.free_bytes, "bytes"),
      display(d.percent, "%"),
    ]),
  );
  table(
    "io-head",
    "disk-io",
    [
      "device",
      "receive",
      "transmit",
      "Read IOPS",
      "Write IOPS",
      "Read operations",
      "Write operations",
    ],
    s.system.disk_io.map((d) => [
      d.device,
      display(d.read_bytes_per_second, "rate"),
      display(d.write_bytes_per_second, "rate"),
      display(d.read_iops),
      display(d.write_iops),
      d.read_operations,
      d.write_operations,
    ]),
  );
  table(
    "network-head",
    "networks",
    [
      "name",
      "addresses",
      "status",
      "receive",
      "transmit",
      "Total RX",
      "Total TX",
      "errors",
      "drops",
    ],
    s.system.network.map((n) => [
      n.name,
      n.addresses.join(" / "),
      n.is_up === null ? "N/A" : tr(n.is_up ? "up" : "down"),
      display(n.receive_bytes_per_second, "rate"),
      display(n.transmit_bytes_per_second, "rate"),
      display(n.received_bytes, "bytes"),
      display(n.sent_bytes, "bytes"),
      `${display(n.errors_in)} / ${display(n.errors_out)}`,
      `${display(n.drops_in)} / ${display(n.drops_out)}`,
    ]),
  );
  table(
    "process-head",
    "processes",
    ["PID", "gpu", "name", "type", "VRAM", "RAM", "CPU %", "GPU %", "start"],
    s.gpu.processes.map((p) => [
      p.pid,
      p.gpu_uuid,
      p.name,
      p.process_type,
      display(p.gpu_memory_bytes, "bytes"),
      display(p.ram_bytes, "bytes"),
      display(p.cpu_percent, "%"),
      display(p.gpu_util_percent, "%"),
      display(p.start_time, "time"),
    ]),
  );
  el("alert-count").textContent = String(s.alerts.length);
  if (
    changed(
      el("alerts"),
      s.alerts.map((a) => [a.id, a.severity, a.since]),
    )
  )
    el("alerts").replaceChildren(
      ...(s.alerts.length
        ? s.alerts.map((a) => {
            const row = node("div", "alert-row");
            const content = node("div");
            const key =
              a.id === "collector/stopped"
                ? "stale"
                : a.id === "gpu/unavailable" ||
                    (a.id.endsWith("/unavailable") && a.id.startsWith("gpu/"))
                  ? "gpuMissing"
                  : a.id.startsWith("cpu/")
                    ? "cpuHigh"
                    : a.id.startsWith("ram/")
                      ? "ramHigh"
                      : a.id.startsWith("disk/")
                        ? "diskLow"
                        : a.id.startsWith("network/")
                          ? "networkDown"
                          : a.id.endsWith("/temperature")
                            ? "gpuHeat"
                            : a.id.endsWith("/vram")
                              ? "gpuMemory"
                              : a.id.endsWith("/power")
                                ? "gpuPower"
                                : a.id.endsWith("/utilization")
                                  ? "gpuBusy"
                                  : a.id.endsWith("/throttling")
                                    ? "throttling"
                                    : a.id.endsWith("/ecc")
                                      ? "eccError"
                                      : "historyMissing";
            content.append(
              node("span", `badge ${a.severity}`, tr(a.severity)),
              document.createTextNode(" " + tr(key)),
            );
            content.title = a.id;
            row.append(content, node("time", "", display(a.since, "time")));
            return row;
          })
        : [node("div", "muted", tr("noAlerts"))]),
    );
  const activity = el("activity");
  if (activity.childElementCount !== s.activity.length)
    activity.replaceChildren(
      ...s.activity.map(() => {
        const card = node("article", "card");
        card.append(
          node("div", "card-top"),
          node("div", "card-value"),
          node("div", "card-note"),
        );
        return card;
      }),
    );
  s.activity.forEach((a, i) => {
    const card = activity.children[i];
    card.children[0].textContent = a.gpu_uuid;
    card.children[1].textContent = `${display(a.average_util_percent, "%")} · ${tr("average")}`;
    card.children[2].textContent = `${tr("peak")}: ${display(a.peak_util_percent, "%")} · ${tr("processCount")}: ${a.process_count}\n${tr("active")}: ${display(a.active_seconds, "s")} · ${tr("idle")}: ${display(a.idle_seconds, "s")}\n${tr("coverage")}: ${display(a.coverage_percent, "%")} · ${tr("growth")}: ${display(a.vram_change_bytes, "bytes")}\n${tr("power")}: ${display(a.average_power_w, "W")} · ${tr("temperature")}: ${display(a.peak_temperature_c, "°C")}\n${a.patterns.map(tr).join(" · ")}`;
  });
  if (changed(el("lm-models"), s.integration.loaded_models))
    el("lm-models").replaceChildren(
      ...(s.integration.loaded_models.length
        ? s.integration.loaded_models.map((m) => node("span", "", m))
        : [node("span", "muted", tr("empty"))]),
    );
  const observerFields = Object.keys(s.observer).map(
    (k) =>
      /** @type {[string,string]} */ ([
        k,
        k.endsWith("_bytes")
          ? "bytes"
          : k.endsWith("_ms")
            ? "ms"
            : k === "cpu_percent"
              ? "%"
              : "",
      ]),
  );
  pairs(el("observer-details"), s.observer, observerFields);
  renderCharts();
}
function translate() {
  document.documentElement.lang = language;
  document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((n) => {
    n.textContent = tr(n.getAttribute("data-i18n") || "");
  });
  el("language").textContent = language === "ar" ? "English" : "العربية";
  if (latest) render(latest);
  connection();
}
function connection() {
  const connected = socket?.readyState === WebSocket.OPEN;
  el("connection").textContent = tr(
    connected
      ? "connected"
      : socket?.readyState === WebSocket.CONNECTING
        ? "connecting"
        : "disconnected",
  );
  el("connection").className = `badge ${connected ? "" : "warning"}`;
}
function freshness() {
  if (!latest) return;
  const stale =
    Date.now() - receivedAt > latest.stale_after_seconds * 1000 ||
    Date.now() / 1000 - latest.timestamp > latest.stale_after_seconds ||
    latest.collector.status === "unavailable";
  el("stale").hidden = !stale;
  el("freshness").textContent =
    `${Math.max(0, Math.round(Date.now() / 1000 - latest.timestamp))} ${tr("seconds")}`;
}
/** @param {unknown} value @returns {value is Snapshot} */ function isSnapshot(
  value,
) {
  return (
    typeof value === "object" &&
    value !== null &&
    "timestamp" in value &&
    typeof value.timestamp === "number" &&
    Number.isFinite(value.timestamp) &&
    "gpu" in value &&
    "system" in value &&
    "sequence" in value
  );
}
function connect() {
  socket = new WebSocket(
    `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws/metrics`,
  );
  connection();
  socket.onopen = () => {
    reconnectDelay = 1000;
    connection();
  };
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (!isSnapshot(data)) return;
      latest = data;
      receivedAt = Date.now();
      if (select("window").value === "5m" && data.sequence !== lastSequence) {
        const point = livePoint(data);
        const previous = points[points.length - 1];
        if (previous && point.timestamp - previous.timestamp > 2) {
          points.push({ timestamp: previous.timestamp + 1, metrics: {} });
        }
        points.push(point);
        points = points
          .filter((p) => p.timestamp >= data.timestamp - 300)
          .slice(-600);
      }
      lastSequence = data.sequence;
      render(data);
      freshness();
    } catch {
      el("connection").textContent = tr("unavailable");
    }
  };
  socket.onerror = () => socket?.close();
  socket.onclose = () => {
    connection();
    setTimeout(connect, reconnectDelay + Math.random() * 300);
    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
  };
}
async function loadHistory() {
  const request = ++historyRequest;
  try {
    const response = await fetch(
      `/api/history?window=${encodeURIComponent(select("window").value)}&max_points=600`,
      { cache: "no-store" },
    );
    if (!response.ok) throw new Error("history");
    /** @type {import('./types').History} */ const data = await response.json();
    if (request !== historyRequest) return;
    historyResolution = data.resolution_seconds;
    points = data.points;
    if (
      select("window").value === "5m" &&
      latest &&
      (!points.length || points[points.length - 1].timestamp < latest.timestamp)
    )
      points.push(livePoint(latest));
    /** @type {Point[]} */ const expanded = [];
    for (const point of points) {
      /** @type {Point|undefined} */ const last = expanded[expanded.length - 1];
      if (last && point.timestamp - last.timestamp > historyResolution * 1.5)
        expanded.push({
          timestamp: last.timestamp + historyResolution,
          metrics: {},
        });
      expanded.push(point);
    }
    points = expanded;
    el("history-status").textContent =
      `${historyResolution} s · ${tr("historyNote")}${data.source.status !== "ok" ? " · " + tr(data.source.status) : ""}`;
    renderCharts();
  } catch {
    el("history-status").textContent = tr("historyError");
  }
}
select("window").addEventListener("change", () => {
  points = [];
  void loadHistory();
});
select("gpu-select").addEventListener("change", () => {
  if (latest) render(latest);
});
el("language").addEventListener("click", () => {
  language = language === "ar" ? "en" : "ar";
  localStorage.setItem("monitor-language", language);
  translate();
  void loadHistory();
});
el("theme").addEventListener("click", () => {
  document.body.classList.toggle("light");
  localStorage.setItem(
    "monitor-theme",
    document.body.classList.contains("light") ? "light" : "dark",
  );
});
document.body.classList.toggle(
  "light",
  localStorage.getItem("monitor-theme") === "light",
);
translate();
connect();
void loadHistory();
setInterval(freshness, 1000);
setInterval(() => void loadHistory(), 60000);
