import logging
import time
from typing import Any

from rag.embeddings import generate_embeddings

logger = logging.getLogger(__name__)


class AzureSearchRetriever:
    """
    Retrieves relevant documents from Azure AI Search using hybrid search:
    keyword search + vector search + semantic reranking.
    """

    def __init__(
        self,
        ai_search_client: Any,
        openai_client: Any,
        embedding_model_deployment_name: str,
        semantic_configuration_name: str = "my_semantic_config",
        vector_field_name: str = "content_vector",
    ):
        self.ai_search_client = ai_search_client
        self.openai_client = openai_client
        self.embedding_model_deployment_name = embedding_model_deployment_name
        self.semantic_configuration_name = semantic_configuration_name
        self.vector_field_name = vector_field_name

    def retrieve(self, question: str, top_k: int = 5) -> str:
        """
        Search Azure AI Search and return formatted grounding text
        that can be inserted into the system prompt.
        """

        start_time = time.time()
        logger.info(
            "Running Azure AI Search grounding retrieval: top_k=%s, question_chars=%s, semantic_configuration=%s, vector_field=%s, embedding_model=%s",
            top_k,
            len(question),
            self.semantic_configuration_name,
            self.vector_field_name,
            self.embedding_model_deployment_name,
        )

        if not question.strip():
            logger.warning("Empty question received for grounding retrieval")
            return "No relevant search results found."

        question_vector = generate_embeddings(
            self.openai_client,
            self.embedding_model_deployment_name,
            question,
        )
        logger.info(
            "Generated query embedding for grounding retrieval: vector_dimensions=%s",
            len(question_vector),
        )

        try:
            logger.info("Submitting hybrid semantic/vector search request")
            results = self.ai_search_client.search(
                search_text=question,
                vector_queries=[
                    {
                        "kind": "vector",
                        "vector": question_vector,
                        "fields": self.vector_field_name,
                        "k": top_k,
                    }
                ],
                query_type="semantic",
                semantic_configuration_name=self.semantic_configuration_name,
                select=["title", "content", "category"],
                top=top_k,
                include_total_count=True,
            )

            formatted_results = []

            for index, result in enumerate(results, start=1):
                title = result.get("title", "Unknown title")
                category = result.get("category", "Unknown category")
                content = result.get("content", "")
                search_score = result.get("@search.score")
                reranker_score = result.get("@search.reranker_score")

                logger.info(
                    "Grounding source selected: source=Source %s, title=%s, category=%s, search_score=%s, reranker_score=%s, content_chars=%s",
                    index,
                    title,
                    category,
                    search_score,
                    reranker_score,
                    len(content),
                )

                formatted_results.append(
                    self._format_result(index=index, result=result)
                )

            if not formatted_results:
                logger.info(
                    "No grounding sources found: latency_ms=%s",
                    round((time.time() - start_time) * 1000, 2),
                )
                return "No relevant search results found."

            logger.info(
                "Azure AI Search grounding retrieval completed: result_count=%s, latency_ms=%s",
                len(formatted_results),
                round((time.time() - start_time) * 1000, 2),
            )

            return "\n\n".join(formatted_results)

        except Exception:
            logger.exception("AI Search retrieval failed")
            return "Search failed. No grounding results available."

    def _format_result(self, index: int, result: dict) -> str:
        """
        Format one Azure AI Search result for prompt grounding.
        """

        title = result.get("title", "Unknown title")
        category = result.get("category", "Unknown category")
        content = result.get("content", "")

        search_score = result.get("@search.score")
        reranker_score = result.get("@search.reranker_score")

        return f"""
[Source {index}]
Title: {title}
Category: {category}
Search score: {search_score}
Reranker score: {reranker_score}

Content:
{content}
""".strip()
