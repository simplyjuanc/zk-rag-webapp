import hashlib
import hmac
from http import HTTPStatus
import logging
from typing import List

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from dependency_injector.wiring import inject, Provide
from config import settings
from libs.models.third_party.github import (
    GithubWebhookHeaders,
    GithubEventTypes,
    PushEvent,
)
from apps.backend.services.document import DocumentService


logger = logging.getLogger(__name__)


class GithubHandler:
    @inject
    def __init__(
        self,
        embedding_service: DocumentService = Provide["Container.embedding_service"],
    ):
        self.embedding_service = embedding_service

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

        files_modified = list(set(all_modified))
        files_removed = list(set(all_removed))
        md_files_modified = [f for f in files_modified if f.endswith(".md")]
        md_files_removed = [f for f in files_removed if f.endswith(".md")]

        logger.info(
            f"Received push event with {len(commits)} commits, "
            f"{len(md_files_modified)} markdown files modified, "
            f"{len(md_files_removed)} markdown files removed."
        )
        if md_files_modified:
            logger.info(f"Processing {len(md_files_modified)} modified markdown files")
            # processed_files = await self.pipeline_service.process_files(md_files_modified)
            # logger.info(f"Successfully processed {len(processed_files)} files: {processed_files}")

        # Handle removed files (you might want to delete them from the database)
        if md_files_removed:
            logger.info(f"Files removed: {md_files_removed}")
            # TODO: Implement deletion from database if needed
            # await self.embedding_service.remove_files(md_files_removed)
