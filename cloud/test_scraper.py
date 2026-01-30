"""Quick test to debug the scraper on Modal"""
import modal
import os
import json

app = modal.App("test-scraper")

scraper_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("chromium", "chromium-driver")
    .pip_install("selenium", "requests")
    .env({
        "CHROME_BIN": "/usr/bin/chromium",
        "CHROMEDRIVER_PATH": "/usr/bin/chromedriver",
    })
)

@app.function(
    image=scraper_image,
    secrets=[modal.Secret.from_name("upwork-cookies")],
    timeout=300,
)
def test_login():
    """Test if cookies work for Upwork login."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time
    
    # Load cookies
    cookies_json = os.environ.get("UPWORK_COOKIES", "[]")
    print(f"Cookies JSON length: {len(cookies_json)}")
    
    try:
        cookies = json.loads(cookies_json)
        print(f"Parsed {len(cookies)} cookies")
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse cookies: {e}"}
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    print("Starting Chrome...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load Upwork first
        print("Loading upwork.com...")
        driver.get("https://www.upwork.com")
        time.sleep(2)
        
        # Clear and add cookies
        driver.delete_all_cookies()
        added = 0
        for cookie in cookies:
            try:
                cookie_dict = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain', '.upwork.com'),
                    'path': cookie.get('path', '/'),
                }
                driver.add_cookie(cookie_dict)
                added += 1
            except Exception as e:
                print(f"Failed to add cookie {cookie.get('name')}: {e}")
        
        print(f"Added {added} cookies")
        
        # Refresh and check login
        driver.refresh()
        time.sleep(3)
        
        print("Navigating to find-work...")
        driver.get("https://www.upwork.com/nx/find-work/")
        time.sleep(5)
        
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        if "login" in current_url.lower():
            return {
                "status": "error", 
                "message": "Cookies expired - redirected to login",
                "url": current_url
            }
        
        # Try to find job elements
        page_source_len = len(driver.page_source)
        print(f"Page source length: {page_source_len}")
        
        return {
            "status": "success",
            "message": "Logged in successfully",
            "url": current_url,
            "page_size": page_source_len
        }
        
    finally:
        driver.quit()

@app.local_entrypoint()
def main():
    result = test_login.remote()
    print("\n" + "="*50)
    print("RESULT:")
    print(json.dumps(result, indent=2))
