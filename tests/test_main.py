import importlib
import inspect
import sys
import types
from dataclasses import dataclass

import pytest


class FakeDepends:
    def __init__(self, dependency):
        self.dependency = dependency


class FakeHTTPException(Exception):
    def __init__(self, status_code, detail=None, headers=None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}


class FakeStatus:
    HTTP_401_UNAUTHORIZED = 401


class FakeFastAPI:
    def __init__(self, *args, **kwargs):
        self.routes = {}
        self.middlewares = []

    def add_middleware(self, middleware, **kwargs):
        self.middlewares.append((middleware, kwargs))

    def include_router(self, router):
        self.routes.update(router.routes)

    def _register(self, method, path, response_model=None):
        def decorator(func):
            self.routes[(method, path)] = {
                "func": func,
                "response_model": response_model,
            }
            return func

        return decorator

    def get(self, path, response_model=None):
        return self._register("GET", path, response_model=response_model)

    def post(self, path, response_model=None):
        return self._register("POST", path, response_model=response_model)

    def delete(self, path, response_model=None):
        return self._register("DELETE", path, response_model=response_model)

    def websocket(self, path):
        return self._register("WEBSOCKET", path)


class FakeStreamingResponse:
    def __init__(self, content, media_type=None, headers=None):
        self.content = list(content)
        self.media_type = media_type
        self.headers = headers or {}


class FakeUploadFile:
    pass


class FakeWebSocket:
    pass


class FakeWebSocketDisconnect(Exception):
    pass


class FakeRequest:
    pass


@dataclass
class UserCreate:
    email: str
    password: str


@dataclass
class UserLogin:
    email: str
    password: str


@dataclass
class UserResponse:
    email: str
    hashed_password: str = ""
    id: int = 0


@dataclass
class Token:
    access_token: str
    token_type: str


@dataclass
class ChatRequest:
    message: str
    conversation_id: int | None = None


@dataclass
class ChatResponse:
    response: str
    conversation_id: int
    message_id: int


@dataclass
class MessageResponse:
    id: int


@dataclass
class ConversationResponse:
    id: int


@dataclass
class UploadResponse:
    filename: str
    path: str


class FakeUser:
    email = "email"

    def __init__(self, email, hashed_password, id=1):
        self.email = email
        self.hashed_password = hashed_password
        self.id = id


class FakeConversation:
    id = 1
    user_id = 1


class FakeMessage:
    id = 1


class FakeRateLimitMiddleware:
    pass


class FakeRagPipeline:
    def add_document(self, text, metadata=None):
        return "doc-1"

    def search(self, query, top_k=3):
        return [{"text": f"result for {query}", "score": 0.9}]

    def add_documents_batch(self, texts, metadatas=None):
        return [f"doc-{idx}" for idx, _ in enumerate(texts, start=1)]


class FakeQuery:
    def __init__(self, existing_user=None):
        self.existing_user = existing_user

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.existing_user


class FakeDB:
    def __init__(self, existing_user=None):
        self.existing_user = existing_user
        self.added = []

    def query(self, _model):
        return FakeQuery(existing_user=self.existing_user)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        if not getattr(obj, "id", None):
            obj.id = 123


