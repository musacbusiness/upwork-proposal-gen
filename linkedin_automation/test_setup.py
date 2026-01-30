#!/usr/bin/env python3
"""
Quick test script for LinkedIn Selenium automation
Run this to verify everything is working before using the full automation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(dotenv_path='../.env')

def check_dependencies():
    """Check if required packages are installed"""
    print("=" * 60)
    print("CHECKING DEPENDENCIES")
    print("=" * 60)
    
    packages = {
        'selenium': 'Selenium (browser automation)',
        'webdriver_manager': 'WebDriver Manager',
        'anthropic': 'Claude AI',
        'requests': 'HTTP requests',
        'dotenv': 'Environment variables'
    }
    
    missing = []
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✓ {description}: INSTALLED")
        except ImportError:
            print(f"✗ {description}: MISSING")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages:")
        print(f"pip3 install {' '.join(missing)}")
        return False
    
    return True


def check_credentials():
    """Check if required credentials are set"""
    print("\n" + "=" * 60)
    print("CHECKING CREDENTIALS")
    print("=" * 60)
    
    required = {
        'LINKEDIN_EMAIL': 'LinkedIn Email',
        'LINKEDIN_PASSWORD': 'LinkedIn Password',
        'ANTHROPIC_API_KEY': 'Claude API Key',
        'AIRTABLE_API_KEY': 'Airtable API Key',
        'REPLICATE_API_TOKEN': 'Replicate API Token'
    }
    
    missing = []
    for env_var, description in required.items():
        value = os.getenv(env_var)
        if value and value != f'your_{env_var.lower()}':
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✓ {description}: {masked}")
        else:
            print(f"✗ {description}: NOT SET")
            missing.append(env_var)
    
    if missing:
        print(f"\nAdd these to your .env file:")
        for var in missing:
            print(f"{var}=your_value_here")
        return False
    
    return True


def test_selenium():
    """Test Selenium browser automation"""
    print("\n" + "=" * 60)
    print("TESTING SELENIUM (This will open a browser)")
    print("=" * 60)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("Initializing Chrome driver...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✓ Chrome driver initialized")
        
        print("Testing navigation to LinkedIn...")
        driver.get('https://www.linkedin.com')
        
        if 'LinkedIn' in driver.title:
            print("✓ Successfully navigated to LinkedIn")
        else:
            print(f"⚠️ Unexpected page title: {driver.title}")
        
        driver.quit()
        print("✓ Browser closed")
        
        return True
        
    except Exception as e:
        print(f"✗ Selenium test failed: {e}")
        return False


def test_linkedin_login():
    """Test LinkedIn login (non-headless so you can see)"""
    print("\n" + "=" * 60)
    print("TESTING LINKEDIN LOGIN")
    print("=" * 60)
    print("This will open a visible browser and attempt to log in.")
    print("Watch the browser to see if login succeeds.")
    print("")
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Skipped login test")
        return True
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'execution'))
        from linkedin_poster_selenium import LinkedInPosterSelenium
        
        print("\nLogging into LinkedIn...")
        print("(Browser window will open - watch for any 2FA challenges)")
        
        with LinkedInPosterSelenium(headless=False) as poster:
            # Just initialize and login, don't post
            print("\n✓ Login successful!")
            print("Browser will close in 5 seconds...")
            import time
            time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"✗ Login test failed: {e}")
        return False


def main():
    print("\n🔍 LinkedIn Automation - System Check\n")
    
    results = {}
    
    # Run checks
    results['dependencies'] = check_dependencies()
    results['credentials'] = check_credentials()
    
    if results['dependencies']:
        results['selenium'] = test_selenium()
        
        if all([results['dependencies'], results['credentials'], results['selenium']]):
            results['login'] = test_linkedin_login()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All tests passed! You're ready to use the automation.")
        print("\nNext steps:")
        print("1. Generate posts: python3 RUN_linkedin_automation.py --action generate-posts")
        print("2. Post to LinkedIn: python3 RUN_linkedin_automation.py --action post-now")
    else:
        print("\n⚠️ Some tests failed. Fix the issues above and try again.")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
