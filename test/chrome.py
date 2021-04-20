import driverutils
from selenium import webdriver


driverutils.ChromeInstaller(True).install()

d = webdriver.Chrome(options=driverutils.make_default_chrome_options())

print(d.execute_script("return navigator.userAgent"))
import time
time.sleep(5)

d.quit()