@pytest.fixture
def main_module(monkeypatch, tmp_path):
    fastapi_module = types.ModuleType("fastapi")
    fastapi_module.FastAPI = FakeFastAPI
    fastapi_module.APIRouter = FakeFastAPI
    fastapi_module.Depends = lambda dependency: FakeDepends(dependency)
    fastapi_module.HTTPException = FakeHTTPException
    fastapi_module.status = FakeStatus
    fastapi_module.UploadFile = FakeUploadFile
    fastapi_module.File = lambda *args, **kwargs: ("file", args, kwargs)
    fastapi_module.WebSocket = FakeWebSocket
    fastapi_module.WebSocketDisconnect = FakeWebSocketDisconnect
    fastapi_module.Request = FakeRequest
    monkeypatch.setitem(sys.modules, "fastapi", fastapi_module)

    cors_module = types.ModuleType("fastapi.middleware.cors")
    cors_module.CORSMiddleware = type("CORSMiddleware", (), {})
    monkeypatch.setitem(sys.modules, "fastapi.middleware.cors", cors_module)

    responses_module = types.ModuleType("fastapi.responses")
    responses_module.StreamingResponse = FakeStreamingResponse
    responses_module.JSONResponse = dict
    monkeypatch.setitem(sys.modules, "fastapi.responses", responses_module)

    config_module = types.ModuleType("app.core.config")
    config_module.UPLOAD_DIR = str(tmp_path / "uploads")
    config_module.JWT_EXPIRATION_MINUTES = 30
    config_module.OPENROUTER_API_KEY = ""
    config_module.GOOGLE_SEARCH_API_KEY = ""
    config_module.GOOGLE_CX = ""
    monkeypatch.setitem(sys.modules, "app.core.config", config_module)

    db_module = types.ModuleType("app.core.database")
    db_module.init_db = lambda: None
    db_module.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.core.database", db_module)

    models_module = types.ModuleType("app.models.entities")
    models_module.User = FakeUser
    models_module.Conversation = FakeConversation
    models_module.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "app.models.entities", models_module)

    models_package = types.ModuleType("app.models")
    models_package.User = FakeUser
    models_package.Conversation = FakeConversation
    models_package.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "app.models", models_package)

    schemas_module = types.ModuleType("app.schemas")
    schemas_module.UserCreate = UserCreate
    schemas_module.UserLogin = UserLogin
    schemas_module.UserResponse = UserResponse
    schemas_module.Token = Token
    schemas_module.ChatRequest = ChatRequest
    schemas_module.ChatResponse = ChatResponse
    schemas_module.MessageResponse = MessageResponse
    schemas_module.ConversationResponse = ConversationResponse
    schemas_module.UploadResponse = UploadResponse
    monkeypatch.setitem(sys.modules, "app.schemas", schemas_module)
    monkeypatch.setitem(sys.modules, "app.schemas.api", schemas_module)

    security_module = types.ModuleType("app.core.security")
    security_module.get_password_hash = lambda password: f"hashed::{password}"
    security_module.authenticate_user = lambda db, email, password: None
    security_module.create_access_token = lambda data, expires_delta=None: "token-123"
    security_module.get_current_user = lambda: None
    monkeypatch.setitem(sys.modules, "app.core.security", security_module)

    agent_module = types.ModuleType("app.agents")
    agent_module.agent = lambda query: f"agent::{query}"
    monkeypatch.setitem(sys.modules, "app.agents", agent_module)

    repository_module = types.ModuleType("app.repositories.conversation_repository")
    repository_module.get_or_create_conversation = lambda db, user_id, conversation_id=None: types.SimpleNamespace(id=11)
    repository_module.add_message = lambda db, conversation_id, role, content: types.SimpleNamespace(
        id=22 if role == "assistant" else 21,
        role=role,
        content=content,
    )
    repository_module.get_conversation_history = lambda db, conversation_id, limit=10: [
        types.SimpleNamespace(role="user", content="hi")
    ]
    repository_module.get_user_conversations = lambda db, user_id: []
    repository_module.delete_conversation = lambda db, user_id, conversation_id: True
    monkeypatch.setitem(sys.modules, "app.repositories.conversation_repository", repository_module)

    rag_module = types.ModuleType("app.integrations.rag_pipeline")
    rag_module.rag_pipeline = FakeRagPipeline()
    monkeypatch.setitem(sys.modules, "app.integrations.rag_pipeline", rag_module)

    tts_module = types.ModuleType("app.integrations.tts_client")
    tts_module.text_to_speech = lambda text, lang="en": b"audio-bytes"
    monkeypatch.setitem(sys.modules, "app.integrations.tts_client", tts_module)

    speech_module = types.ModuleType("app.integrations.speech_client")
    speech_module.speech_to_text = lambda audio_data: "transcribed"
    monkeypatch.setitem(sys.modules, "app.integrations.speech_client", speech_module)

    rate_limit_module = types.ModuleType("app.core.rate_limit")
    rate_limit_module.RateLimitMiddleware = FakeRateLimitMiddleware
    monkeypatch.setitem(sys.modules, "app.core.rate_limit", rate_limit_module)

    search_module = types.ModuleType("app.integrations.search_client")
    search_module.google_search = lambda query, num_results=3: [f"{query}-{idx}" for idx in range(num_results)]
    monkeypatch.setitem(sys.modules, "app.integrations.search_client", search_module)

    api_client_module = types.ModuleType("app.integrations.api_client")
    api_client_module.call_api = lambda url, method="GET", headers=None, data=None: {"url": url, "method": method}
    monkeypatch.setitem(sys.modules, "app.integrations.api_client", api_client_module)

    for module_name in [
        "app.main",
        "app.core.factory",
        "app.agents.runtime",
        "app.routers.auth",
        "app.routers.chat",
        "app.routers.health",
        "app.routers.rag",
        "app.routers.tools",
        "app.services.auth_service",
        "app.services.chat_service",
        "app.services.file_service",
        "app.services.rag_service",
        "app.services.tool_service",
    ]:
        sys.modules.pop(module_name, None)
    return importlib.import_module("app.main")


def test_root(main_module):
    assert main_module.root() == {"status": "ok", "message": "Chatbot API is running"}


def test_health(main_module):
    assert main_module.health_check() == {"status": "healthy"}


def test_signup(main_module):
    db = FakeDB()
    user = main_module.signup(UserCreate(email="test@example.com", password="testpass123"), db)
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed::testpass123"
    assert db.added == [user]


def test_login(main_module, monkeypatch):
    monkeypatch.setitem(
        main_module.login.__globals__,
        "login_user",
        lambda email, password, db: {"access_token": "token-abc", "token_type": "bearer"},
    )

    response = main_module.login(UserLogin(email="login_test@example.com", password="testpass123"), FakeDB())
    assert response == {"access_token": "token-abc", "token_type": "bearer"}


def test_signup_and_login_with_long_password(main_module, monkeypatch):
    password = "a" * 100
    created_user = main_module.signup(UserCreate(email="long_password_test@example.com", password=password), FakeDB())
    monkeypatch.setitem(
        main_module.login.__globals__,
        "login_user",
        lambda email, raw_password, db: {"access_token": "token-123", "token_type": "bearer"},
    )

    response = main_module.login(UserLogin(email=created_user.email, password=password), FakeDB())
    assert response["token_type"] == "bearer"
    assert response["access_token"] == "token-123"


def test_chat_unauthorized(main_module):
    signature = inspect.signature(main_module.chat)
    current_user_default = signature.parameters["current_user"].default
    assert isinstance(current_user_default, FakeDepends)
    assert current_user_default.dependency is main_module.chat.__globals__["get_current_user"]


def test_search(main_module):
    response = main_module.search(query="test")
    assert response == {"results": ["test-0", "test-1", "test-2"]}
