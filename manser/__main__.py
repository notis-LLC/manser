import logging

from fastapi import FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics

from manser.config import DEBUG, HOST, LOG_LEVEL, PORT
from manser.handlers import router

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=LOG_LEVEL
)


def get_application() -> FastAPI:
    app = FastAPI(title="Manser - Ru manga updates API", debug=DEBUG)
    app.include_router(router)
    app.add_middleware(PrometheusMiddleware, app_name="manser")
    app.add_route("/metrics", handle_metrics)
    return app


app = get_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, log_level=LOG_LEVEL)
