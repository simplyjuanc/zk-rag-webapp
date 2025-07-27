import hashlib
import hmac
from http import HTTPStatus
import logging
from typing import List

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from dependency_injector.wiring import inject, Provide
from apps.backend.services import document_service
from config import settings
from libs.models.third_party.github import (
    GithubWebhookHeaders,
    GithubEventTypes,
    PushEvent,
)
from apps.backend.services.document_service import DocumentService
from libs.pipeline.pipeline import DataPipeline


logger = logging.getLogger(__name__)


class EmbeddingJob:
    def schedule_job(self, files: List[str]) -> None:
        """Schedule a job to process the modified files."""
        # This method should be implemented to handle the scheduling logic
        # For now, we will just log the files
        logger.info(f"Scheduling job for files: {files}")


class GithubHandler:
    @inject
    def __init__(
        self,
        document_service: DocumentService = Provide["Container.document_service"],
        embedding_job: EmbeddingJob = EmbeddingJob(),
    ):
        self.document_service = document_service
        self.embedding_job = embedding_job

    async def handle_event(self, request: Request) -> JSONResponse:
        try:
            webhook_headers = GithubWebhookHeaders.model_validate(dict(request.headers))
        except ValidationError as e:
            logger.error(f"Invalid GitHub webhook headers: {e.errors()}", exc_info=e)
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid webhook headers"
            )
        payload = await request.body()
        self._verify_github_signature(
            payload, settings.zk_repo_secret, webhook_headers.x_hub_signature_256
        )

        if webhook_headers.x_github_event == GithubEventTypes.PING:
            logger.info(f"GitHub ping event received.")
            return JSONResponse(content={"message": "Ping event received."})
        if webhook_headers.x_github_event != GithubEventTypes.PUSH:
            logger.info(
                f"Unsupported GitHub event type: {webhook_headers.x_github_event}"
            )
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Unsupported GitHub event type",
            )
        push_event = PushEvent.model_validate_json(payload)
        await self._handle_github_push_event(push_event)
        return JSONResponse(content={"message": "Push event processed successfully."})

    def _verify_github_signature(
        self, payload_body: bytes, secret_token: str, signature: str | None
    ) -> None:
        """Verify that the payload was sent from GitHub by validating SHA256.

        Raise and return 403 if not authorized.

        Args:
            payload_body: original request body to verify (request.body())
            secret_token: GitHub app webhook token (WEBHOOK_SECRET)
            signature_header: header received from GitHub (x-hub-signature-256)
        """
        if not signature:
            logger.info("Github x-hub-signature-256 header is missing.")
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Github x-hub-signature-256 header is missing.",
            )
        hash_object = hmac.new(
            secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
        )
        expected_signature = "sha256=" + hash_object.hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            logger.info("Github request signature didn't match.")
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Github request signatures didn't match!",
            )

    async def _handle_github_push_event(self, event: PushEvent) -> None:
        commits = event.commits
        all_modified: List[str] = []
        all_removed: List[str] = []
        for commit in commits:
            if commit.added:
                all_modified.extend(commit.added)
            if commit.modified:
                all_modified.extend(commit.modified)
            if commit.removed:
                all_removed.extend(commit.removed)

        md_files_modified = self._extract_unique_md_files(all_modified)
        md_files_removed = self._extract_unique_md_files(all_removed)

        logger.info(
            f"Received push event with {len(commits)} commits, "
            f"{len(md_files_modified)} markdown files to update, "
            f"{len(md_files_removed)} markdown files to be removed."
        )
        if md_files_modified:
            logger.info(f"Processing {len(md_files_modified)} modified markdown files")
            self.embedding_job.schedule_job(md_files_modified)
        if md_files_removed:
            _ = self.document_service.remove_documents_from_gh_path(md_files_removed)
            logger.info(f"Files removed: {md_files_removed}")

    def _extract_unique_md_files(self, all_modified: List[str]) -> List[str]:
        files_modified = list(set(all_modified))
        md_files_modified = [f for f in files_modified if f.endswith(".md")]
        return md_files_modified
