
//const API_BASE_URL = "http://127.0.0.1:8000";
const API_BASE_URL = "https://customer-journey-pipeline.onrender.com";
let isRefreshing = false;

function formatNumber(value) {
    return Number(value ?? 0).toLocaleString("en-US");
}

function formatPercent(value) {
    return `${(Number(value ?? 0) * 100).toFixed(1)}%`;
}

function setConnectionStatus(connected) {
    const status = document.getElementById("connection-status");
    const dot = document.querySelector(".status-dot");

    status.textContent = connected ? "API connected" : "Connection failed";
    if (dot) {
        dot.style.background = connected ? "#22a06b" : "#d64545";
    }
}

// 1. Load the main KPI cards
async function loadDashboard() {
    const status = document.getElementById("connection-status");

    try {
        const response = await fetch(`${API_BASE_URL}/api/metrics`);

        if (!response.ok) {
            throw new Error(`Metrics API returned HTTP ${response.status}`);
        }

        const metrics = await response.json();

        document.getElementById("total-sessions").textContent =
            formatNumber(metrics.total_sessions);

        document.getElementById("converted-sessions").textContent =
            formatNumber(metrics.converted_sessions);

        document.getElementById("conversion-rate").textContent =
            formatPercent(metrics.conversion_rate);

        document.getElementById("support-rate").textContent =
            formatPercent(metrics.support_contact_rate);

        setConnectionStatus(true);
    } catch (error) {
        console.error("Unable to load dashboard metrics:", error);
        setConnectionStatus(false);
    }
}

