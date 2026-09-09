// ===== 설정 =====
// 배포 시 이 값을 Render 백엔드 주소로 변경하세요. (예: "https://m1-2-backend.onrender.com")
const API_BASE_URL = "http://127.0.0.1:8000";

const CHART_COLORS = ["#2C3E66", "#3D8D7A", "#D4A24E", "#C1666B"];

// ===== 탭 전환 =====
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");

    if (btn.dataset.tab === "data") loadDataTable();
    if (btn.dataset.tab === "history") loadHistoryList();
    if (btn.dataset.tab === "summary") loadSummary();
  });
});

// ===== 공통 fetch 헬퍼 =====
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

/* =========================================================
   1. 채팅 화면
   ========================================================= */
let currentConversationId = null;

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const chatStatus = document.getElementById("chat-status");
const chatSendBtn = document.getElementById("chat-send-btn");

function appendChatMessage(role, content) {
  const div = document.createElement("div");
  div.className = `chat-msg ${role}`;
  div.textContent = content;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendChatMessage("user", message);
  chatInput.value = "";
  chatSendBtn.disabled = true;
  chatStatus.textContent = "AI가 답변을 생성하는 중입니다...";

  try {
    const data = await apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        conversation_id: currentConversationId,
      }),
    });
    currentConversationId = data.conversation_id;
    appendChatMessage("assistant", data.answer || "(빈 응답이 반환되었습니다.)");
    chatStatus.textContent = "";
  } catch (err) {
    chatStatus.textContent = `오류: ${err.message} (잠시 후 다시 시도해주세요)`;
  } finally {
    chatSendBtn.disabled = false;
  }
});

/* =========================================================
   2. 데이터 관리 화면
   ========================================================= */
const dataForm = document.getElementById("data-form");
const dataTableBody = document.getElementById("data-table-body");

async function loadDataTable() {
  dataTableBody.innerHTML = `<tr><td colspan="4">불러오는 중...</td></tr>`;
  try {
    const items = await apiFetch("/api/data");
    if (!items.length) {
      dataTableBody.innerHTML = `<tr><td colspan="4">데이터가 없습니다.</td></tr>`;
      return;
    }
    dataTableBody.innerHTML = items.map(item => `
      <tr data-id="${item.id}">
        <td>${item.date}</td>
        <td>${item.memo}</td>
        <td>${Number(item.value).toLocaleString()}</td>
        <td>
          <button class="btn-danger" onclick="deleteDataItem('${item.id}')">삭제</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    dataTableBody.innerHTML = `<tr><td colspan="4">불러오기 실패: ${err.message}</td></tr>`;
  }
}

dataForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const date = document.getElementById("data-date").value;
  const value = parseFloat(document.getElementById("data-value").value);
  const memo = document.getElementById("data-memo").value.trim();

  try {
    await apiFetch("/api/data", {
      method: "POST",
      body: JSON.stringify({ date, value, memo }),
    });
    dataForm.reset();
    loadDataTable();
  } catch (err) {
    alert(`추가 실패: ${err.message}`);
  }
});

async function deleteDataItem(id) {
  if (!confirm("이 데이터를 삭제하시겠습니까?")) return;
  try {
    await apiFetch(`/api/data/${id}`, { method: "DELETE" });
    loadDataTable();
  } catch (err) {
    alert(`삭제 실패: ${err.message}`);
  }
}

document.getElementById("data-refresh-btn").addEventListener("click", loadDataTable);

/* =========================================================
   3. 대화 기록 화면
   ========================================================= */
const historyList = document.getElementById("history-list");
const historyDetail = document.getElementById("history-detail");

async function loadHistoryList() {
  historyList.innerHTML = `<li>불러오는 중...</li>`;
  try {
    const items = await apiFetch("/api/conversations");
    if (!items.length) {
      historyList.innerHTML = `<li>대화 기록이 없습니다.</li>`;
      return;
    }
    historyList.innerHTML = items.map(item => `
      <li data-id="${item.id}">
        <div class="h-title">${escapeHtml(item.title)}</div>
        <div class="h-meta">${item.created_at ? item.created_at.slice(0, 19).replace("T", " ") : ""} · 메시지 ${item.message_count}개</div>
      </li>
    `).join("");

    historyList.querySelectorAll("li[data-id]").forEach(li => {
      li.addEventListener("click", () => {
        historyList.querySelectorAll("li").forEach(l => l.classList.remove("selected"));
        li.classList.add("selected");
        loadHistoryDetail(li.dataset.id);
      });
    });
  } catch (err) {
    historyList.innerHTML = `<li>불러오기 실패: ${err.message}</li>`;
  }
}

async function loadHistoryDetail(id) {
  historyDetail.innerHTML = `<p class="status-text">불러오는 중...</p>`;
  try {
    const conv = await apiFetch(`/api/conversations/${id}`);
    historyDetail.innerHTML = conv.messages.map(m => `
      <div class="chat-msg ${m.role}" style="margin-bottom:8px;">${escapeHtml(m.content)}</div>
    `).join("");
  } catch (err) {
    historyDetail.innerHTML = `<p class="status-text">불러오기 실패: ${err.message}</p>`;
  }
}

document.getElementById("history-refresh-btn").addEventListener("click", loadHistoryList);

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

/* =========================================================
   4. 요약 표시 화면
   ========================================================= */
const summaryMeta = document.getElementById("summary-meta");
const summaryTableBody = document.getElementById("summary-table-body");
let summaryChartInstance = null;

async function loadSummary() {
  summaryMeta.textContent = "불러오는 중...";
  summaryTableBody.innerHTML = "";
  try {
    const [summary, allData] = await Promise.all([
      apiFetch("/api/data/summary"),
      apiFetch("/api/data"),
    ]);

    summaryMeta.innerHTML = `
      <div>기간: <b>${summary.period ?? "-"}</b></div>
      <div>데이터 개수: <b>${summary.count}개</b></div>
      <div>매출 추세: <b>${summary.trend}</b></div>
    `;

    const metrics = summary.metrics_by_indicator || {};
    summaryTableBody.innerHTML = Object.entries(metrics).map(([name, m]) => `
      <tr>
        <td>${name}</td>
        <td>${Number(m.latest).toLocaleString()}</td>
        <td>${Number(m.average).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
        <td>${Number(m.max).toLocaleString()}</td>
        <td>${Number(m.min).toLocaleString()}</td>
        <td>${m.count}</td>
      </tr>
    `).join("");

    renderSummaryChart(allData);
  } catch (err) {
    summaryMeta.textContent = `불러오기 실패: ${err.message}`;
  }
}

function renderSummaryChart(allData) {
  const revenueData = allData
    .filter(d => d.memo === "매출액")
    .sort((a, b) => a.date.localeCompare(b.date));

  const ctx = document.getElementById("summary-chart");
  if (summaryChartInstance) summaryChartInstance.destroy();

  summaryChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: revenueData.map(d => d.date),
      datasets: [{
        label: "매출액",
        data: revenueData.map(d => d.value),
        borderColor: CHART_COLORS[0],
        backgroundColor: CHART_COLORS[0] + "22",
        tension: 0.25,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { ticks: { callback: v => Number(v).toLocaleString() } } },
    },
  });
}

document.getElementById("summary-refresh-btn").addEventListener("click", loadSummary);
