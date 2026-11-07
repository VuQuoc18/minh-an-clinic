from fastapi import FastAPI

app = FastAPI(title="Minh An Clinic API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
