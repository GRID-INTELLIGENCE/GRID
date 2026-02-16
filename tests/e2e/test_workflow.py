import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture(scope="module")
def browser():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def test_login_and_inference(browser):
    # Open application
    browser.get("http://localhost:3000")

    # Login
    browser.find_element(By.ID, "username").send_keys("testuser")
    browser.find_element(By.ID, "password").send_keys("testpass")
    browser.find_element(By.ID, "login-button").click()

    # Wait for dashboard
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "dashboard-header")))

    # Create inference
    browser.find_element(By.ID, "prompt-input").send_keys("What is the meaning of life?")
    browser.find_element(By.ID, "submit-inference").click()

    # Wait for result
    result = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.ID, "inference-result")))

    assert "result" in result.text.lower()


def test_privacy_masking(browser):
    # Navigate to privacy tool
    browser.find_element(By.ID, "privacy-tab").click()

    # Enter text with PII
    browser.find_element(By.ID, "privacy-input").send_keys("Contact me at test@example.com or 555-123-4567")
    browser.find_element(By.ID, "mask-button").click()

    # Check result
    result = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "masked-output")))

    assert "test@example.com" not in result.text
    assert "555-123-4567" not in result.text
