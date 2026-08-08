import asyncio

from httpx import AsyncClient

http_client: AsyncClient | None = None


def init_http_client():
    global http_client
    http_client = AsyncClient()


async def close_http_client():
    if http_client:
        await http_client.aclose()


if __name__ == '__main__':
    init_http_client()


    async def test():
        response = await http_client.get('http://localhost:18081/users/u1001/orders')
        print(response.json()['data']['orders'])

        await close_http_client()


    asyncio.run(test())
