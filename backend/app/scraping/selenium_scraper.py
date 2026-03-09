from __future__ import annotations
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def fetch_text(url: str, max_chars: int = 4000) -> str:
    remote = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Remote(command_executor=remote, options=opts)
    try:
        driver.get(url)
        body = driver.find_element(By.TAG_NAME, "body")
        text = " ".join(body.text.split())
        return text[:max_chars]
    finally:
        driver.quit()
