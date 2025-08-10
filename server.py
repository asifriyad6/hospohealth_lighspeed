# server.py
from fastapi import FastAPI, Request
import os
import main  # your Selenium script logic here

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "Service running"}

@app.post("/run")
async def run_script(req: Request):
    data = await req.json()
    result = main.run(data)  # assuming you wrap your Selenium logic in a run() function
    return {"status": "done", "result": result}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
