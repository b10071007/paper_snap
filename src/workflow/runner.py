import logging
from typing import Dict, Any
from config.settings import settings
from src.database.db_manager import DBManager
from src.database.models import Paper
from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.llm.summarizer import LLMSummarizer
from src.publishers.facebook_publisher import FacebookPublisher

logger = logging.getLogger(__name__)

class WorkflowRunner:
    def __init__(self):
        self.db = DBManager(settings.DB_PATH)
        self.db.seed_classic_papers(settings.CLASSIC_SEED_PATH)
        self.fetcher = ArxivFetcher()
        self.summarizer = LLMSummarizer()
        self.publisher = FacebookPublisher()

    def run_classic_paper_job(self) -> bool:
        """
        Process and post 1 classic paper daily.
        """
        logger.info("Starting Daily Classic Paper Job...")
        classic = self.db.get_next_classic_paper()
        if not classic:
            logger.warning("No unprocessed classic papers found in classic_queue.")
            return False

        arxiv_id = classic["arxiv_id"]
        logger.info(f"Processing Classic Paper: {classic['title']} (ArXiv ID: {arxiv_id})")

        # Summarize paper
        summary_res = self.summarizer.summarize_paper(classic, paper_type="classic")

        # Create Paper model & save
        paper = Paper(
            arxiv_id=arxiv_id,
            title=classic["title"],
            authors=classic.get("authors", ""),
            url=classic["url"],
            paper_type="classic",
            summary=summary_res.get("summary"),
            problem=summary_res.get("problem"),
            method=summary_res.get("method"),
            conclusion=summary_res.get("conclusion"),
            formatted_post=summary_res.get("formatted_post")
        )
        self.db.save_paper(paper)

        # Publish to Facebook
        pub_res = self.publisher.publish_post(summary_res["formatted_post"])
        if pub_res.get("status") in ("success", "simulated"):
            self.db.mark_published(arxiv_id)
            self.db.mark_classic_processed(arxiv_id)
            logger.info(f"Classic Paper Job completed for: {classic['title']}")
            return True
        else:
            logger.error(f"Classic Paper post failed for: {classic['title']}")
            return False

    def run_latest_papers_job(self) -> int:
        """
        Fetch latest 10 papers, filter out already published ones, pick top 2, and post them.
        """
        logger.info("Starting Daily Latest Papers Job...")
        raw_papers = self.fetcher.fetch_latest_papers(max_results=10)
        
        # Filter out existing papers
        candidates = [p for p in raw_papers if not self.db.is_arxiv_exists(p["arxiv_id"])]
        logger.info(f"Fetched {len(raw_papers)} papers, found {len(candidates)} new candidates.")

        if not candidates:
            logger.info("No new unpublished papers found today.")
            return 0

        # Select top 2 papers using LLM
        selected_papers = self.summarizer.select_top_papers(candidates, target_count=2)
        logger.info(f"Selected {len(selected_papers)} papers to publish.")

        published_count = 0
        for p in selected_papers:
            arxiv_id = p["arxiv_id"]
            logger.info(f"Summarizing Latest Paper: {p['title']}")
            
            summary_res = self.summarizer.summarize_paper(p, paper_type="latest")
            
            paper = Paper(
                arxiv_id=arxiv_id,
                title=p["title"],
                authors=p.get("authors", ""),
                url=p["url"],
                paper_type="latest",
                summary=summary_res.get("summary"),
                problem=summary_res.get("problem"),
                method=summary_res.get("method"),
                conclusion=summary_res.get("conclusion"),
                formatted_post=summary_res.get("formatted_post")
            )
            self.db.save_paper(paper)

            # Publish post
            pub_res = self.publisher.publish_post(summary_res["formatted_post"])
            if pub_res.get("status") in ("success", "simulated"):
                self.db.mark_published(arxiv_id)
                published_count += 1
                logger.info(f"Successfully published latest paper: {p['title']}")

        logger.info(f"Latest Papers Job finished. Total published: {published_count}")
        return published_count

    def run_all_daily(self):
        logger.info("=== Starting Daily Paper Snap Workflow ===")
        self.run_classic_paper_job()
        self.run_latest_papers_job()
        logger.info("=== Daily Paper Snap Workflow Completed ===")
