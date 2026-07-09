import logging

from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchableField,
    SearchField,
    SearchIndex,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
)

logger = logging.getLogger(__name__)

def create_index(index_client, index_name):
    logger.info(f"Creating index '{index_name}'...")

    # Define the index schema
    fields = [
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="title", type="Edm.String"),
        SearchableField(name="content", type="Edm.String"),
        SimpleField(name="category", type="Edm.String", filterable=True),
        SearchField(
            name="content_vector",
            type="Collection(Edm.Single)",
            vector_search_dimensions=1536,
            vector_search_profile_name="my_vector_profile",
        ),
    ]

    # Configure the vector search algorithm
    # This example uses HNSW (Hierarchical Navigable Small World) algorithm for efficient vector similarity search.
    # The vector search profile specifies which algorithm configuration to use for vector search queries.
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="my_hnsw_config")],
        profiles=[
            VectorSearchProfile(
                name="my_vector_profile", algorithm_configuration_name="my_hnsw_config"
            )
        ],
    )

    # Configure semantic search with prioritized fields for better relevance when using semantic queries.
    # This configuration tells Azure AI Search to prioritize the 'title' field and then the 'content' field when reranking results for semantic search queries.
    # You can adjust the prioritized fields based on your data and search relevance needs.
    # The semantic configuration is required to enable semantic search capabilities, which use language models to understand user intent and context for improved search relevance.
    # Without this configuration, semantic search queries will not be able to rerank results based on the content of the fields, and you will only get keyword-based search results.
    semantic_config = SemanticConfiguration(
        name="my_semantic_config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    semantic_search = SemanticSearch(
        # Pass your config in a SemanticSearch wrapper
        configurations=[semantic_config]
    )

    # Create the index with the new vector configuration and semantic configuration
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )

    # Check if the index already exists
    try:
        index_client.get_index(index_name)
        logger.info(f"Index '{index_name}' already exists. Skipping creation.")
        return "Index already exists"
    except ResourceNotFoundError:
        index_client.create_index(index)
        logger.info("Index '%s' created successfully", index_name)
        return "Index created"