// 2. Load funnel chart and conversion insights
async function loadFunnel() {
    const message = document.getElementById("funnel-message");
    const canvas = document.getElementById("funnel-chart");

    try {
        const response = await fetch(`${API_BASE_URL}/api/funnel`);

        if (!response.ok) {
            throw new Error(`Funnel API returned HTTP ${response.status}`);
        }

        const funnel = await response.json();

        if (!Array.isArray(funnel) || funnel.length === 0) {
            throw new Error("No funnel data is available.");
        }

        const browse = funnel.find(stage => stage.stage === "browse");
        const product = funnel.find(
            stage => stage.stage === "product_interest"
        );
        const purchase = funnel.find(stage => stage.stage === "purchase");

        if (!browse || !product || !purchase) {
            throw new Error("Required funnel stages are missing.");
        }

        const browseCount = Number(browse.sessions_reached);
        const productCount = Number(product.sessions_reached);
        const purchaseCount = Number(purchase.sessions_reached);

        if (
            ![browseCount, productCount, purchaseCount].every(Number.isFinite) ||
            browseCount < 0 ||
            productCount < 0 ||
            purchaseCount < 0
        ) {
            throw new Error("Funnel contains invalid session counts.");
        }

        if (typeof Chart === "undefined") {
            throw new Error("Chart.js did not load. Check your internet connection.");
        }

        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }

        canvas.hidden = false;
        message.hidden = true;

        new Chart(canvas, {
            type: "bar",
            data: {
                labels: funnel.map(stage =>
                    stage.stage.replaceAll("_", " ")
                ),
                datasets: [{
                    label: "Sessions reached",
                    data: funnel.map(stage => Number(stage.sessions_reached)),
                    backgroundColor: ["#6485e5", "#8b9ff0", "#22a06b"],
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: context =>
                                ` ${formatNumber(context.raw)} sessions`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });

        // Calculate consecutive-stage drop-offs
        const productDropoffCount = Math.max(0, browseCount - productCount);
        const purchaseDropoffCount = Math.max(0, productCount - purchaseCount);
        const notConvertedCount = Math.max(0, browseCount - purchaseCount);

        const productDropoffRate = browseCount > 0
            ? productDropoffCount / browseCount
            : 0;

        const purchaseDropoffRate = productCount > 0
            ? purchaseDropoffCount / productCount
            : 0;

        const conversionRate = browseCount > 0
            ? purchaseCount / browseCount
            : 0;

        document.getElementById("insight-conversion-rate").textContent =
            formatPercent(conversionRate);

        document.getElementById("dropoff-product").textContent =
            formatPercent(productDropoffRate);

        document.getElementById("dropoff-product-count").textContent =
            `${formatNumber(productDropoffCount)} of ${formatNumber(browseCount)} browse sessions`;

        document.getElementById("dropoff-purchase").textContent =
            formatPercent(purchaseDropoffRate);

        document.getElementById("dropoff-purchase-count").textContent =
            `${formatNumber(purchaseDropoffCount)} of ${formatNumber(productCount)} product-interest sessions`;

        document.getElementById("insight-not-converted").textContent =
            formatNumber(notConvertedCount);

    } catch (error) {
        console.error("Unable to load funnel:", error);

        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }

        canvas.hidden = true;
        message.hidden = false;
        message.textContent =
            "Unable to load funnel data. Check the API and refresh.";
    }
}

// 3. Load overall and dataset-level data quality
async function loadQuality() {
    const message = document.getElementById("quality-message");
    const indicator = document.querySelector(".quality-indicator");
    const breakdown = document.getElementById("quality-breakdown");

    try {
        const response = await fetch(`${API_BASE_URL}/api/quality`);

        if (!response.ok) {
            throw new Error(`Quality API returned HTTP ${response.status}`);
        }

        const quality = await response.json();

        breakdown.replaceChildren();

        quality.datasets.forEach(dataset => {
            const row = document.createElement("div");
            row.className = "quality-row";

            const name = document.createElement("span");
            name.textContent = dataset.dataset;

            const details = document.createElement("span");
            details.textContent =
                `${formatNumber(dataset.valid_records)}/` +
                `${formatNumber(dataset.total_records)} · ` +
                formatPercent(dataset.quality_rate);

            row.append(name, details);
            breakdown.appendChild(row);
        });

        message.textContent =
            `${formatNumber(quality.valid_records)} valid of ` +
            `${formatNumber(quality.total_records)} records · ` +
            `${formatNumber(quality.quarantined_records)} quarantined · ` +
            `${formatPercent(quality.quality_rate)} accepted`;

        indicator.style.background =
            quality.quarantined_records > 0 ? "#d64545" : "#22a06b";

    } catch (error) {
        console.error("Unable to load data quality:", error);

        message.textContent =
            "Unable to load data quality. Check the API.";

        indicator.style.background = "#d64545";
        breakdown.replaceChildren();
    }
}

let outcomesChart = null;

async function loadOutcomes() {
  const message = document.getElementById("outcomes-message");
  const breakdown = document.getElementById("outcomes-breakdown");

  try {
    const response = await fetch(`${API_BASE_URL}/api/outcomes`);

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const data = await response.json();

    message.textContent = `Total sessions: ${data.total_sessions}`;
    breakdown.replaceChildren();

    data.outcomes.forEach((item) => {
      const row = document.createElement("div");
      row.className = "quality-row";

      const label = document.createElement("span");
      label.textContent = item.label;

      const value = document.createElement("strong");
      value.textContent =
        `${item.count} (${Number(item.percentage).toFixed(1)}%)`;

      row.append(label, value);
      breakdown.appendChild(row);
    });

    if (outcomesChart) {
      outcomesChart.destroy();
    }

    const canvas = document.getElementById("outcomes-chart");

    outcomesChart = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: data.outcomes.map((item) => item.label),
        datasets: [{
          data: data.outcomes.map((item) => item.count)
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom"
          },
          tooltip: {
            callbacks: {
              label(context) {
                const count = context.raw;
                const percentage = data.total_sessions
                  ? (count / data.total_sessions * 100).toFixed(1)
                  : "0.0";

                return `${context.label}: ${count} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  } catch (error) {
    message.textContent = "Unable to load journey outcomes.";
    console.error("Journey outcomes error:", error);
  }
}

let devicesChart = null;
let trendsChart = null;
let sessionsOffset = 0;
const sessionsPageSize = 10;

function showMessage(id, message) {
    const element = document.getElementById(id);
    if (element) element.textContent = message;
}

function drawTable(containerId, columns, rows, emptyMessage = "No records found.") {
    const container = document.getElementById(containerId);
    container.replaceChildren();

    if (!rows.length) {
        const message = document.createElement("p");
        message.textContent = emptyMessage;
        container.appendChild(message);
        return;
    }

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    columns.forEach(column => {
        const th = document.createElement("th");
        th.textContent = column.label;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    rows.forEach(row => {
        const tr = document.createElement("tr");

        columns.forEach(column => {
            const td = document.createElement("td");

            if (column.render) {
                column.render(td, row);
            } else {
                const value = row[column.key];
                td.textContent =
                    value === null || value === undefined ? "—" : String(value);
            }

            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

function destroyChart(chart) {
    if (chart) chart.destroy();
}

// 4. Device performance
async function loadDevices() {
    const message = "devices-message";

    try {
        const response = await fetch(`${API_BASE_URL}/api/devices`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        showMessage(
            message,
            `${formatNumber(data.total_sessions)} sessions across all devices`
        );

        const rows = data.devices || [];

        drawTable("devices-breakdown", [
            { key: "device", label: "Device" },
            { key: "total_sessions", label: "Sessions" },
            { key: "converted_sessions", label: "Converted" },
            {
                label: "Conversion rate",
                render: (td, row) => {
                    td.textContent = formatPercent(row.conversion_rate);
                }
            }
        ], rows);

        destroyChart(devicesChart);

        devicesChart = new Chart(
            document.getElementById("devices-chart"),
            {
                type: "bar",
                data: {
                    labels: rows.map(row => row.device),
                    datasets: [{
                        label: "Sessions",
                        data: rows.map(row => row.total_sessions)
                    }, {
                        label: "Converted sessions",
                        data: rows.map(row => row.converted_sessions)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    }
                }
            }
        );
    } catch (error) {
        showMessage(message, "Unable to load device performance.");
        console.error("Device performance error:", error);
    }
}

// 5. Page and product performance
async function loadPerformance() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/performance`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        const pages = (data.page_performance || []).slice(0, 10);
        const products = (data.product_performance || []).slice(0, 10);

        showMessage("pages-message", `${pages.length} page records shown`);
        showMessage("products-message", `${products.length} product records shown`);

        drawTable("pages-table", [
            { key: "page_name", label: "Page" },
            { key: "sessions", label: "Sessions" },
            { key: "page_views", label: "Page views" },
            { key: "event_count", label: "Events" }
        ], pages);

        drawTable("products-table", [
            { key: "product_name", label: "Product" },
            { key: "sessions", label: "Sessions" },
            { key: "item_views", label: "Item views" },
            { key: "add_to_cart_events", label: "Add to cart" },
            { key: "purchase_events", label: "Purchase events" }
        ], products);
    } catch (error) {
        showMessage("pages-message", "Unable to load page performance.");
        showMessage("products-message", "Unable to load product performance.");
        console.error("Page/product performance error:", error);
    }
}

// 6. Time-based trends
async function loadTrends() {
    const interval = document.getElementById("trend-interval").value;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/trends?interval=${encodeURIComponent(interval)}`
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        const rows = data.trends || [];

        showMessage(
            "trends-message",
            `${formatNumber(rows.length)} ${interval} periods`
        );

        destroyChart(trendsChart);

        trendsChart = new Chart(
            document.getElementById("trends-chart"),
            {
                type: "line",
                data: {
                    labels: rows.map(row => row.period),
                    datasets: [{
                        label: "Sessions",
                        data: rows.map(row => row.sessions),
                        tension: 0.25
                    }, {
                        label: "Converted sessions",
                        data: rows.map(row => row.converted_sessions),
                        tension: 0.25
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: "index"
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    }
                }
            }
        );
    } catch (error) {
        showMessage("trends-message", "Unable to load time-based trends.");
        console.error("Trends error:", error);
    }
}

// 7. Session explorer
async function loadSessions() {
    const query = document.getElementById("session-search").value.trim();
    const device = document.getElementById("session-device").value;
    const outcome = document.getElementById("session-outcome").value;

    const params = new URLSearchParams({
        limit: String(sessionsPageSize),
        offset: String(sessionsOffset)
    });

    if (query) params.set("q", query);
    if (device) params.set("device", device);
    if (outcome) params.set("outcome", outcome);

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/sessions?${params.toString()}`
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        showMessage(
            "sessions-message",
            `${formatNumber(data.total)} matching sessions`
        );

        const rows = data.sessions || [];

        drawTable("sessions-table", [
            { key: "session_id", label: "Session ID" },
            { key: "customer_id", label: "Customer ID" },
            { key: "device", label: "Device" },
            { key: "started_at", label: "Started at" },
            { key: "outcome", label: "Outcome" },
            {
                label: "Events",
                render: (td, row) => {
                    const button = document.createElement("button");
                    button.type = "button";
                    button.className = "secondary-button";
                    button.textContent = "View events";
                    button.addEventListener("click", () => {
                        loadSessionEvents(row.session_id);
                    });
                    td.appendChild(button);
                }
            }
        ], rows, "No sessions match these filters.");

        const currentPage = Math.floor(sessionsOffset / sessionsPageSize) + 1;
        const totalPages = Math.max(
            1,
            Math.ceil(data.total / sessionsPageSize)
        );

        showMessage("sessions-page", `Page ${currentPage} of ${totalPages}`);

        document.getElementById("sessions-previous").disabled =
            sessionsOffset === 0;

        document.getElementById("sessions-next").disabled =
            sessionsOffset + sessionsPageSize >= data.total;
    } catch (error) {
        showMessage("sessions-message", "Unable to load sessions.");
        console.error("Session explorer error:", error);
    }
}

// 8. Individual session event timeline
async function loadSessionEvents(sessionId) {
    const panel = document.getElementById("session-events-panel");
    panel.hidden = false;

    showMessage("selected-session-title", `Events for ${sessionId}`);
    showMessage("session-events-message", "Loading events...");

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}/events`
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        showMessage(
            "session-events-message",
            `${formatNumber(data.event_count)} events in this session`
        );

        drawTable("session-events-table", [
            { key: "event_timestamp", label: "Timestamp" },
            { key: "event_type", label: "Event" },
            { key: "source", label: "Source" },
            { key: "page_id", label: "Page ID" },
            { key: "product_id", label: "Product ID" }
        ], data.events || [], "No events found for this session.");

        panel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
        showMessage("session-events-message", "Unable to load session events.");
        console.error("Session events error:", error);
    }
}

// 9. Wire up explorer and trend controls
document.getElementById("search-sessions").addEventListener("click", () => {
    sessionsOffset = 0;
    loadSessions();
});

document.getElementById("session-search").addEventListener("keydown", event => {
    if (event.key === "Enter") {
        sessionsOffset = 0;
        loadSessions();
    }
});

document.getElementById("session-device").addEventListener("change", () => {
    sessionsOffset = 0;
    loadSessions();
});

document.getElementById("session-outcome").addEventListener("change", () => {
    sessionsOffset = 0;
    loadSessions();
});

document.getElementById("sessions-previous").addEventListener("click", () => {
    sessionsOffset = Math.max(0, sessionsOffset - sessionsPageSize);
    loadSessions();
});

document.getElementById("sessions-next").addEventListener("click", () => {
    sessionsOffset += sessionsPageSize;
    loadSessions();
});

document.getElementById("trend-interval").addEventListener("change", loadTrends);


/* --------------------------------------------------
   AI-powered insights
-------------------------------------------------- */

async function loadAiInsights() {
    const message = document.getElementById("ai-insights-message");
    const provider = document.getElementById("ai-provider");
    const container = document.getElementById("ai-insights-list");

    message.textContent = "Generating insights...";
    container.replaceChildren();

    try {
        const response = await fetch(`${API_BASE_URL}/api/insights`);

        if (!response.ok) {
            throw new Error(`AI insights API returned HTTP ${response.status}`);
        }

        const data = await response.json();
        provider.textContent = data.provider === "gemini"
            ? `Generated by Gemini${data.model ? ` · ${data.model}` : ""}`
            : "Rule-based insights";

        message.textContent = data.message || "Insights loaded successfully.";

        const insights = data.insights || [];

        if (!insights.length) {
            message.textContent = "No insights are available for this dataset.";
            return;
        }

        insights.forEach((insight) => {
            const card = document.createElement("article");
            card.className = "ai-insight-card";

            const priority = document.createElement("span");
            const level = String(insight.priority || "medium").toLowerCase();
            priority.className = `priority-label ${
                ["high", "medium", "low"].includes(level) ? level : "medium"
            }`;
            priority.textContent = `${level} priority`;

            const title = document.createElement("h3");
            title.textContent = insight.title || "Journey insight";

            const finding = document.createElement("p");
            finding.textContent = insight.finding || "No finding provided.";

            const evidenceTitle = document.createElement("strong");
            evidenceTitle.textContent = "Supporting evidence";

            const evidence = document.createElement("div");
            evidence.className = "evidence";
            evidence.textContent = JSON.stringify(
                insight.evidence ?? {},
                null,
                2
            );

            const recommendationTitle = document.createElement("strong");
            recommendationTitle.textContent = "Recommended action";

            const recommendation = document.createElement("p");
            recommendation.textContent =
                insight.recommendation || "No recommendation provided.";

            card.append(
                priority,
                title,
                finding,
                evidenceTitle,
                evidence,
                recommendationTitle,
                recommendation
            );

            container.appendChild(card);
        });
    } catch (error) {
        console.error("AI insights error:", error);
        provider.textContent = "Unavailable";
        message.textContent =
            "Unable to load AI insights. Check the API and try again.";
    }
}


/* --------------------------------------------------
   Anomaly detection and evaluation
-------------------------------------------------- */

function drawRecordTable(containerId, records, emptyMessage) {
    if (!Array.isArray(records) || records.length === 0) {
        drawTable(containerId, [], []);
        const container = document.getElementById(containerId);
        container.replaceChildren();

        const empty = document.createElement("p");
        empty.className = "message";
        empty.textContent = emptyMessage;
        container.appendChild(empty);
        return;
    }

    const keys = [...new Set(records.flatMap(
        record => Object.keys(record)
    ))];

    const columns = keys.map(key => ({
        key,
        label: key.replaceAll("_", " "),
        render: (cell, record) => {
            const value = record[key];
            cell.textContent = value === null || value === undefined
                ? "—"
                : typeof value === "object"
                    ? JSON.stringify(value)
                    : String(value);
        }
    }));

    drawTable(containerId, columns, records);
}


async function loadAnomalyMetrics() {
    const message = document.getElementById("anomaly-metrics-message");

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/anomalies/metrics`
        );

        if (!response.ok) {
            throw new Error(`Anomaly metrics API returned HTTP ${response.status}`);
        }

        const data = await response.json();

        drawRecordTable(
            "anomaly-metrics-table",
            data.metrics || [],
            "No anomaly metrics found. Run anomaly analysis first."
        );

        drawRecordTable(
            "anomaly-evaluation-table",
            data.evaluation || [],
            "No evaluation records found. Run anomaly analysis first."
        );

        message.textContent =
            `Loaded ${(data.metrics || []).length} metric record(s) and ` +
            `${(data.evaluation || []).length} evaluation record(s).`;
    } catch (error) {
        console.error("Anomaly metrics error:", error);
        message.textContent =
            "Unable to load anomaly metrics. Check the API.";
    }
}


async function loadAnomalies() {
    const message = document.getElementById("anomalies-message");
    const severity = document.getElementById("anomaly-severity").value.trim();
    const anomalyType = document.getElementById("anomaly-type").value.trim();
    const status = document.getElementById("anomaly-status").value.trim();

    const params = new URLSearchParams({
        limit: "100",
        offset: "0"
    });

    if (severity) params.set("severity", severity);
    if (anomalyType) params.set("anomaly_type", anomalyType);
    if (status) params.set("status", status);

    message.textContent = "Loading anomalies...";

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/anomalies?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`Anomalies API returned HTTP ${response.status}`);
        }

        const data = await response.json();
        const rows = data.anomalies || [];

        document.getElementById("anomaly-count-message").textContent =
            `${formatNumber(data.total)} matching anomaly record(s)`;

        message.textContent = `${rows.length} record(s) displayed.`;

        drawTable("anomalies-table", [
            { key: "anomaly_type", label: "Type" },
            { key: "severity", label: "Severity" },
            { key: "entity_id", label: "Entity ID" },
            { key: "session_id", label: "Session ID" },
            { key: "description", label: "Description" },
            { key: "status", label: "Status" },
            { key: "detected_at", label: "Detected at" }
        ], rows, "No anomalies match these filters.");
    } catch (error) {
        console.error("Anomaly loading error:", error);
        message.textContent =
            "Unable to load anomalies. Check the API.";
    }
}


