/* ==========================================================================
   AI-POWERED TRAFFIC VIOLATION DETECTION SYSTEM - CORE CONTROLLER (app.js)
   ========================================================================== */

// --- Global State ---
let charts = {};
const mockLprData = [
  { id: "TR-2026-001", plate: "MH12-LK-9021", type: "Motorcycle", violation: "Helmet Violation", time: "2026-06-18 23:10:15", conf: "95.8%" },
  { id: "TR-2026-002", plate: "DL3C-AA-0922", type: "Truck", violation: "Red Light Violation", time: "2026-06-18 23:08:44", conf: "97.2%" },
  { id: "TR-2026-003", plate: "KA03-MD-4392", type: "Car", violation: "Wrong Side Driving", time: "2026-06-18 23:00:10", conf: "99.1%" },
  { id: "TR-2026-004", plate: "MH14-GH-1221", type: "Car", violation: "None", time: "2026-06-18 22:45:30", conf: "98.9%" },
  { id: "TR-2026-005", plate: "HR26-CU-8091", type: "Bus", violation: "Stop Line Violation", time: "2026-06-18 22:30:12", conf: "94.5%" },
  { id: "TR-2026-006", plate: "UP16-TR-7822", type: "Motorcycle", violation: "Triple Riding", time: "2026-06-18 22:15:05", conf: "93.1%" },
  { id: "TR-2026-007", plate: "MH02-EX-4455", type: "Car", violation: "Seatbelt Violation", time: "2026-06-18 21:55:18", conf: "96.4%" },
  { id: "TR-2026-008", plate: "KA51-PP-1100", type: "Car", violation: "Illegal Parking", time: "2026-06-18 21:40:02", conf: "92.0%" }
];

const mockGalleryData = [
  { img: "assets/annotated.png", title: "Helmet & Lane Infraction", label: "HELMET VIOLATION", time: "2026-06-18 23:10:15", conf: "95.8%", isCritical: true },
  { img: "assets/original.png", title: "Intersection Stop Line Breach", label: "STOP LINE", time: "2026-06-18 22:30:12", conf: "94.5%", isCritical: false },
  { img: "assets/processed.png", title: "Speedway Night Classification", label: "VEHICLE DETECTION", time: "2026-06-18 21:55:18", conf: "98.9%", isCritical: false }
];

const reportTemplates = {
  daily: {
    title: "DAILY SYSTEM REPORT - JUN 18, 2026",
    date: "June 18, 2026",
    stats: {
      "Total Vehicles Processed": "5,412",
      "Total Infractions Flags": "439",
      "AI Average Matching Confidence": "96.4%",
      "Critical Red Light Runs": "34",
      "Helmet Detection Failures": "112",
      "Wrong Way Intersections": "12",
      "Stop Line Enforcements": "281"
    }
  },
  weekly: {
    title: "WEEKLY CONSOLIDATED REPORT - WEEK 25",
    date: "June 12 - June 18, 2026",
    stats: {
      "Total Vehicles Processed": "38,920",
      "Total Infractions Flags": "3,110",
      "AI Average Matching Confidence": "96.8%",
      "Critical Red Light Runs": "210",
      "Helmet Detection Failures": "820",
      "Wrong Way Intersections": "92",
      "Stop Line Enforcements": "1,988"
    }
  },
  monthly: {
    title: "MONTHLY REGULATORY REPORT - JUNE 2026",
    date: "June 01 - June 18, 2026",
    stats: {
      "Total Vehicles Processed": "143,820",
      "Total Infractions Flags": "12,953",
      "AI Average Matching Confidence": "96.75%",
      "Critical Red Light Runs": "982",
      "Helmet Detection Failures": "3,410",
      "Wrong Way Intersections": "392",
      "Stop Line Enforcements": "8,169"
    }
  }
};

// --- Initializing App ---
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  initCharts();
  renderLprTable(mockLprData);
  renderGallery(mockGalleryData);
  updateReportPreview("daily");
  initCounters();
  setupEventListeners();
  simulateLiveFeed();
});

// --- Live Clock ---
function initClock() {
  const timeEl = document.getElementById("liveTime");
  setInterval(() => {
    const now = new Date();
    timeEl.textContent = now.toUTCString().replace("GMT", "UTC");
  }, 1000);
}

