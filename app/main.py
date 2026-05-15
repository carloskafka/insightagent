from app.core.factory import create_app
from app.routers.auth import get_me, login, signup
from app.routers.chat import (
    chat,
    delete_conv,
    get_conversation,
    list_conversations,
    text_to_speech_endpoint,
    upload_file,
    voice_message,
    websocket_endpoint,
)
from app.routers.health import health_check, root
from app.routers.rag import add_to_rag, search_rag
from app.routers.tools import api_call, search


app = create_app()
