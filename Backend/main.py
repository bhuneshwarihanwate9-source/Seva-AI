from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Seva-AI Backend Running properly!"}