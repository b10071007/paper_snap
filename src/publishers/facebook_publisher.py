import logging
import requests
from typing import Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class FacebookPublisher:
    def __init__(self):
        self.page_id = settings.FB_PAGE_ID
        self.access_token = settings.FB_PAGE_ACCESS_TOKEN
        self.dry_run = settings.DRY_RUN

    def publish_post(self, content: str) -> Dict[str, Any]:
        """
        Publish a text post to Facebook Page Feed.
        If DRY_RUN is True or credentials missing, simulates the publish action.
        """
        if self.dry_run or not self.page_id or not self.access_token:
            logger.info("=" * 60)
            logger.info("[DRY RUN / SIMULATION MODE] Facebook Post Output:")
            logger.info("-" * 60)
            try:
                print(content)
            except Exception:
                print(content.encode('utf-8', errors='ignore').decode('utf-8'))
            logger.info("=" * 60)
            return {"id": "dry_run_simulated_post_id", "status": "simulated"}


        url = f"https://graph.facebook.com/v18.0/{self.page_id}/feed"
        payload = {
            "message": content,
            "access_token": self.access_token
        }

        try:
            response = requests.post(url, data=payload, timeout=30)
            result = response.json()
            if response.status_code == 200 and "id" in result:
                logger.info(f"Successfully posted to Facebook Page. Post ID: {result['id']}")
                return {"id": result["id"], "status": "success"}
            else:
                logger.error(f"Failed to post to Facebook: {response.status_code} - {result}")
                return {"status": "error", "response": result}
        except Exception as e:
            logger.error(f"Exception occurred while posting to Facebook API: {e}")
            return {"status": "exception", "error": str(e)}
