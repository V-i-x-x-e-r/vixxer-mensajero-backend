from starlette.concurrency import run_in_threadpool


async def en_hilo(fn, *args, **kwargs):
    return await run_in_threadpool(fn, *args, **kwargs)
