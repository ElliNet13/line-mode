import requests
from bs4 import BeautifulSoup
import re
import execjs  # Importing execjs for JavaScript execution
from urllib.parse import urljoin, urlparse

class LineModeBrowser:
    def __init__(self):
        self.history = []
        self.current_url = ""
        self.page_length = 1000
        self.js_engine = execjs.get()

    def strip_html_tags_and_add_numbers(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = {i: a['href'] for i, a in enumerate(soup.find_all('a'), start=1)}

        # Handle images and clickable elements
        images = soup.find_all('img')
        for img in images:
            alt_text = img.get('alt', 'No alt text')
            img.insert_before(f"[IMAGE: {alt_text}] ")

        clickable_elements = soup.find_all(lambda tag: tag.has_attr('onclick'))
        for elem in clickable_elements:
            elem.insert_before(f"[CLICKABLE] ")

        # Insert link numbers into the text
        for i, a in enumerate(soup.find_all(['a', 'img', lambda tag: tag.has_attr('onclick')]), start=1):
            a.insert(0, f"[{i}] ")

        clean_text = soup.get_text()
        return clean_text, links, str(soup)  # Return modified HTML document as string

    def display_text_paginated(self, text):
        start = 0
        while start < len(text):
            print(text[start:start + self.page_length])
            start += self.page_length
            if start < len(text):
                input("Press Enter to continue...")

    def fetch_page(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.current_url = url
            self.history.append(url)
            clean_text, links, modified_html = self.strip_html_tags_and_add_numbers(response.text)

            # Execute JavaScript functions directly on the modified HTML
            self.execute_js_functions(modified_html)

            self.display_text_paginated(clean_text)
            return links
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {}

    def execute_js_functions(self, html):
        # Find all JavaScript functions and execute them using execjs
        js_functions = self.extract_js_functions(html)
        for func in js_functions:
            try:
                ctx = self.js_engine.compile(html)
                ctx.eval(func)
            except Exception as e:
                print(f"Error executing JavaScript function: {e}")

    def extract_js_functions(self, html):
        # Use regex to find JavaScript function definitions
        js_functions = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
        return js_functions

    def handle_url(self, url):
        # Handle different types of URLs (http/https, javascript, etc.)
        if url.startswith("javascript:"):
            self.execute_javascript_url(url)
        else:
            new_url = urljoin(self.current_url, url)
            self.fetch_page(new_url)

    def execute_javascript_url(self, js_url):
        # Execute JavaScript code directly from javascript: URL
        js_code = js_url.replace("javascript:", "").strip()
        try:
            ctx = self.js_engine.compile("")
            ctx.eval(js_code)
        except Exception as e:
            print(f"Error executing JavaScript URL: {e}")

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()  # Remove current page
            previous_url = self.history.pop()  # Get the previous page
            self.fetch_page(previous_url)
        else:
            print("No previous page to go back to.")

    def start(self):
        while True:
            command = input("Enter a URL, 'back', 'help', or 'exit': ").strip()
            if command.lower() == 'exit':
                break
            elif command.lower() == 'help':
                print("Commands:\n- Enter a URL to visit it\n- 'back' to go to the previous page\n- 'exit' to quit")
            elif command.lower() == 'back':
                self.go_back()
            else:
                self.handle_url(command)

print("Line mode browser simulator by ElliNet13")
browser = LineModeBrowser()
browser.start()