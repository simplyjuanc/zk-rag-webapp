from http import HTTPStatus
from fastapi import APIRouter, BackgroundTasks, Request
import logging
from starlette.responses import JSONResponse
from dependency_injector.wiring import inject, Provide
from apps.backend.handler.github_handler import GithubHandler
from libs.di.container import Container

logger = logging.getLogger(__name__)

WebhooksRouter = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@WebhooksRouter.post("/github", status_code=HTTPStatus.ACCEPTED)
async def handle_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> None:
    handler: GithubHandler = Container.github_handler()
    background_tasks.add_task(handler.handle_event, request)
