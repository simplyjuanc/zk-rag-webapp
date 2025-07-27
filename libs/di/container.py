from apps.backend.handler.github_handler import GithubHandler
from apps.backend.services.document_service import DocumentService
from dependency_injector import containers, providers

from libs.storage.db import get_db_session
from libs.storage.repositories.document import DocumentRepository
from libs.storage.repositories.user import UserRepository
from libs.pipeline.pipeline import DataPipeline
from libs.models.pipeline.config import PipelineConfig
from config import settings


class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()

    # Database
    db_session = providers.Resource(get_db_session)

    # Repositories
    document_repo = providers.Factory(DocumentRepository, session=db_session)
    user_repo = providers.Factory(UserRepository, session=db_session)

    # Pipeline Configuration
    pipeline_config = providers.Singleton(
        PipelineConfig,
        watch_directory="",  # Not used for manual processing
        ollama_url=str(settings.ollama_url),
        embedding_model=settings.llm_embeddings_model,
        chunk_size=1000,
        chunk_overlap=200,
    )

    pipeline = providers.Singleton(DataPipeline, config=pipeline_config)

    # Services
    embedding_service: providers.Factory[DocumentService] = providers.Factory(
        "apps.backend.services.document.DocumentService",
        document_repo=document_repo,
        pipeline=pipeline,
    )

    # Handlers
    github_handler: providers.Factory[GithubHandler] = providers.Factory(
        "apps.backend.handler.github.GithubHandler", embedding_service=embedding_service
    )


container = Container()
# dependency-injector library does not
# recognise pydantic settings from the constructor
container.config.from_dict(settings.model_dump())
