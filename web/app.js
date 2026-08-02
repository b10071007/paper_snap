document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentType = "all";
  let currentStatus = "all";
  let searchQuery = "";
  let debounceTimer = null;
  let activePaperData = null;

  // DOM Elements
  const searchInput = document.getElementById("searchInput");
  const clearSearchBtn = document.getElementById("clearSearchBtn");
  const typeTabs = document.getElementById("typeTabs");
  const statusSelect = document.getElementById("statusSelect");
  const paperGrid = document.getElementById("paperGrid");
  const resultsCount = document.getElementById("resultsCount");

  // Stats Elements
  const statTotal = document.getElementById("statTotal");
  const statClassic = document.getElementById("statClassic");
  const statLatest = document.getElementById("statLatest");
  const statPublished = document.getElementById("statPublished");

  // Modal Elements
  const readerModal = document.getElementById("readerModal");
  const modalCloseBtn = document.getElementById("modalCloseBtn");
  const modalTypeBadge = document.getElementById("modalTypeBadge");
  const modalPublishedBadge = document.getElementById("modalPublishedBadge");
  const modalArxivId = document.getElementById("modalArxivId");
  const modalTitle = document.getElementById("modalTitle");
  const modalAuthors = document.getElementById("modalAuthors");
  const modalDate = document.getElementById("modalDate");
  const modalArxivLink = document.getElementById("modalArxivLink");
  const modalSummary = document.getElementById("modalSummary");
  const modalProblem = document.getElementById("modalProblem");
  const modalMethod = document.getElementById("modalMethod");
  const modalConclusion = document.getElementById("modalConclusion");
  const modalFormattedPost = document.getElementById("modalFormattedPost");
  const copyPostBtn = document.getElementById("copyPostBtn");
  const toast = document.getElementById("toast");

  // Init
  loadStats();
  loadPapers();

  // Search input debouncing
  searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value.trim();
    clearSearchBtn.style.display = searchQuery ? "block" : "none";

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      loadPapers();
    }, 300);
  });

  clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    searchQuery = "";
    clearSearchBtn.style.display = "none";
    loadPapers();
  });

  // Type Tabs
  typeTabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab-btn");
    if (!btn) return;

    typeTabs.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentType = btn.dataset.type;
    loadPapers();
  });

  // Status Select
  statusSelect.addEventListener("change", (e) => {
    currentStatus = e.target.value;
    loadPapers();
  });

  // Fetch Dashboard Stats
  async function loadStats() {
    try {
      const res = await fetch("/api/stats");
      if (!res.ok) return;
      const data = await res.json();
      statTotal.textContent = data.total_papers || 0;
      statClassic.textContent = data.classic_processed || 0;
      statLatest.textContent = data.latest_processed || 0;
      statPublished.textContent = data.published_count || 0;
    } catch (err) {
      console.error("Failed to load stats:", err);
    }
  }

  // Fetch & Render Papers
  async function loadPapers() {
    paperGrid.innerHTML = `
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>正在搜尋資料庫...</p>
      </div>
    `;

    try {
      const url = new URL("/api/papers", window.location.origin);
      if (searchQuery) url.searchParams.set("q", searchQuery);
      if (currentType !== "all") url.searchParams.set("paper_type", currentType);
      if (currentStatus !== "all") url.searchParams.set("is_published", currentStatus);

      const res = await fetch(url);
      if (!res.ok) throw new Error("API error");
      const data = await res.json();

      resultsCount.textContent = data.total;
      renderPaperCards(data.items);
    } catch (err) {
      console.error("Error loading papers:", err);
      paperGrid.innerHTML = `
        <div class="empty-state">
          <p>⚠️ 載入論文資料失敗，請確認後端服務是否已正常啟動。</p>
        </div>
      `;
    }
  }

  // Render Paper Cards
  function renderPaperCards(papers) {
    if (!papers || papers.length === 0) {
      paperGrid.innerHTML = `
        <div class="empty-state">
          <p>📭 找不到符合條件的論文紀錄</p>
        </div>
      `;
      return;
    }

    paperGrid.innerHTML = papers.map(p => {
      const isClassic = p.paper_type === "classic";
      const typeBadgeClass = isClassic ? "badge-classic" : "badge-latest";
      const typeLabel = isClassic ? "🏛️ 經典論文" : "⚡ 最新速報";
      const isPub = p.is_published === 1;
      const statusBadgeClass = isPub ? "status-pub" : "status-draft";
      const statusLabel = isPub ? "✅ 已發布" : "📝 未發布";
      const snippet = p.summary || p.problem || "無摘要內容";

      return `
        <div class="paper-card" data-arxiv="${escapeHtml(p.arxiv_id)}">
          <div class="card-top">
            <span class="type-badge ${typeBadgeClass}">${typeLabel}</span>
            <span class="published-badge ${statusBadgeClass}">${statusLabel}</span>
          </div>
          <h3 class="card-title" title="${escapeHtml(p.title)}">${escapeHtml(p.title)}</h3>
          <div class="card-authors">👤 ${escapeHtml(p.authors || "未知作者")}</div>
          <div class="card-summary-snippet">${escapeHtml(snippet)}</div>
          <div class="card-footer">
            <span>ArXiv: ${escapeHtml(p.arxiv_id)}</span>
            <span class="read-btn">閱讀全文 ➔</span>
          </div>
        </div>
      `;
    }).join("");

    // Attach click listeners to cards
    paperGrid.querySelectorAll(".paper-card").forEach(card => {
      card.addEventListener("click", () => {
        const arxivId = card.dataset.arxiv;
        openModal(arxivId);
      });
    });
  }

  // Open Modal
  async function openModal(arxivId) {
    try {
      const res = await fetch(`/api/papers/${arxivId}`);
      if (!res.ok) throw new Error("Paper detail fetch error");
      const paper = await res.json();
      activePaperData = paper;

      const isClassic = paper.paper_type === "classic";
      modalTypeBadge.textContent = isClassic ? "🏛️ 經典論文" : "⚡ 最新速報";
      modalTypeBadge.className = `type-badge ${isClassic ? 'badge-classic' : 'badge-latest'}`;

      const isPub = paper.is_published === 1;
      modalPublishedBadge.textContent = isPub ? "✅ 已發布" : "📝 未發布";
      modalPublishedBadge.className = `published-badge ${isPub ? 'status-pub' : 'status-draft'}`;

      modalArxivId.textContent = `ArXiv: ${paper.arxiv_id}`;
      modalTitle.textContent = paper.title;
      modalAuthors.textContent = paper.authors || "未知作者";
      modalDate.textContent = paper.created_at ? paper.created_at.substring(0, 10) : "-";
      modalArxivLink.href = paper.url;

      modalSummary.textContent = paper.summary || "尚無摘要資料";
      modalProblem.textContent = paper.problem || "尚無問題描述資料";
      modalMethod.textContent = paper.method || "尚無方法描述資料";
      modalConclusion.textContent = paper.conclusion || "尚無結論描述資料";

      modalFormattedPost.textContent = paper.formatted_post || "尚無發布貼文內容";

      readerModal.classList.add("open");
    } catch (err) {
      console.error("Failed to open paper modal:", err);
    }
  }

  // Close Modal
  function closeModal() {
    readerModal.classList.remove("open");
    activePaperData = null;
  }

  modalCloseBtn.addEventListener("click", closeModal);
  readerModal.addEventListener("click", (e) => {
    if (e.target === readerModal) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && readerModal.classList.contains("open")) {
      closeModal();
    }
  });

  // Copy Post
  copyPostBtn.addEventListener("click", async () => {
    if (!activePaperData || !activePaperData.formatted_post) return;
    try {
      await navigator.clipboard.writeText(activePaperData.formatted_post);
      showToast("已成功複製 Facebook 貼文內容！");
    } catch (err) {
      console.error("Copy failed:", err);
    }
  });

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2500);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
