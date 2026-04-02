import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.api import memory


class MemoryApiTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_list_long_term_memories_filters_by_session(self):
        records = [
            SimpleNamespace(id=1, session_id=1),
            SimpleNamespace(id=2, session_id=2),
            SimpleNamespace(id=3, session_id=1),
        ]

        with patch("app.api.memory.MemoryDAO.list_all", new=AsyncMock(return_value=records)):
            result = await memory.list_long_term_memories(db=object(), limit=50, session_id=1)

        self.assertEqual([item.id for item in result], [1, 3])

    async def test_create_long_term_memory_passes_session_id(self):
        payload = memory.LongTermMemoryCreate(
            session_id=8,
            key="k",
            content="hello",
            importance=0.6,
            source="manual",
        )
        created = SimpleNamespace(id=99)

        fake_task = object()
        with (
            patch("app.api.memory.MemoryDAO.create", new=AsyncMock(return_value=created)) as create_memory,
            patch("app.api.memory.index_long_term_memory_embedding", new=AsyncMock()) as index_embedding,
            patch(
                "app.api.memory.asyncio.create_task",
                side_effect=lambda coro: (coro.close(), fake_task)[1],
            ) as create_task,
        ):
            result = await memory.create_long_term_memory(payload, db=object())

        self.assertIs(result, created)
        create_memory.assert_awaited_once()
        self.assertEqual(create_memory.await_args.kwargs["session_id"], 8)
        create_task.assert_called_once()
        index_embedding.assert_called_once_with(99)


if __name__ == "__main__":
    unittest.main()
