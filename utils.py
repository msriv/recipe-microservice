import asyncio
import aiotask_context as context


def _run_coroutine(coro):
    asyncio.get_event_loop().set_task_factory(context.task_factory)
    return asyncio.get_event_loop().run_until_complete(coro)
