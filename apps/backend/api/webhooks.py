from fastapi import APIRouter, Request
import logging
from starlette.responses import JSONResponse
from dependency_injector.wiring import inject, Provide
from apps.backend.handler.github import GithubHandler
from libs.di.container import Container

logger = logging.getLogger(__name__)

WebhooksRouter = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@WebhooksRouter.post("/github")
async def handle_github_webhook(
    request: Request,
) -> JSONResponse:
    handler: GithubHandler = Container.github_handler()
    return await handler.handle_event(request)
