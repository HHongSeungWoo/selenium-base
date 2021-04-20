import driverutils
from selenium import webdriver

driverutils.IeInstaller(True).install()

d = webdriver.Ie(options=driverutils.IeOptions().build())
print(d.execute_script("return navigator.userAgent"))
import time
time.sleep(5)
d.quit()