// --- Setup Charts (Chart.js) ---
function initCharts() {
  const ctxPie = document.getElementById("violationPieChart").getContext("2d");
  const ctxBar = document.getElementById("dailyBarChart").getContext("2d");
  const ctxLine = document.getElementById("monthlyLineChart").getContext("2d");
  const ctxDou = document.getElementById("vehicleDoughnutChart").getContext("2d");

  // Chart Global Default Stylings
  Chart.defaults.color = "#8fa0c4";
  Chart.defaults.font.family = "'Inter', sans-serif";

  // 1. Violation Distribution Pie Chart
  charts.pie = new Chart(ctxPie, {
    type: "pie",
    data: {
      labels: ["Helmet", "Seatbelt", "Red Light", "Wrong Side", "Illegal Parking", "Stop Line", "Triple Riding"],
      datasets: [{
        data: [26, 18, 14, 11, 8, 15, 8],
        backgroundColor: [
          "#00f2fe", "#4facfe", "#b15cff", "#f736ff", "#00ff87", "#f9d423", "#ff3366"
        ],
        borderWidth: 1,
        borderColor: "rgba(10, 18, 42, 0.8)"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { boxWidth: 12, font: { size: 10 } }
        }
      }
    }
  });

  // 2. Daily Violations Bar Chart
  charts.bar = new Chart(ctxBar, {
    type: "bar",
    data: {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      datasets: [{
        label: "Infractions",
        data: [120, 145, 130, 165, 190, 220, 205],
        backgroundColor: "rgba(0, 242, 254, 0.45)",
        borderColor: "#00f2fe",
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.03)" } },
        y: { grid: { color: "rgba(255,255,255,0.03)" } }
      }
    }
  });

  // 3. Monthly Trend Line Chart
  charts.line = new Chart(ctxLine, {
    type: "line",
    data: {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      datasets: [{
        label: "Detections",
        data: [8200, 9400, 10500, 11200, 12100, 12953],
        borderColor: "#b15cff",
        backgroundColor: "rgba(177, 92, 255, 0.08)",
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointBackgroundColor: "#f736ff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.03)" } },
        y: { grid: { color: "rgba(255,255,255,0.03)" } }
      }
    }
  });

  // 4. Vehicle Doughnut Chart
  charts.dou = new Chart(ctxDou, {
    type: "doughnut",
    data: {
      labels: ["Cars", "Motorcycles", "Trucks", "Buses"],
      datasets: [{
        data: [55, 30, 10, 5],
        backgroundColor: ["#00f2fe", "#b15cff", "#00ff87", "#ffaa00"],
        borderWidth: 1,
        borderColor: "rgba(10, 18, 42, 0.8)"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { boxWidth: 12, font: { size: 10 } }
        }
      },
      cutout: "70%"
    }
  });
}

// --- Animated Counters ---
function initCounters() {
  const counters = document.querySelectorAll(".counter");
  
  counters.forEach(counter => {
    const target = +counter.getAttribute("data-target");
    if (target === 0) return;
    
    let current = 0;
    const increment = Math.max(1, Math.floor(target / 80));
    
    const updateCount = () => {
      current += increment;
      if (current < target) {
        counter.textContent = current.toLocaleString();
        requestAnimationFrame(updateCount);
      } else {
        counter.textContent = target.toLocaleString();
      }
    };
    updateCount();
  });
}

