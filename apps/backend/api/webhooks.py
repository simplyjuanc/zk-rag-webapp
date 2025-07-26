

from calendar import c
from http import HTTPStatus
import json
from typing import Dict
from fastapi import APIRouter, HTTPException
import logging
from fastapi import Request
import hashlib
import hmac

from pydantic import BaseModel, ValidationError

from config import settings
from libs.models.third_party.github import GitHubWebhookHeaders, GithubEventTypes, PushEvent

logger = logging.getLogger(__name__)

WebhooksRouter = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)

@WebhooksRouter.post("/github")
async def handle_github_webhook(request: Request) -> Dict[str, str]:
  try:
    webhook_headers = GitHubWebhookHeaders.model_validate(dict(request.headers))
  except ValidationError as e:
    logger.error(f"Invalid GitHub webhook headers: {e.errors()}", exc_info=e)
    raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid webhook headers")

  payload = await request.body()
  verify_github_signature(payload, settings.zk_repo_secret, webhook_headers.x_hub_signature_256)


  if webhook_headers.x_github_event == GithubEventTypes.PING:
    logger.info(f"GitHub ping event received.")
    return {"message": "Ping event received"}

  if webhook_headers.x_github_event != GithubEventTypes.PUSH:
    logger.info(f"Unsupported GitHub event type: {webhook_headers.x_github_event}")
    raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Unsupported GitHub event type")

  decoded_payload = PushEvent.model_validate_json(payload)

  """ Handle the GitHub webhook payload.
   Need to:
    - Grab all the `commits` in the object -> grab timestamp and `added`, `removed`, `modified` files
    - Find the earliest timestamp commit list

  """

  logger.info(f"GitHub webhook headers: {dict(request.headers)}")
  logger.info(f"GitHub webhook received: {decoded_payload}")
  return decoded_payload.model_dump()




def verify_github_signature(payload_body: bytes, secret_token: str, signature: str | None) -> None:
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature:
        logger.info("Github x-hub-signature-256 header is missing.")
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Github x-hub-signature-256 header is missing.")
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        logger.info("Github request signature didn't match.")
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Github request signatures didn't match!")
