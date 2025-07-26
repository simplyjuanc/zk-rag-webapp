import hashlib
import hmac
from http import HTTPStatus
import logging
from typing import Annotated, Set

from fastapi import HTTPException, Request
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from libs.models.third_party.github import (
    GithubWebhookHeaders,
    GithubEventTypes,
    PushEvent,
)

from config import settings

logger = logging.getLogger(__name__)


class GithubHandler:
    async def handle_event(self, request: Request) -> JSONResponse:
        try:
            webhook_headers = GithubWebhookHeaders.model_validate(dict(request.headers))
        except ValidationError as e:
            logger.error(f"Invalid GitHub webhook headers: {e.errors()}", exc_info=e)
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid webhook headers"
            )

        payload = await request.body()
        self.__verify_github_signature(
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
        self.__handle_github_push_event(push_event)

        return JSONResponse(content={"message": "Push event processed successfully."})

    def __verify_github_signature(
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

    def __handle_github_push_event(self, event: PushEvent) -> None:
        commits = event.commits
        files_modified: Set[str] = set()
        files_removed: Set[str] = set()
        for commit in commits:
            if commit.added:
                files_modified.update(commit.added)
            if commit.removed:
                files_removed.update(commit.removed)
            if commit.modified:
                files_modified.update(commit.modified)

        timestamps = [
            commit.timestamp for commit in commits if commit.timestamp is not None
        ]
        min_timestamp = min(timestamps) if timestamps else None


def get_github_handler() -> GithubHandler:
    return GithubHandler()


github_handler_injection = Annotated[GithubHandler, Depends(get_github_handler)]
