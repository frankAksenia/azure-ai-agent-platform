import logging

from backend.app.core.clients import get_ai_search_client, get_ai_search_index_client
from backend.app.core.settings import AI_SEARCH_INDEX_NAME, EMBEDDING_MODEL_DEPLOYMENT_NAME
from backend.app.rag.document_loader import get_documents, upload_documents
from backend.app.rag.indexer import create_index

logger = logging.getLogger(__name__)


def setup_search_index(openai_client):
    """Create the grounding index if needed and upload its seed documents."""
    logger.info(
        "Setting up Azure AI Search grounding index: index_name=%s, embedding_model=%s",
        AI_SEARCH_INDEX_NAME,
        EMBEDDING_MODEL_DEPLOYMENT_NAME,
    )

    index_result = create_index(
        index_client=get_ai_search_index_client(),
        index_name=AI_SEARCH_INDEX_NAME,
    )
    logger.info("Index setup result: %s", index_result)

    upload_documents(
        ai_search_client=get_ai_search_client(),
        openai_client=openai_client,
        embedding_model_deployment_name=EMBEDDING_MODEL_DEPLOYMENT_NAME,
        index_name=AI_SEARCH_INDEX_NAME,
        documents=get_documents(),
    )
    logger.info(
        "Azure AI Search grounding index setup completed: index_name=%s",
        AI_SEARCH_INDEX_NAME,
    )
