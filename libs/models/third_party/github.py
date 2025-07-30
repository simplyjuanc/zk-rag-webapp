from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, AnyHttpUrl, Field
from datetime import datetime

# Taken from required models from: https://docs.github.com/en/webhooks/webhook-events-and-payloads#push
# There are more fields available in the Github payload


class User(BaseModel):
    login: Optional[str]
    id: Optional[int]
    node_id: Optional[str]
    avatar_url: Optional[AnyHttpUrl]
    html_url: Optional[AnyHttpUrl]
    type: Optional[str]
    site_admin: Optional[bool]


class Repository(BaseModel):
    id: int
    node_id: Optional[str]
    name: str
    full_name: str
    private: bool
    owner: User
    html_url: Optional[AnyHttpUrl]
    description: Optional[str]
    fork: Optional[bool]
    url: Optional[AnyHttpUrl]


class CommitAuthor(BaseModel):
    name: Optional[str]
    email: Optional[str]

    class Config:
        extra = "allow"


class Commit(BaseModel):
    id: Optional[str]
    tree_id: Optional[str]
    distinct: Optional[bool]
    message: Optional[str]
    timestamp: Optional[datetime]
    url: Optional[AnyHttpUrl]
    author: Optional[CommitAuthor]
    committer: Optional[CommitAuthor]
    added: Optional[List[str]]
    removed: Optional[List[str]]
    modified: Optional[List[str]]

    class Config:
        extra = "allow"


class PushEvent(BaseModel):
    ref: str
    before: str
    after: str
    created: Optional[bool]
    deleted: Optional[bool]
    forced: Optional[bool]
    base_ref: Optional[str]
    compare: Optional[AnyHttpUrl]
    commits: List[Commit]
    repository: Repository

    class Config:
        extra = "allow"


class GithubEventTypes(str, Enum):
    PUSH = "push"
    PING = "ping"
    PULL_REQUEST = "pull_request"
    OTHER = "other"

    # If the value is not one of the defined enum values, return OTHER
    @classmethod
    def _missing_(cls, value: object) -> "GithubEventTypes":
        return cls.OTHER


class GithubWebhookHeaders(BaseModel):
    x_github_hook_id: str = Field(alias="x-github-hook-id")
    x_github_event: GithubEventTypes = Field(alias="x-github-event")
    x_github_delivery: str = Field(alias="x-github-delivery")
    x_hub_signature: Optional[str] = Field(default=None, alias="x-hub-signature")
    x_hub_signature_256: Optional[str] = Field(
        default=None, alias="x-hub-signature-256"
    )
    user_agent: str = Field(alias="user-agent")
    x_github_hook_installation_target_type: Optional[str] = Field(
        default=None, alias="x-github-hook-installation-target-type"
    )
    x_github_hook_installation_target_id: Optional[str] = Field(
        default=None, alias="x-github-hook-installation-target-id"
    )

    class Config:
        validate_by_name = True
