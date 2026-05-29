from fastapi import FastAPI

app = FastAPI(title="Enterprise RAG Platform")


@app.get("/")
def home():
    return{
        "message":"Enterprise RAG Backend Running Successfully"
    }