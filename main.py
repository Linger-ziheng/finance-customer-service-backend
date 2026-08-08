import uvicorn

from atguigu.conf.config import settings


def main():
    uvicorn.run('atguigu.app.app:app', host=settings.app_host, port=settings.app_port)


if __name__ == '__main__':
    main()
