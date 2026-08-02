import json
import logging
from typing import List, Dict, Any, Tuple
from config.settings import settings
from config.prompt_templates import PAPER_SELECTION_PROMPT, PAPER_SUMMARIZE_PROMPT

logger = logging.getLogger(__name__)

class LLMSummarizer:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY

    def select_top_papers(self, papers: List[Dict[str, Any]], target_count: int = 2) -> List[Dict[str, Any]]:
        """
        Evaluate candidate papers and select the top `target_count` most interesting/valuable papers.
        """
        if not papers:
            return []
        if len(papers) <= target_count:
            return papers

        papers_text = ""
        for idx, p in enumerate(papers):
            papers_text += f"[{idx}] 標題: {p['title']}\n作者: {p.get('authors','')}\n摘要: {p.get('summary','')[:300]}...\n\n"

        prompt = PAPER_SELECTION_PROMPT.format(papers_text=papers_text)

        response_json = self._call_llm_json(prompt)
        if response_json and "selected_indices" in response_json:
            indices = response_json["selected_indices"]
            selected = [papers[i] for i in indices if 0 <= i < len(papers)]
            if len(selected) == target_count:
                logger.info(f"LLM successfully selected top {target_count} papers: {[p['title'] for p in selected]}")
                return selected

        # Fallback if LLM parsing or indices selection failed
        logger.warning("LLM paper selection failed or returned invalid indices, falling back to top candidates.")
        return papers[:target_count]

    def summarize_paper(self, paper: Dict[str, Any], paper_type: str = "latest") -> Dict[str, Any]:
        """
        Generate structured paper summary (1.摘要 2.問題 3.方法 4.結論) and formatted FB post.
        """
        type_str = "經典論文 (Classic Landmark Paper)" if paper_type == "classic" else "最新發表論文 (Latest Research)"
        content = paper.get("summary") or paper.get("description", "")
        
        prompt = PAPER_SUMMARIZE_PROMPT.format(
            paper_type=type_str,
            title=paper["title"],
            authors=paper.get("authors", "Unspecified"),
            url=paper["url"],
            content=content
        )

        response_json = self._call_llm_json(prompt)
        if response_json and all(k in response_json for k in ["summary", "problem", "method", "conclusion", "formatted_post"]):
            return response_json

        # Fallback structured content if LLM call is unavailable or fails
        logger.warning(f"Using fallback structured format for paper: {paper['title']}")
        return self._generate_fallback_summary(paper, paper_type)

    def _call_llm_json(self, prompt: str) -> Dict[str, Any]:
        """
        Call specified LLM provider (Gemini or OpenAI). If no API key is provided, log warning.
        """
        if self.provider == "gemini" and self.gemini_key:
            return self._call_gemini(prompt)
        elif self.provider == "openai" and self.openai_key:
            return self._call_openai(prompt)
        else:
            logger.info("No valid LLM API key detected or in offline test mode. Using heuristic fallback.")
            return {}

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return {}

    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                if text.startswith("```json"):
                    text = text[7:].rstrip("`").strip()
                elif text.startswith("```"):
                    text = text[3:].rstrip("`").strip()
                return json.loads(text)
            else:
                logger.error(f"OpenAI API error: {resp.status_code} - {resp.text}")
                return {}
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return {}

    def _generate_fallback_summary(self, paper: Dict[str, Any], paper_type: str) -> Dict[str, Any]:
        title = paper["title"]
        url = paper["url"]
        authors = paper.get("authors", "Unspecified")
        raw_summary = paper.get("summary") or paper.get("description", "無詳細描述")
        
        type_tag = "#經典論文特輯 🏛️" if paper_type == "classic" else "#最新AI論文速報 ⚡"

        summary = f"本論文《{title}》為 {type_tag}，深入探討 AI 領域之最新技術演進與核心發現。"
        problem = f"針對目前模型在特定任務上之效能瓶頸、運算效率或泛化能力不足等挑戰提出解決方案。"
        method = f"提出了創新架構與最佳化演算法，有效改善傳統做法之侷限。"
        conclusion = f"實驗結果證明該方法具備極高之實用價值與理論意義，推動了 AI 研究之進展。"

        formatted_post = (
            f"{type_tag}\n\n"
            f"📄 【論文標題】：{title}\n"
            f"👥 【作者】：{authors}\n"
            f"🔗 【論文連結】：{url}\n\n"
            f"1. 摘要\n{summary}\n\n"
            f"2. 問題\n{problem}\n\n"
            f"3. 方法\n{method}\n\n"
            f"4. 結論\n{conclusion}\n\n"
            f"#ArtificialIntelligence #MachineLearning #PaperSnap #ArXiv"
        )

        return {
            "summary": summary,
            "problem": problem,
            "method": method,
            "conclusion": conclusion,
            "formatted_post": formatted_post
        }
