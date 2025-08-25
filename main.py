from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

app = FastAPI()

# --------- Selenium Setup ---------
options = Options()
options.add_argument("--headless=new")   # headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")

# use Railway Chromium
options.binary_location = "/usr/bin/chromium"

driver = webdriver.Chrome(
    executable_path="/usr/bin/chromedriver",
    options=options
)


class RunRequest(BaseModel):
    url: str


@app.post("/run")
def run_selenium_task(req: RunRequest):
    """Open a webpage and return the title."""
    driver.get(req.url)
    return {"url": req.url, "title": driver.title}


@app.get("/")
def root():
    return {"status": "FastAPI + Selenium running on Railway 🚀"}


@app.on_event("shutdown")
def shutdown_event():
    driver.quit()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)