import logging
from azure.ai.contentsafety.models import AnalyzeTextOptions

logger = logging.getLogger(__name__)


class ContentSafetyService:
    def __init__(self, client, config: dict):
        self.client = client
        self.severity_threshold = config["content_safety"]["severity_threshold"]

    def is_text_safe(self, input_text: str) -> bool:
        analysis_request = AnalyzeTextOptions(text=input_text)
        analysis_result = self.client.analyze_text(analysis_request)

        categories = getattr(analysis_result, "categories_analysis", None)
        if categories is None and isinstance(analysis_result, dict):
            categories = analysis_result.get("categoriesAnalysis") or analysis_result.get("categories_analysis")

        severities = {}
        for category in categories or []:
            if isinstance(category, dict):
                category_name = category.get("category")
                severity = category.get("severity")
            else:
                category_name = getattr(category, "category", None)
                severity = getattr(category, "severity", None)

            if category_name is not None and severity is not None:
                severities[category_name] = severity

        for category, severity in severities.items():
            if severity > self.severity_threshold:
                logger.info(f"Blocked: {category.upper()} content severity {severity}")
                return False

        return True
