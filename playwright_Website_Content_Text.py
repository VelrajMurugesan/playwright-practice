"""
Extract text content from https://docs.python.org/3.14/
and save it to a text file.
"""

from playwright.sync_api import sync_playwright


URL = "https://docs.python.org/3.14/"
OUTPUT_FILE = "python_3_14_docs.txt"


def extract_text_from_python_docs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Open the site
        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # Extract visible text from main content
        text_content = page.evaluate("""
            () => {
                const main = document.querySelector("main") || document.body;
                return main.innerText;
            }
        """)

        # Write to text file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            file.write(text_content)

        browser.close()
        print(f"✅ Text extracted and saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    extract_text_from_python_docs()