// --- Render License Plate Table ---
function renderLprTable(data) {
  const tbody = document.getElementById("lprTableBody");
  tbody.innerHTML = "";

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dark-grey);">No matching records found.</td></tr>`;
    return;
  }

  data.forEach(item => {
    let tagClass = "none";
    if (item.violation !== "None") {
      tagClass = (item.violation === "Red Light Violation" || item.violation === "Wrong Side Driving") ? "critical" : "";
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.id}</td>
      <td><span class="plate-badge">${item.plate}</span></td>
      <td>${item.type}</td>
      <td><span class="violation-tag ${tagClass}">${item.violation}</span></td>
      <td>${item.time}</td>
      <td style="font-weight:600; color:var(--neon-green);">${item.conf}</td>
    `;
    tbody.appendChild(tr);
  });
}

// --- Filter LPR Table ---
function filterLprTable() {
  const searchValue = document.getElementById("lprSearchInput").value.toLowerCase();
  const typeFilter = document.getElementById("filterVehicleType").value;
  const violationFilter = document.getElementById("filterViolationType").value;

  const filtered = mockLprData.filter(item => {
    const matchesSearch = item.plate.toLowerCase().includes(searchValue) || 
                          item.id.toLowerCase().includes(searchValue) ||
                          item.type.toLowerCase().includes(searchValue) ||
                          item.violation.toLowerCase().includes(searchValue);
                          
    const matchesType = typeFilter === "ALL" || item.type === typeFilter;
    const matchesViolation = violationFilter === "ALL" || 
                              (violationFilter === "None" && item.violation === "None") ||
                              (violationFilter !== "None" && item.violation === violationFilter);

    return matchesSearch && matchesType && matchesViolation;
  });

  renderLprTable(filtered);
}

// --- Render Evidence Gallery ---
function renderGallery(data) {
  const grid = document.getElementById("evidenceGalleryGrid");
  grid.innerHTML = "";

  data.forEach(item => {
    const card = document.createElement("div");
    card.className = `evidence-card ${item.isCritical ? 'alert-active' : ''}`;
    card.innerHTML = `
      <div class="evidence-img-container">
        <span class="evidence-overlay-label">${item.label}</span>
        <img src="${item.img}" alt="${item.title}">
      </div>
      <div class="evidence-details">
        <div class="evidence-meta-row">
          <span>AI Conf: <strong class="evidence-confidence">${item.conf}</strong></span>
          <span>${item.time}</span>
        </div>
        <h4 class="evidence-title">${item.title}</h4>
        <button class="evidence-btn-download" onclick="simulateDownload('${item.title}')">
          <i class="fa-solid fa-download"></i> Download Bounding Evidence
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

// --- Update Report Preview ---
function updateReportPreview(timeframe) {
  const preview = reportTemplates[timeframe];
  document.getElementById("previewReportTitle").textContent = preview.title;
  document.getElementById("previewReportDate").textContent = `Generated: ${preview.date} // Secure Auth v8.4`;
  
  const contentBody = document.getElementById("previewReportContent");
  contentBody.innerHTML = "";
  
  for (const [key, val] of Object.entries(preview.stats)) {
    const row = document.createElement("div");
    row.className = "report-stat-row";
    row.innerHTML = `
      <span>${key}</span>
      <strong>${val}</strong>
    `;
    contentBody.appendChild(row);
  }
}

// --- Simulated Download ---
function simulateDownload(title) {
  alert(`[SECURE ACCESS] Generating evidence artifact file for: "${title}". Download will start shortly.`);
}

// --- Setup Event Listeners ---
function setupEventListeners() {
  // Mobile Nav Toggle
  const toggleBtn = document.getElementById("mobileMenuToggle");
  const sidebar = document.querySelector(".sidebar");
  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("mobile-active");
  });

  // Hide sidebar on clicking nav list in mobile
  document.querySelectorAll(".nav-item a").forEach(link => {
    link.addEventListener("click", (e) => {
      sidebar.classList.remove("mobile-active");
      
      // Update Active Nav Link
      document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
      link.parentElement.classList.add("active");
    });
  });

  // Notification panel Toggle
  const notiBtn = document.getElementById("notificationBtn");
  const notiPanel = document.getElementById("notificationsPanel");
  notiBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    notiPanel.classList.toggle("active");
  });

  document.addEventListener("click", (e) => {
    if (!notiPanel.contains(e.target) && e.target !== notiBtn) {
      notiPanel.classList.remove("active");
    }
  });

  document.getElementById("clearNotis").addEventListener("click", () => {
    document.getElementById("notiList").innerHTML = `<div style="padding:15px; text-align:center; color: var(--text-dark-grey);">No active alerts.</div>`;
    document.getElementById("notiCount").textContent = "0";
    document.getElementById("notiCount").style.display = "none";
  });

  // Upload Module Buttons
  const fileInput = document.getElementById("fileInput");
  const btnUploadSelect = document.getElementById("btnUploadSelect");
  const btnStartDetection = document.getElementById("btnStartDetection");
  const btnReset = document.getElementById("btnReset");
  const dragArea = document.getElementById("dragArea");
  const uploadFilename = document.getElementById("uploadFilename");

  btnUploadSelect.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  // Drag and drop events
  dragArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    dragArea.classList.add("active");
  });

  dragArea.addEventListener("dragleave", () => {
    dragArea.classList.remove("active");
  });

  dragArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dragArea.classList.remove("active");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  // Trigger scanning sequence
  btnStartDetection.addEventListener("click", () => {
    runDetectionScan();
  });

  // Reset button
  btnReset.addEventListener("click", () => {
    resetUploadModule();
  });

  // Preview Tabs switching
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      
      const tabName = btn.getAttribute("data-tab");
      document.querySelectorAll(".viewer-img").forEach(img => img.classList.remove("active"));
      
      if (tabName === "original") {
        document.getElementById("imgOriginal").classList.add("active");
      } else if (tabName === "processed") {
        document.getElementById("imgProcessed").classList.add("active");
      } else if (tabName === "annotated") {
        document.getElementById("imgAnnotated").classList.add("active");
      }
    });
  });

  // LPR search and filters
  document.getElementById("lprSearchInput").addEventListener("input", filterLprTable);
  document.getElementById("filterVehicleType").addEventListener("change", filterLprTable);
  document.getElementById("filterViolationType").addEventListener("change", filterLprTable);

  // Reports radio selection
  document.querySelectorAll(".report-radio-card").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".report-radio-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      const rName = card.getAttribute("data-report");
      updateReportPreview(rName);
    });
  });

  // Reports Buttons Action
  document.getElementById("btnExportPDF").addEventListener("click", () => {
    alert("[EXPORTER] Compiling PDF format document. Secure digital signature MH-TRAFFIC-AI added. Download starting...");
  });
  document.getElementById("btnExportCSV").addEventListener("click", () => {
    alert("[EXPORTER] Building spreadsheet export of all filter-matching incident records in CSV format.");
  });
  document.getElementById("btnPrintReport").addEventListener("click", () => {
    window.print();
  });
}

