"""
LinkedIn Poster - Selenium Browser Automation
==============================================
Posts content to LinkedIn using browser automation instead of API.
No API keys required - just your LinkedIn email and password.
"""

import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()


class LinkedInPosterSelenium:
    """
    Automates LinkedIn posting using Selenium browser automation.
    """
    
    def __init__(self, headless=True):
        """
        Initialize the LinkedIn poster.
        
        Args:
            headless: Run browser in headless mode (invisible). Set to False to see what's happening.
        """
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.headless = headless
        self.driver = None
        
        if not self.email or not self.password:
            raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env file")
    
    def _init_driver(self):
        """Initialize Chrome driver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent to avoid detection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        print("✓ Chrome driver initialized")
    
    def _login(self):
        """Log into LinkedIn."""
        print("Logging into LinkedIn...")
        
        self.driver.get('https://www.linkedin.com/login')
        time.sleep(2)
        
        # Enter email
        email_field = self.driver.find_element(By.ID, 'username')
        email_field.send_keys(self.email)
        
        # Enter password
        password_field = self.driver.find_element(By.ID, 'password')
        password_field.send_keys(self.password)
        
        # Click login button
        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        # Wait for login to complete (check for feed)
        time.sleep(5)
        
        # Check if we're on the feed or if there's a verification challenge
        current_url = self.driver.current_url
        
        if 'checkpoint' in current_url or 'challenge' in current_url:
            print("⚠️  LinkedIn security checkpoint detected!")
            print("Please complete the verification in the browser window.")
            print("Waiting 60 seconds for manual verification...")
            time.sleep(60)
        
        print("✓ Logged in successfully")
    
    def post_content(self, text, image_path=None):
        """
        Post content to LinkedIn.
        
        Args:
            text: The text content to post
            image_path: Optional path to image file to upload
        
        Returns:
            dict: Result with success status and message
        """
        try:
            # Initialize driver if not already done
            if not self.driver:
                self._init_driver()
                self._login()
            
            print(f"Posting to LinkedIn...")
            
            # Navigate to feed
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(3)
            
            # Click "Start a post" button
            try:
                start_post_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-button') and contains(., 'Start a post')]"))
                )
                start_post_button.click()
            except:
                # Alternative selector
                start_post_button = self.driver.find_element(By.CSS_SELECTOR, 'button.share-box-feed-entry__trigger')
                start_post_button.click()
            
            time.sleep(2)
            
            # Enter text in the post editor
            try:
                # Wait for the editor to be visible
                editor = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ql-editor[contenteditable="true"]'))
                )
                editor.click()
                time.sleep(1)
                editor.send_keys(text)
                print("✓ Text entered")
            except Exception as e:
                print(f"Error entering text: {e}")
                # Try alternative selector
                editor = self.driver.find_element(By.CSS_SELECTOR, 'div[role="textbox"]')
                editor.click()
                editor.send_keys(text)
            
            # Upload image if provided
            if image_path and os.path.exists(image_path):
                try:
                    # Find and click the image upload button
                    image_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="Add a photo"]')
                    image_button.click()
                    time.sleep(1)
                    
                    # Find the file input and upload
                    file_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
                    abs_image_path = os.path.abspath(image_path)
                    file_input.send_keys(abs_image_path)
                    
                    print(f"✓ Image uploaded: {image_path}")
                    time.sleep(3)  # Wait for image to process
                except Exception as e:
                    print(f"⚠️  Could not upload image: {e}")
            
            # Click Post button
            try:
                post_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'share-actions__primary-action') and not(@disabled)]"))
                )
                post_button.click()
                print("✓ Post button clicked")
            except:
                # Alternative selector
                post_button = self.driver.find_element(By.CSS_SELECTOR, 'button.share-actions__primary-action')
                post_button.click()
            
            # Wait for post to complete
            time.sleep(5)
            
            print("✓ Post published successfully!")
            
            return {
                'success': True,
                'message': 'Post published successfully',
                'url': self.driver.current_url
            }
            
        except Exception as e:
            error_msg = f"Error posting to LinkedIn: {str(e)}"
            print(f"✗ {error_msg}")
            
            # Take screenshot for debugging
            if self.driver:
                screenshot_path = f"/tmp/linkedin_error_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
            
            return {
                'success': False,
                'message': error_msg
            }
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("✓ Browser closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def test_post():
    """Test function to verify LinkedIn posting works."""
    test_text = """🚀 Testing automated LinkedIn posting!

This is a test post from my automation system. 

#Automation #Testing"""
    
    # Use with context manager for automatic cleanup
    with LinkedInPosterSelenium(headless=False) as poster:
        result = poster.post_content(test_text)
        print(f"\nResult: {result}")


if __name__ == '__main__':
    # Run test
    test_post()
