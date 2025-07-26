

from http import HTTPStatus
import json
from typing import Dict
from fastapi import APIRouter, HTTPException
import logging
from fastapi import Request
import hashlib
import hmac

from config import settings

logger = logging.getLogger(__name__)

WebhooksRouter = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)

@WebhooksRouter.post("/github")
async def handle_github_webhook(request: Request) -> Dict[str, str]:
  payload = await request.body()
  verify_github_signature(payload, settings.zk_repo_secret, request.headers.get("x-hub-signature-256"))

  decoded_payload = json.loads(payload)
  logger.info(f"GitHub webhook headers: {dict(request.headers)}")
  logger.info(f"GitHub webhook received: {decoded_payload}")
  return {"status": "success"}




def verify_github_signature(payload_body: bytes, secret_token: str, signature_header: str | None) -> None:
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature_header:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="x-hub-signature-256 header is missing!")
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Request signatures didn't match!")