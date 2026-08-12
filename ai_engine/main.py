from fastapi import FastAPI

app = FastAPI(
    title="AlternIA AI Engine",
    description="Moteur pédagogique intelligent d'AlternIA",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "application": "AlternIA",
        "status": "online",
        "version": "0.1.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
