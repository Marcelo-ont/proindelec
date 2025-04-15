from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def iniciar_driver():
    """Inicializa el driver de Selenium con Chrome"""
    driver_path = "/snap/bin/chromium.chromedriver"
    options = Options()
    options.add_argument("--headless=new")  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")  
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    return driver