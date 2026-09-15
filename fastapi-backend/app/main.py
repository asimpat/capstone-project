from fastapi import FastAPI

app = FastAPI(title="My FastAPI Backend")


@app.get("/")
def home():
    return {
        "message": "FastAPI backend is working!"
    }


@app.get("/hello")
def hello():
    return {
        "message": "Hello World!"
    }
