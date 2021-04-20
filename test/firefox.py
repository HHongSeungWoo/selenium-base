import driverutils
from selenium import webdriver


driverutils.FireFoxInstaller(True).install()

d = webdriver.Firefox(options=driverutils.make_default_firefox_options())

print(d.execute_script("return navigator.userAgent"))
import time
time.sleep(5)

d.quit()
