import logging
from azure.ai.contentsafety.models import AnalyzeTextOptions

logger = logging.getLogger(__name__)

class ContentSafetyService:
    def __init__(self, client, severity_threshold: int):
        self.client = client
        self.severity_threshold = severity_threshold

    def is_text_safe(self, input_text: str) -> bool:
        analysis_request = AnalyzeTextOptions(text=input_text)
        analysis_result = self.client.analyze_text(analysis_request)

        severities = {
            category["category"]: category["severity"]
            for category in analysis_result["categoriesAnalysis"]
        }

        for category, severity in severities.items():
            if severity > self.severity_threshold:
                logger.info(
                    f"Blocked: {category.upper()} content severity {severity}")
                return False

        return True
