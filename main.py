import uvicorn

from atguigu.conf.config import settings


def mian():
    uvicorn.run('atguigu.app.app:app', host=settings.app_host, port=settings.app_port, reload=True)


if __name__ == '__main__':
    mian()
