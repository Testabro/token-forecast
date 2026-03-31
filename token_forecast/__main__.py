import uvicorn

from token_forecast.config import settings


def main():
    uvicorn.run(
        "token_forecast.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