async function runAnomalyAnalysis() {
    const button = document.getElementById("run-anomaly-analysis");

    button.disabled = true;
    button.textContent = "Running analysis...";

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/anomalies/run`,
            { method: "POST" }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(
                errorData.detail || `Analysis returned HTTP ${response.status}`
            );
        }

        const result = await response.json();

        document.getElementById("anomalies-message").textContent =
            result.status === "completed"
                ? "Analysis completed. Refreshing results..."
                : "Analysis finished.";

        await Promise.all([
            loadAnomalies(),
            loadAnomalyMetrics()
        ]);
    } catch (error) {
        console.error("Anomaly analysis error:", error);
        document.getElementById("anomalies-message").textContent =
            `Analysis failed: ${error.message}`;
    } finally {
        button.disabled = false;
        button.textContent = "Run analysis";
    }
}


/* --------------------------------------------------
   Wire up AI and anomaly controls
-------------------------------------------------- */

document.getElementById("refresh-ai-insights")
    .addEventListener("click", loadAiInsights);

document.getElementById("filter-anomalies")
    .addEventListener("click", loadAnomalies);

document.getElementById("run-anomaly-analysis")
    .addEventListener("click", runAnomalyAnalysis);

document.getElementById("anomaly-type")
    .addEventListener("keydown", event => {
        if (event.key === "Enter") loadAnomalies();
    });


// 4. Refresh the currently implemented API data
async function refreshDashboard() {
    if (isRefreshing) return;

    const button = document.getElementById("refresh-dashboard");

    isRefreshing = true;
    button.disabled = true;
    button.textContent = "Refreshing...";

    try {
        await Promise.all([
             loadDashboard(),
             loadFunnel(),
            loadQuality(),
            loadOutcomes(),
            loadDevices(),
            loadPerformance(),
            loadTrends(),
            loadSessions(),
            loadAiInsights(),
            loadAnomalies(),
            loadAnomalyMetrics()
        ]);
    } finally {
        isRefreshing = false;
        button.disabled = false;
        button.textContent = "↻ Refresh data";
    }
}

// 5. Highlight sidebar navigation
function initializeNavigation() {
    const links = document.querySelectorAll(".nav-link");
    const sections = document.querySelectorAll(
        ".main-content .content-section"
    );

    links.forEach(link => {
        link.addEventListener("click", () => {
            links.forEach(item => item.classList.remove("active"));
            link.classList.add("active");
        });
    });

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(entries => {
            const visibleSections = entries
                .filter(entry => entry.isIntersecting)
                .sort((a, b) => b.intersectionRatio - a.intersectionRatio);

            if (visibleSections.length === 0) return;

            const activeId = visibleSections[0].target.id;

            links.forEach(link => {
                link.classList.toggle(
                    "active",
                    link.getAttribute("href") === `#${activeId}`
                );
            });
        }, {
            rootMargin: "-10% 0px -65% 0px",
            threshold: [0, 0.1, 0.3]
        });

        sections.forEach(section => observer.observe(section));
    }
}

// 6. Initialize the frontend
document.getElementById("refresh-dashboard")
    .addEventListener("click", refreshDashboard);

initializeNavigation();
refreshDashboard();
console.log("APP.JS EXECUTED — dashboard script reached the end");
