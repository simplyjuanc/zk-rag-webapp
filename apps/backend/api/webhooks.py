from fastapi import APIRouter
import logging
from fastapi import Request

from starlette.responses import JSONResponse

from apps.backend.handler.github import github_handler_injection

logger = logging.getLogger(__name__)

WebhooksRouter = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@WebhooksRouter.post("/github")
async def handle_github_webhook(
    request: Request, handler: github_handler_injection
) -> JSONResponse:
    return await handler.handle_event(request)