// --- Upload State Handlers ---
function handleFileSelected(file) {
  const uploadFilename = document.getElementById("uploadFilename");
  const btnStartDetection = document.getElementById("btnStartDetection");
  
  // Set mock files
  document.getElementById("imgOriginal").src = "assets/original.png";
  document.getElementById("imgProcessed").src = "assets/processed.png";
  document.getElementById("imgAnnotated").src = "assets/annotated.png";

  uploadFilename.textContent = `Selected File: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  uploadFilename.style.display = "block";
  btnStartDetection.removeAttribute("disabled");

  // Show original preview
  document.getElementById("viewerPlaceholder").style.display = "none";
  document.getElementById("imgOriginal").classList.add("active");
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelector("[data-tab='original']").classList.add("active");
}

function runDetectionScan() {
  const consoleEl = document.getElementById("terminalConsole");
  const laserEl = document.getElementById("scannerLaser");
  const tabProcessed = document.getElementById("tabProcessed");
  const tabAnnotated = document.getElementById("tabAnnotated");
  const btnStartDetection = document.getElementById("btnStartDetection");

  btnStartDetection.setAttribute("disabled", true);
  consoleEl.style.display = "block";
  consoleEl.innerHTML = "";
  laserEl.style.display = "block";

  const logs = [
    "[SYSTEM] Initiating Traffic AI Core CLI...",
    "[IMAGE] Reading feed resolution: 1920x1080px (RGB channels)",
    "[PREPROCESS] Enhancing low-light shadows (CLAHE algorithm)... Done.",
    "[PREPROCESS] Filtering lens moisture and high-speed motion blurs... Done.",
    "[MODEL] Running inference with YOLOv8s weights (Conf threshold: 0.25)...",
    "[YOLOv8] Detected (1) Motorcycle [0.94], (4) Cars [0.98, 0.95, 0.89, 0.81]",
    "[MODEL] Crop coordinates isolated. Running helmet infraction check...",
    "[HELMET DETECTOR] Negative overlay result - Rider lacks helmet protection! Conf: 95.8%",
    "[OCR] Plate bounding box detected. Character extraction via EasyOCR...",
    "[EasyOCR] Success. Extracted text: MH12-LK-9021",
    "[RTO REGISTRY] Querying national vehicle database... Match found.",
    "[RTO REGISTRY] Vehicle Type: Two-Wheeler (Motorcycle), Reg: R. Sharma.",
    "[SYSTEM] Enforcement Ticket generated. Rendering AI Bounding Annotations..."
  ];

  let lineIdx = 0;
  function printLog() {
    if (lineIdx < logs.length) {
      const p = document.createElement("div");
      p.className = "terminal-line";
      p.textContent = logs[lineIdx];
      consoleEl.appendChild(p);
      consoleEl.scrollTop = consoleEl.scrollHeight;
      lineIdx++;
      setTimeout(printLog, 350);
    } else {
      // Completed scanning
      laserEl.style.display = "none";
      tabProcessed.removeAttribute("disabled");
      tabAnnotated.removeAttribute("disabled");
      
      // Auto switch to Annotated View
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      tabAnnotated.classList.add("active");
      document.querySelectorAll(".viewer-img").forEach(img => img.classList.remove("active"));
      document.getElementById("imgAnnotated").classList.add("active");

      // Update counters in results panel
      triggerResultPanelCounters();

      // Push result to table
      addNewRecord();
      
      // Add notification
      triggerLiveNotification("Helmet Violation", "Motorcycle MH12-LK-9021 flagged at Junction 4.", "critical");
    }
  }

  printLog();
}

function triggerResultPanelCounters() {
  const counts = {
    resVehicles: 5,
    resHelmet: 1,
    resSeatbelt: 0,
    resWrongSide: 0,
    resParking: 0,
    resRedLight: 0
  };

  for (const [id, val] of Object.entries(counts)) {
    const el = document.getElementById(id);
    el.setAttribute("data-target", val);
  }

  // Animate the values
  const counters = document.querySelectorAll("#results-panel .counter");
  counters.forEach(counter => {
    const target = +counter.getAttribute("data-target");
    let current = 0;
    const interval = setInterval(() => {
      current++;
      if (current <= target) {
        counter.textContent = current;
      } else {
        clearInterval(interval);
        counter.textContent = target;
      }
    }, 150);
  });

  // Set card classes for alert
  document.getElementById("cardHelmet").classList.add("alert-active");
  document.getElementById("statHelmet").textContent = "VIOLATION";
}

function addNewRecord() {
  // Check if MH12-LK-9021 already exists in table list
  if (mockLprData.some(d => d.plate === "MH12-LK-9021")) return;

  const newRec = {
    id: "TR-2026-009",
    plate: "MH12-LK-9021",
    type: "Motorcycle",
    violation: "Helmet Violation",
    time: new Date().toISOString().replace('T', ' ').substring(0, 19),
    conf: "95.8%"
  };

  mockLprData.unshift(newRec);
  renderLprTable(mockLprData);

  // Add to evidence gallery
  const newEv = {
    img: "assets/annotated.png",
    title: "Motorcycle Helmet Breach (Junction 4)",
    label: "HELMET VIOLATION",
    time: newRec.time,
    conf: "95.8%",
    isCritical: true
  };
  mockGalleryData.unshift(newEv);
  renderGallery(mockGalleryData);
}

function resetUploadModule() {
  document.getElementById("fileInput").value = "";
  document.getElementById("uploadFilename").style.display = "none";
  document.getElementById("btnStartDetection").setAttribute("disabled", true);
  document.getElementById("terminalConsole").style.display = "none";
  document.getElementById("scannerLaser").style.display = "none";
  
  document.getElementById("tabProcessed").setAttribute("disabled", true);
  document.getElementById("tabAnnotated").setAttribute("disabled", true);
  
  document.querySelectorAll(".viewer-img").forEach(img => {
    img.classList.remove("active");
    img.src = "";
  });

  document.getElementById("viewerPlaceholder").style.display = "flex";

  // Reset counters to 0
  const counters = document.querySelectorAll("#results-panel .counter");
  counters.forEach(counter => {
    counter.textContent = "0";
    counter.setAttribute("data-target", "0");
  });

  document.querySelectorAll(".result-card").forEach(card => card.classList.remove("alert-active"));
  document.getElementById("statHelmet").textContent = "NORMAL";
}

// --- Live Notifications Stream (Simulation) ---
function simulateLiveFeed() {
  // Random notification triggers every 20 seconds
  const plates = ["KA53-MM-1022", "DL1C-BY-9002", "MH14-TT-4431", "HR26-DD-3030"];
  const vehicles = ["Car", "Motorcycle", "Car", "Truck"];
  const violations = ["Seatbelt Violation", "Triple Riding", "Illegal Parking", "Red Light Violation"];
  const crit = [false, true, false, true];

  let idx = 0;
  setInterval(() => {
    const plate = plates[idx];
    const veh = vehicles[idx];
    const vio = violations[idx];
    const isCrit = crit[idx];
    const randTime = new Date().toISOString().replace('T', ' ').substring(0, 19);
    
    // Push database record
    const tempId = `TR-2026-0${10 + idx}`;
    const newRec = { id: tempId, plate: plate, type: veh, violation: vio, time: randTime, conf: "94.2%" };
    mockLprData.unshift(newRec);
    renderLprTable(mockLprData);

    // Trigger Notification
    triggerLiveNotification(vio, `${veh} (${plate}) flagged for ${vio}.`, isCrit ? "critical" : "");
    
    idx = (idx + 1) % plates.length;
  }, 22000);
}

function triggerLiveNotification(title, text, type) {
  const panel = document.getElementById("notificationsPanel");
  const list = document.getElementById("notiList");
  const countBadge = document.getElementById("notiCount");
  
  let currentCount = parseInt(countBadge.textContent);
  currentCount++;
  countBadge.textContent = currentCount;
  countBadge.style.display = "flex";

  const item = document.createElement("div");
  item.className = `notification-item ${type}`;
  item.innerHTML = `
    <strong>${title} Detected</strong> - ${text}
    <span class="notification-time">Just now</span>
  `;

  list.insertBefore(item, list.firstChild);

  // Subtle alert sound/vibe (mock sound)
  console.log(`[ALERT TRIGGER] Live traffic alert triggered: ${title}`);
}
