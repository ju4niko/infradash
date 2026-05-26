from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "infradash backend ok"}

