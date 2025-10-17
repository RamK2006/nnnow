"""
NNNOW Product Scraper
Scrapes product information from NNNOW.com
"""

import time
import json
import hashlib
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class NNNOWScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with Chrome driver"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15)
        
    def generate_product_id(self, url):
        """Generate unique product ID from URL using hash"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def extract_price(self, price_text):
        """Extract numeric price from text like '₹ 1,999.00'"""
        if not price_text:
            return None
        try:
            clean_price = price_text.replace('₹', '').replace(',', '').replace('Rs.', '').strip()
            return f"{float(clean_price)} INR"
        except:
            return None
    
    def scroll_page(self, scroll_pause_time=2):
        """Scroll page to load all products (lazy loading)"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 5  # Limit scrolls to avoid infinite loop
        
        while scroll_count < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            last_height = new_height
            scroll_count += 1
            print(f"Scrolled {scroll_count} times...")
    
    def get_product_links(self, category_url, max_products=10):
        """Extract product URLs from category page"""
        print(f"\n{'='*60}")
        print(f"Navigating to: {category_url}")
        print(f"{'='*60}\n")
        
        self.driver.get(category_url)
        time.sleep(3)
        
        # Scroll to load more products
        self.scroll_page()
        
        # Get page source and parse
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Find product links (adjust selectors based on actual site structure)
        product_links = []
        
        # Try multiple selector patterns
        link_elements = soup.find_all('a', href=True)
        
        for link in link_elements:
            href = link.get('href', '')
            # Filter for product detail pages
            if href.startswith('/') and len(href) > 10 and not any(x in href for x in ['products', 'sale', 'category', 'search']):
                full_url = f"https://www.nnnow.com{href}" if href.startswith('/') else href
                if full_url not in product_links:
                    product_links.append(full_url)
        
        print(f"Found {len(product_links)} product links")
        return product_links[:max_products]
    
    def extract_product_details(self, product_url):
        """Extract all details from a single product page"""
        print(f"\nScraping: {product_url}")
        
        try:
            self.driver.get(product_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Initialize product data structure
            product_data = {
                "id": self.generate_product_id(product_url),
                "title": None,
                "description": None,
                "link": product_url,
                "product_category": None,
                "brand": None,
                "material": None,
                "weight": None,
                "age_group": "Adult",  # Default
                "image_link": None,
                "additional_image_link": [],
                "price": None,
                "sale_price": None,
                "pricing_trend": None,
                "availability": "in_stock",  # Default
                "inventory_quantity": None,
                "variant_options": []
            }
            
            # Extract title
            try:
                title_elem = soup.find('h1') or soup.find('h2', class_=lambda x: x and 'title' in x.lower())
                if title_elem:
                    product_data['title'] = title_elem.get_text(strip=True)
            except:
                pass
            
            # Extract brand
            try:
                brand_elem = soup.find(class_=lambda x: x and 'brand' in x.lower())
                if brand_elem:
                    product_data['brand'] = brand_elem.get_text(strip=True)
            except:
                pass
            
            # Extract description
            try:
                desc_elem = soup.find(class_=lambda x: x and 'description' in x.lower()) or \
                           soup.find('div', class_=lambda x: x and 'details' in x.lower())
                if desc_elem:
                    product_data['description'] = desc_elem.get_text(strip=True)[:200]
            except:
                pass
            
            # Extract prices
            try:
                # Look for price elements
                price_elements = soup.find_all(class_=lambda x: x and 'price' in x.lower())
                prices = []
                for elem in price_elements:
                    text = elem.get_text(strip=True)
                    if '₹' in text or 'Rs' in text:
                        prices.append(text)
                
                if len(prices) >= 2:
                    product_data['price'] = self.extract_price(prices[0])
                    product_data['sale_price'] = self.extract_price(prices[1])
                elif len(prices) == 1:
                    product_data['price'] = self.extract_price(prices[0])
                    product_data['sale_price'] = self.extract_price(prices[0])
            except:
                pass
            
            # Extract images
            try:
                img_elements = soup.find_all('img')
                for img in img_elements:
                    src = img.get('src', '') or img.get('data-src', '')
                    if src and 'cdn' in src and 'styles' in src:
                        if not product_data['image_link']:
                            product_data['image_link'] = src
                        elif src not in product_data['additional_image_link']:
                            product_data['additional_image_link'].append(src)
            except:
                pass
            
            # Extract category from breadcrumbs
            try:
                breadcrumb = soup.find(class_=lambda x: x and 'breadcrumb' in x.lower())
                if breadcrumb:
                    links = breadcrumb.find_all('a')
                    categories = [link.get_text(strip=True) for link in links]
                    product_data['product_category'] = ' > '.join(categories) if categories else None
            except:
                pass
            
            # Extract variants (sizes, colors)
            try:
                # Look for size/color selectors
                size_elements = soup.find_all(class_=lambda x: x and 'size' in x.lower())
                color_elements = soup.find_all(class_=lambda x: x and 'color' in x.lower())
                
                if size_elements or color_elements:
                    variant = {
                        "color": color_elements[0].get_text(strip=True) if color_elements else "",
                        "size": size_elements[0].get_text(strip=True) if size_elements else "",
                        "size_system": "IN",
                        "gender": "unisex",
                        "price": product_data['price'],
                        "sale_price": product_data['sale_price']
                    }
                    product_data['variant_options'].append(variant)
            except:
                pass
            
            print(f"✓ Successfully scraped: {product_data['title']}")
            return product_data
            
        except Exception as e:
            print(f"✗ Error scraping {product_url}: {str(e)}")
            return None
    
    def scrape_category(self, category_url, max_products=10):
        """Main method to scrape products from a category"""
        all_products = []
        
        try:
            # Get product links
            product_links = self.get_product_links(category_url, max_products)
            
            # Scrape each product
            for i, link in enumerate(product_links, 1):
                print(f"\n[{i}/{len(product_links)}] Processing product...")
                product_data = self.extract_product_details(link)
                
                if product_data:
                    all_products.append(product_data)
                
                # Rate limiting
                time.sleep(2)
            
            return all_products
            
        except Exception as e:
            print(f"Error in scraping category: {str(e)}")
            return all_products
    
    def save_to_json(self, products, filename='output/products.json'):
        """Save products to JSON file"""
        os.makedirs('output', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✓ Saved {len(products)} products to {filename}")
        print(f"{'='*60}\n")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed.")


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("NNNOW PRODUCT SCRAPER")
    print("="*60 + "\n")
    
    # Initialize scraper
    scraper = NNNOWScraper(headless=False)
    
    try:
        # Target URL - Men's clothing category
        category_url = "https://www.nnnow.com/men-clothing"
        
        # Scrape products (adjust max_products as needed)
        products = scraper.scrape_category(category_url, max_products=10)
        
        # Save results
        if products:
            scraper.save_to_json(products)
            
            # Print summary
            print("\nSCRAPING SUMMARY:")
            print(f"Total products scraped: {len(products)}")
            for i, product in enumerate(products, 1):
                print(f"{i}. {product.get('title', 'N/A')} - {product.get('brand', 'N/A')}")
        else:
            print("\n⚠ No products were scraped. Check the selectors or website structure.")
    
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()