from apps.backend.handler.github_handler import GithubHandler
from apps.backend.services.embedding_service import EmbeddingService
from apps.backend.services.document_service import DocumentService
from dependency_injector import containers, providers

from libs.clients.github_client import GithubClient
from libs.storage.db import get_db_session
from libs.storage.repositories.document import DocumentRepository
from libs.storage.repositories.user import UserRepository
from libs.pipeline.pipeline import DataPipeline
from libs.pipeline.embedder import DocumentEmbedder, SimilarityCalculator
from libs.models.pipeline.config import PipelineConfig
from config import settings


class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()

    # Database
    db_session = providers.Resource(get_db_session)

    # Repositories
    document_repo = providers.Singleton(DocumentRepository, session=db_session)
    user_repo = providers.Singleton(UserRepository, session=db_session)

    # Clients
    github_client: providers.Factory[GithubClient] = providers.Factory(
        GithubClient,
    )

    # Services
    embedding_service: providers.Singleton[EmbeddingService] = providers.Singleton(
        EmbeddingService,
    )
    document_service: providers.Singleton[DocumentService] = providers.Singleton(
        DocumentService,
        document_repo=document_repo,
        embedding_service=embedding_service,
    )

    # Handlers
    github_handler: providers.Singleton[GithubHandler] = providers.Singleton(
        GithubHandler,
        document_service=document_service,
        embedding_service=embedding_service,
        github_client=github_client,
    )

    # Pipeline
    pipeline_config = providers.Singleton(
        PipelineConfig,
        watch_directory="assets",
        ollama_url=str(settings.ollama_url),
        embedding_model=settings.llm_embeddings_model,
        chunk_size=1000,
        chunk_overlap=200,
    )

    document_embedder = providers.Singleton(
        DocumentEmbedder,
        embedder=embedding_service,
    )
    similarity_calculator = providers.Singleton(SimilarityCalculator)

    pipeline = providers.Singleton(
        DataPipeline,
        config=pipeline_config,
        document_embedder=document_embedder,
        similarity_calculator=similarity_calculator,
    )


container = Container()
# assignment needed because dependency-injector
# does not recognise pydantic settings from the constructor
container.config.from_dict(settings.model_dump())
