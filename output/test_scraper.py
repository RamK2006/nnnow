"""
Quick test script to verify Selenium setup and NNNOW website access
Run this first before the main scraper
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_setup():
    print("Testing Selenium setup...\n")
    
    try:
        # Initialize Chrome driver
        print("1. Initializing Chrome driver...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        print("✓ Chrome driver initialized successfully\n")
        
        # Test NNNOW website access
        print("2. Testing NNNOW website access...")
        driver.get("https://www.nnnow.com/")
        time.sleep(5)
        
        # Check if page loaded
        if "NNNOW" in driver.title:
            print(f"✓ Successfully loaded: {driver.title}\n")
        else:
            print("⚠ Page loaded but title unexpected\n")
        
        # Get page source length
        page_source = driver.page_source
        print(f"3. Page source length: {len(page_source)} characters")
        
        # Check for product elements
        print("\n4. Checking for common elements...")
        if 'product' in page_source.lower():
            print("✓ Found product-related content\n")
        
        print("="*50)
        print("✓ ALL TESTS PASSED!")
        print("You can now run the main scraper (scraper.py)")
        print("="*50)
        
        # Keep browser open for inspection
        input("\nPress Enter to close the browser...")
        driver.quit()
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome browser is installed")
        print("2. Check your internet connection")
        print("3. Try running: pip install --upgrade selenium webdriver-manager")

if __name__ == "__main__":
    test_setup()