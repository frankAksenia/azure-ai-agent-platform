import logging

from rag.embeddings import generate_embeddings

logger = logging.getLogger(__name__)


def get_documents():

    documents = [
        {
            "id": "order-1",
            "title": "Order: 55-inch 4K Smart TV",
            "content": (
                "Order ID: 12345. Customer purchased a 55-inch 4K Ultra HD Smart TV, "
                "brand: Contoso Electronics, model: UltraView 5500, serial number: TV-987654321. "
                "Order date: 2024-11-15. Delivery address: 123 Main St, Sydney, NSW. "
                "The TV features HDR, built-in Wi-Fi, and voice assistant support. "
            ),
            "category": "order",
        },
        {
            "id": "order-2",
            "title": "Order: Mountain Bike",
            "content": (
                "Order ID: 54321. Customer purchased a 21-speed mountain bike, "
                "brand: AdventureCycles, model: TrailBlazer 3000. "
                "Order date: 2023-07-10. Delivery address: 456 Elm St, Melbourne, VIC. "
                "The bike features front suspension and disc brakes."
            ),
            "category": "order",
        },
        {
            "id": "order-3",
            "title": "Order: Espresso Coffee Machine",
            "content": (
                "Order ID: 67890. Customer purchased an espresso coffee machine, "
                "brand: BrewMaster, model: ProBarista X2. "
                "Order date: 2024-01-22. Delivery address: 789 Oak Ave, Brisbane, QLD. "
                "The machine includes a milk frother and digital display."
            ),
            "category": "order",
        },
        {
            "id": "order-4",
            "title": "Order: Yoga Mat",
            "content": (
                "Order ID: 24680. Customer purchased a non-slip yoga mat, "
                "brand: ZenFit, model: ComfortMat 6mm. "
                "Order date: 2022-09-05. Delivery address: 321 Maple Rd, Perth, WA. "
                "The mat is eco-friendly and lightweight."
            ),
            "category": "order",
        },
    ]

    logger.info("Loaded seed grounding documents: document_count=%s", len(documents))
    return documents


def upload_documents(
    ai_search_client,
    openai_client,
    embedding_model_deployment_name,
    index_name,
    documents,
):
    """Upload test documents to the index"""
    logger.info(
        "Preparing grounding documents for upload: index_name=%s, document_count=%s, embedding_model=%s",
        index_name,
        len(documents),
        embedding_model_deployment_name,
    )

    documents_with_vectors = []
    for doc in documents:
        logger.info(
            "Embedding grounding document: document_id=%s, title=%s, category=%s, content_chars=%s",
            doc["id"],
            doc["title"],
            doc["category"],
            len(doc["content"]),
        )

        content_vector = generate_embeddings(
            openai_client, embedding_model_deployment_name, doc["content"]
        )

        documents_with_vectors.append(
            {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "category": doc["category"],
                "content_vector": content_vector,  # Add the vector to the doc
            }
        )

    try:
        logger.info(
            "Uploading grounding documents to Azure AI Search: index_name=%s, document_count=%s",
            index_name,
            len(documents_with_vectors),
        )

        result = ai_search_client.upload_documents(documents=documents_with_vectors)
        uploaded_count = sum(1 for r in result if r.succeeded)

        for item in result:
            logger.info(
                "Grounding document upload result: document_id=%s, succeeded=%s, status_code=%s, error_message=%s",
                item.key,
                item.succeeded,
                item.status_code,
                item.error_message,
            )

        logger.info(
            "Grounding document upload completed: index_name=%s, uploaded_count=%s, document_count=%s",
            index_name,
            uploaded_count,
            len(documents_with_vectors),
        )
        return True
    except Exception:
        logger.exception("Failed to upload documents")
        raise
