import typing
from abc import ABCMeta, abstractmethod

from selenium import webdriver
from selenium.webdriver.remote.remote_connection import RemoteConnection
from urllib3.util import timeout as _timeout


class OptionInterface(metaclass=ABCMeta):

    def __init__(self):
        self._options = self.init_options()

    @abstractmethod
    def init_options(self):
        pass

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, val):
        self._options = val

    @abstractmethod
    def set_user_agent(self, user_agent: str):
        return self

    @abstractmethod
    def set_start_url(self, url: str):
        return self

    def build(self):
        return self._options


class IeOptions(OptionInterface):

    def __init__(self):
        super().__init__()
        print("설정 -> 인터넷 옵션 -> 보안 탭의 4가지 영역 모두 보호 모드 사용 체크 확인")
        print("설정 -> 확대/축소 -> 100% 설정 확인")

    def init_options(self):
        options = webdriver.IeOptions()
        options.ignore_zoom_level = True
        options.ignore_protected_mode_settings = True
        return options

    def set_user_agent(self, user_agent: str):
        print("IE는 User-Agent 변경 기능을 지원하지 않습니다.")
        return self

    def set_start_url(self, url: str):
        self._options.initial_browser_url = url
        return self


class ChromeOptions(OptionInterface):

    def __init__(self):
        super().__init__()
        RemoteConnection.set_timeout(_timeout.Timeout(total=30))

    def init_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        return options

    def set_user_agent(self, user_agent: str):
        self._options.add_argument(f'user-agent={user_agent}')
        return self

    def set_start_url(self, url: str):
        print("크롬은 시작페이지 설정을 지원하지 않습니다.")
        return self


class FirefoxOptions(OptionInterface):

    def init_options(self):
        options = webdriver.FirefoxOptions()
        profile = webdriver.FirefoxProfile()
        options.profile = profile
        profile.set_preference("dom.webdriver.enabled", False)
        profile.set_preference('useAutomationExtension', False)

        return options

    def set_user_agent(self, user_agent: str):
        self._options.profile.set_preference("general.useragent.override", user_agent)
        return self

    def set_start_url(self, url: str):
        self._options.profile.set_preference("browser.startup.homepage", "https://google.com")
        self._options.profile.set_preference("browser.startup.blankWindow", False)
        self._options.profile.set_preference("browser.startup.page", 1)

        return self

    def build(self):
        self._options.profile.update_preferences()
        return self._options
