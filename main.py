from fastapi import FastAPI, Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from io import StringIO
import csv
import json
import requests

app = FastAPI()

def safe_click(driver, element, retries=3):
    """Click element safely, scrolling into view if intercepted."""
    for _ in range(retries):
        try:
            element.click()
            return True
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
    return False

def init_driver():
    """Initialize Chrome driver for headless Railway deployment."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def extract_csv_from_pre(driver):
    """Extract CSV text from <pre> tag and convert to JSON list."""
    csv_text = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "pre"))
    ).text
    reader = csv.DictReader(StringIO(csv_text))
    return list(reader)

def login_and_switch_iframe(driver, url):
    """Login and switch to Looker iframe."""
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys("keith@hospohealth.com")
    driver.find_element(By.NAME, "password").send_keys("KountaHH2095!")
    wait.until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "lookerFrame")))

def update_dashboard(driver, location_text, interval_values=None):
    """Update dashboard filters, select hours, and set location."""
    wait = WebDriverWait(driver, 15)

    # Switch 'months' dropdowns to 'hours' via JS
    driver.execute_script("""
        document.querySelectorAll("input.kYwJhe[readonly][value='months']").forEach(el => el.value = 'hours');
    """)

    # Set interval inputs if provided
    if interval_values:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[data-testid='interval-value']")
        for idx, val in enumerate(interval_values):
            if idx < len(inputs):
                inputs[idx].clear()
                inputs[idx].send_keys(str(val))

    # Set location
    location_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input.InputText__StyledInput-sc-6cvg1f-0.iOZCVS"))
    )
    location_input.clear()
    location_input.send_keys(location_text)
    location_input.send_keys(Keys.RETURN)

    # Click Update button via JS
    update_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ButtonBase__ButtonOuter-sc-1bpio6j-0.RunButton__IconButtonWithBackground-sc-skoy04-0"))
    )
    driver.execute_script("arguments[0].click();", update_btn)

@app.post("/run")
async def run_selenium(request: Request):
    data = await request.json()
    location_text = data.get("location", "")
    if not location_text:
        return {"error": "No location text provided"}

    driver = init_driver()
    try:
        # -------------------------------
        # First dashboard
        # -------------------------------
        login_and_switch_iframe(driver, "https://insights.kounta.com/insights?url=/embed/dashboards-next/1231")
        update_dashboard(driver, location_text, interval_values=[228, 158])

        # Extract first dashboard CSV
        data1 = extract_csv_from_pre(driver)

        # Optionally extract a tile value
        try:
            reconciliations_section = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "section[aria-label='No. of Reconciliations']"))
            )
            value_span = reconciliations_section.find_element(
                By.CSS_SELECTOR,
                "span.TextBase-sc-90l5yt-0.Span-sc-1e8sfe6-0.Text-sc-1d84yfs-0.jPObWb.eCUHIC > span"
            )
            reconciliations_value = value_span.text.strip()
        except:
            reconciliations_value = None

        # -------------------------------
        # Second dashboard
        # -------------------------------
        driver.get("https://insights.kounta.com/insights?url=/embed/dashboards-next/1216")
        WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "lookerFrame")))
        # Example: select "Previous Week" filter for the second dashboard
        try:
            more_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH, "//div[normalize-space()='More'] | //span[normalize-space()='More']"
                ))
            )
            safe_click(driver, more_btn)
            previous_week_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[normalize-space()='Previous Week']]"))
            )
            safe_click(driver, previous_week_btn)
        except:
            pass

        update_dashboard(driver, location_text)

        # Extract second dashboard CSV
        data2 = extract_csv_from_pre(driver)

        # -------------------------------
        # Post both dashboard data to webhook
        # -------------------------------
        payload = {
            "location": location_text,
            "no_of_reconciliations": reconciliations_value,
            "dashboard_1": data1,
            "dashboard_2": data2
        }

        resp = requests.post(
            "https://primary-production-3d6e.up.railway.app/webhook-test/88e57b55-ff1a-4324-b9ef-37fc2f48aa7b",
            json=payload,
            timeout=20
        )

        return {"status": "done", "search": location_text, "webhook_status": resp.status_code}

    except TimeoutException as e:
        return {"error": "Timeout occurred", "details": str(e)}
    except Exception as e:
        return {"error": "Exception occurred", "details": str(e)}
    finally:
        driver.quit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
