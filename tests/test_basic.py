import os
import unittest
from pathlib import Path
from src.database.db_manager import DBManager
from src.database.models import Paper
from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.llm.summarizer import LLMSummarizer
from src.publishers.facebook_publisher import FacebookPublisher

class TestPaperSnap(unittest.TestCase):
    def setUp(self):
        self.test_db_path = Path("data/test_paper_snap.db")
        if self.test_db_path.exists():
            self.test_db_path.unlink()
        self.db = DBManager(self.test_db_path)

    def tearDown(self):
        if self.test_db_path.exists():
            self.test_db_path.unlink()

    def test_database_init_and_seed(self):
        seed_path = Path("data/seed_classic_papers.json")
        self.db.seed_classic_papers(seed_path)
        
        classic = self.db.get_next_classic_paper()
        self.assertIsNotNone(classic)
        self.assertIn("arxiv_id", classic)

    def test_paper_save_and_publish_status(self):
        paper = Paper(
            arxiv_id="1706.03762",
            title="Attention Is All You Need",
            authors="Ashish Vaswani et al.",
            url="https://arxiv.org/abs/1706.03762",
            paper_type="classic",
            summary="Test Summary",
            problem="Test Problem",
            method="Test Method",
            conclusion="Test Conclusion",
            formatted_post="Test FB Post Content"
        )
        self.db.save_paper(paper)
        self.assertTrue(self.db.is_arxiv_exists("1706.03762"))

    def test_llm_summarizer_fallback(self):
        summarizer = LLMSummarizer()
        paper = {
            "title": "Attention Is All You Need",
            "url": "https://arxiv.org/abs/1706.03762",
            "authors": "Vaswani et al.",
            "description": "Transformer model"
        }
        res = summarizer.summarize_paper(paper, paper_type="classic")
        self.assertIn("summary", res)
        self.assertIn("problem", res)
        self.assertIn("method", res)
        self.assertIn("conclusion", res)
        self.assertIn("formatted_post", res)

    def test_facebook_publisher_dry_run(self):
        publisher = FacebookPublisher()
        publisher.dry_run = True
        res = publisher.publish_post("Test post string")
        self.assertEqual(res.get("status"), "simulated")

if __name__ == "__main__":
    unittest.main()
