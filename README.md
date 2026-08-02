# 📄 Paper Snap - AI 論文自動化摘要與 Facebook 發布機器人

**Paper Snap** 是一個自動化的 AI 論文追蹤、重點摘要與 Facebook 粉絲專頁社群機器人。每天定時透過 ArXiv API 抓取最新 AI 論文，並結合經典論文儲列，運用 LLM（如 Gemini 2.5 Flash / GPT-4o-mini）生成結構化貼文並發布至 FB 粉絲專頁。

---

## 🌟 每日發布主題與特色

1. **經典論文發布 (每日 1 篇)**：
   - 自動從內建的 100 篇開創性經典 AI 論文庫 (`data/seed_classic_papers.json`) 依序取出。
   - LLM 生成深度的結構化摘要後發布，確保歷史經典持續被複習。

2. **最新論文發布 (每日 2 篇)**：
   - 每日自動連接 ArXiv API 抓取最新的 10 篇 AI 領域論文 (涵蓋 `cs.AI`, `cs.CL`, `cs.CV`, `cs.LG`)。
   - 經由 LLM 評估並挑選出 **最具價值與閱讀潛力的 2 篇精選論文** 發布。
   - 內建 SQLite 資料庫過濾機制，保證已發布過的論文不會重複發布。

3. **四段式結構化 FB 貼文**：
   - **1. 摘要**：核心特點與貢獻
   - **2. 問題**：欲解決的痛點與瓶頸
   - **3. 方法**：創新技術與演算法機制
   - **4. 結論**：實驗成果與未來應用價值

4. **安全測試與 Dry-Run 模式**：
   - 支援 `DRY_RUN=true` 模擬發布模式，在尚未申請 FB API 或無網路 Key 時可在主控台預覽發布成果。

---

## 📁 專案架構說明

```text
paper_snap/
├── config/
│   ├── settings.py           # 讀取 .env 設定檔與全域變數
│   └── prompt_templates.py   # LLM 論文評選與四段式摘要 Prompt
├── data/
│   ├── seed_classic_papers.json  # 經典論文初始種子資料庫
│   └── paper_snap.db        # SQLite 資料庫 (自動建立)
├── src/
│   ├── database/
│   │   ├── models.py         # Paper 實體資料結構定義
│   │   └── db_manager.py     # SQLite 建表、CRUD 與經典論文佇列
│   ├── fetchers/
│   │   └── arxiv_fetcher.py  # ArXiv SDK / Atom API 論文擷取模組
│   ├── llm/
│   │   └── summarizer.py     # Gemini / OpenAI 摘要生成與論文評選
│   ├── publishers/
│   │   └── facebook_publisher.py # FB Graph API 貼文與 Dry-Run
│   └── workflow/
│       └── runner.py         # 每日 Workflow 核心統籌
├── tests/
│   └── test_basic.py         # 單元測試範例
├── .env.example              # API Key 環境變數範本
├── .gitignore                # Git 忽略檔案設定
├── requirements.txt          # 套件依賴清單
├── README.md                 # 專案說明文件
└── main.py                   # 系統執行主程式 (CLI / 排程器)
```

---

## 🚀 快速開始與開發環境設定

### 1. 安裝 Python 依賴套件

建議使用 Python 3.9+ 虛擬環境：

```bash
python -m venv venv
# Windows 啟用虛擬環境:
venv\Scripts\activate
# Linux/macOS 啟用虛擬環境:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 設定 `.env` 環境變數

複製 `.env.example` 為 `.env` 並填入對應 API 密鑰：

```bash
cp .env.example .env
```

`.env` 設定說明：
- `LLM_PROVIDER`: 指定 LLM 供應商 (`gemini` 或 `openai`)
- `GEMINI_API_KEY`: Google Gemini API Key
- `OPENAI_API_KEY`: OpenAI API Key
- `FB_PAGE_ID`: Facebook 粉絲專頁 ID
- `FB_PAGE_ACCESS_TOKEN`: Facebook Page Access Token (具有 `pages_manage_posts`, `pages_read_engagement` 權限)
- `DRY_RUN`: 設為 `true` 進行本機輸出測試，不實際發布至 Facebook；測試完成後改為 `false`。

---

## 💻 執行指令說明

### 1. 執行單元測試驗證環境
```bash
python -m unittest discover tests
```

### 2. 手動觸發發布 (Dry-Run 預覽)
```bash
# 執行所有每日任務 (1篇經典 + 2篇最新論文):
python main.py --dry-run

# 僅執行經典論文任務:
python main.py --dry-run --job classic

# 僅執行最新論文任務:
python main.py --dry-run --job latest
```

### 3. 啟動每日自動排程 (Daemon 模式)
```bash
# 每日上午 09:00 自動執行:
python main.py --schedule
```

---

## 🛠️ 未來擴充建議

1. **擴充經典論文庫**：可增修 `data/seed_classic_papers.json` 內容至 100 篇完整清單。
2. **多平台同步**：可於 `src/publishers/` 擴充 Threads / Twitter (X) / Telegram 機器人發布模組。
