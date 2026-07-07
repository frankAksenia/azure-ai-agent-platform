import logging
import time

logger = logging.getLogger(__name__)


def generate_embeddings(openai_client, embedding_model_deployment_name, text):
    """Generate a vector embedding for the given text."""
    start_time = time.time()
    logger.info(
        "Generating embedding: embedding_model=%s, input_chars=%s",
        embedding_model_deployment_name,
        len(text),
    )

    response = openai_client.embeddings.create(
        input=text, model=embedding_model_deployment_name
    )
    embedding = response.data[0].embedding

    logger.info(
        "Embedding generated: embedding_model=%s, dimensions=%s, latency_ms=%s",
        embedding_model_deployment_name,
        len(embedding),
        round((time.time() - start_time) * 1000, 2),
    )

    return embedding
