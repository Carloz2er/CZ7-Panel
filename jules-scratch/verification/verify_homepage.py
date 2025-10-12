from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()

    # Go to the homepage
    page.goto("http://127.0.0.1:8000/")

    # Expect the main heading to be visible
    heading = page.get_by_role("heading", name="Bem-vindo ao Painel CZ7 Host")
    expect(heading).to_be_visible()

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/homepage.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)