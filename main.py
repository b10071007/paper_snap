import argparse
import io
import logging
import sys
import time
from config.settings import settings
from src.workflow.runner import WorkflowRunner

# Ensure Windows stdout handles UTF-8 (emojis, Chinese characters) properly
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("PaperSnapMain")


def main():
    parser = argparse.ArgumentParser(description="Paper Snap - ArXiv AI Paper Daily Summary & FB Bot")
    parser.add_argument(
        "--job",
        choices=["all", "classic", "latest"],
        default="all",
        help="Specify which job to run: classic (1 classic paper), latest (2 latest papers), or all (default)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry run mode (simulates Facebook posting without calling Graph API)."
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run in daemon/schedule mode (runs daily at 09:00 AM)."
    )
    args = parser.parse_args()

    if args.dry_run:
        settings.DRY_RUN = True
        logger.info("Dry-run mode explicitly enabled via CLI flag.")

    runner = WorkflowRunner()

    if args.schedule:
        try:
            import schedule
        except ImportError:
            logger.error("Package 'schedule' is not installed. Please run: pip install schedule")
            sys.exit(1)

        logger.info("Starting Paper Snap Scheduler Daemon... Scheduled daily at 09:00 AM.")
        schedule.every().day.at("09:00").do(runner.run_all_daily)
        
        # Execute once immediately on startup
        runner.run_all_daily()

        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        if args.job == "classic":
            runner.run_classic_paper_job()
        elif args.job == "latest":
            runner.run_latest_papers_job()
        else:
            runner.run_all_daily()

if __name__ == "__main__":
    main()

