import asyncio
from collections import Counter

import httpx

from batch import QUEUE_MAX_SIZE
from test.common import BASE, FARM

# enough simultaneous requests to outrun the worker
REQUEST_COUNT = QUEUE_MAX_SIZE * 4


async def main() -> None:
    limits = httpx.Limits(max_connections=None, max_keepalive_connections=None)
    async with httpx.AsyncClient(base_url=BASE, limits=limits, timeout=30) as client:
        responses = await asyncio.gather(*(
            client.post("/predict-queued", json=FARM.model_dump())
            for _ in range(REQUEST_COUNT)
        ))

    print(f"Sent {REQUEST_COUNT} requests")
    print(f"Codes: {dict(Counter(res.status_code for res in responses))}")
    rejected = next((res for res in responses if res.status_code == 429), None)
    if rejected is not None:
        print(f"Retry-After: {rejected.headers.get('Retry-After')}")
        print(f"Contents:\n{rejected.json()}")


if __name__ == "__main__":
    asyncio.run(main())
