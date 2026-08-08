from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.clients import database_client
from atguigu.engine.builder import build_dialogue_engine
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.repository.dialogue_state_repository import DialogueStateRepository
from atguigu.service.dialogue_service import DialogueService

_dialogue_engine: DialogueEngine | None = None


def init_dialogue_engine():
    global _dialogue_engine
    _dialogue_engine = build_dialogue_engine()


async def get_engine():
    return _dialogue_engine


async def get_session():
    async with database_client.session_factory() as session:
        yield session


async def get_repository(session: AsyncSession = Depends(get_session)):
    return DialogueStateRepository(session)


async def get_dialogue_service(dialogue_engine: DialogueEngine = Depends(get_engine),
                               dialogue_state_repository: DialogueStateRepository = Depends(get_repository)):
    return DialogueService(dialogue_state_repository, dialogue_engine)
