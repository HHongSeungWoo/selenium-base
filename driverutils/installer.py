import sys
import os
import subprocess
import typing
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as elemTree
import re
from io import BytesIO
from abc import ABCMeta, abstractmethod


class InstallInterface(metaclass=ABCMeta):

    def __init__(self, cwd=False):
        self.cwd = cwd

    def install(self) -> str:
        self.download()

        if 'PATH' not in os.environ:
            os.environ['PATH'] = self.driver_dir
        elif self.driver_dir not in os.environ['PATH']:
            os.environ['PATH'] = self.driver_dir + ";" if sys.platform.startswith('win') else ":" + os.environ['PATH']
        return self.binary_path

    @property
    @abstractmethod
    def binary_name(self) -> str:
        pass

    @property
    def binary_path(self) -> str:
        return os.path.join(self.driver_dir, self.binary_name)

    @property
    def driver_dir(self) -> str:
        return os.path.join(os.path.abspath(os.getcwd())) if self.cwd else os.path.join(
            os.path.abspath(os.path.dirname(__file__)))

    @property
    @abstractmethod
    def require_version(self) -> str:
        pass

    @property
    @abstractmethod
    def current_version(self) -> str:
        pass

    @property
    @abstractmethod
    def get_download_url(self) -> str:
        pass

    @abstractmethod
    def download(self) -> str:
        pass

    @abstractmethod
    def has_require_version(self) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def get_platform_architecture() -> typing.Tuple[str, str]:
        pass


class ChromeInstaller(InstallInterface):

    @staticmethod
    def get_platform_architecture() -> typing.Tuple[str, str]:
        if sys.platform.startswith('linux') and sys.maxsize > 2 ** 32:
            platform = 'linux'
            architecture = '64'
        elif sys.platform == 'darwin':
            platform = 'mac'
            architecture = '64'
        elif sys.platform.startswith('win'):
            platform = 'win'
            architecture = '32'
        else:
            raise RuntimeError('Could not determine chromedriver download URL for this platform.')
        return platform, architecture

    @property
    def binary_name(self) -> str:
        return 'chromedriver' + '.exe' if sys.platform.startswith('win') else ''

    @property
    def require_version(self) -> str:
        if (cache_version := getattr(self, "_require_version", False)) is not False:
            return cache_version
        platform, _ = self.get_platform_architecture()
        if platform == 'linux':
            with subprocess.Popen(['chromium-browser', '--version'], stdout=subprocess.PIPE) as proc:
                version = proc.stdout.read().decode('utf-8').replace('Chromium', '').strip()
                version = version.replace('Google Chrome', '').strip()
        elif platform == 'mac':
            process = subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                                       stdout=subprocess.PIPE)
            version = process.communicate()[0].decode('UTF-8').replace('Google Chrome', '').strip()
        elif platform == 'win':
            process = subprocess.Popen(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
            )
            version = process.communicate()[0].decode('UTF-8').strip().split()[-1]
        else:
            return ''

        if version:
            setattr(self, "_require_version", version)

        return version

    @property
    def get_download_url(self) -> str:
        base_url = 'https://chromedriver.storage.googleapis.com/'
        platform, architecture = self.get_platform_architecture()
        major_version = self.require_version.split('.')[0]
        doc = urllib.request.urlopen('https://chromedriver.storage.googleapis.com').read()
        root = elemTree.fromstring(doc)
        for k in root.iter('{http://doc.s3.amazonaws.com/2006-03-01}Key'):
            if k.text.find(major_version + '.') == 0:
                return base_url + k.text.split('/')[0] + '/chromedriver_' + platform + architecture + '.zip'
        else:
            raise Exception("not found match driver")

    def has_require_version(self) -> bool:
        return self.require_version.split(".")[0] == self.current_version.split(".")[0]

    @property
    def current_version(self) -> str:
        if (cache_version := getattr(self, "_current_version", False)) is not False:
            return cache_version
        version = subprocess.check_output([self.binary_path, '-v'])
        version = re.match(r'.*?([\d.]+).*?', version.decode('utf-8'))[1]

        if version:
            setattr(self, "_current_version", version)

        return version

    def download(self) -> str:
        if not self.require_version:
            raise Exception("크롬이 설치되어 있는지 확인하세요.")

        if not os.path.isfile(self.binary_path) or not self.has_require_version():
            response = urllib.request.urlopen(self.get_download_url)
            if response.getcode() != 200:
                raise urllib.error.URLError('Not Found')
            archive = BytesIO(response.read())
            with zipfile.ZipFile(archive) as zip_file:
                zip_file.extract(self.binary_name, self.driver_dir)
        if not os.access(self.binary_path, os.X_OK):
            os.chmod(self.binary_path, 0o744)
        return self.binary_path


class IeInstaller(InstallInterface):

    @staticmethod
    def get_platform_architecture() -> typing.Tuple[str, str]:
        pass

    @property
    def binary_name(self) -> str:
        return "IEDriverServer.exe"

    @property
    def require_version(self) -> str:
        return "3.150.1"

    @property
    def current_version(self) -> str:
        version = subprocess.check_output([self.binary_path, '-v'])
        return version.decode().split()[1]

    @property
    def get_download_url(self) -> str:
        return f"https://selenium-release.storage.googleapis.com/{self.require_version[:-2]}" \
               f"/IEDriverServer_Win32_{self.require_version}.zip"

    def download(self) -> str:
        if not os.path.isfile(self.binary_path) or not self.has_require_version():
            response = urllib.request.urlopen(self.get_download_url)
            if response.getcode() != 200:
                raise urllib.error.URLError('Not Found')
            archive = BytesIO(response.read())
            with zipfile.ZipFile(archive) as zip_file:
                zip_file.extract(self.binary_name, self.driver_dir)
        if not os.access(self.binary_path, os.X_OK):
            os.chmod(self.binary_path, 0o744)
        return self.binary_path

    def has_require_version(self) -> bool:
        return self.require_version == self.current_version[:-2]


class FireFoxInstaller(InstallInterface):

    @property
    def binary_name(self) -> str:
        return 'geckodriver' + '.exe' if sys.platform.startswith('win') else ''

    @property
    def require_version(self) -> str:
        if (cache_version := getattr(self, "_require_version", False)) is not False:
            return cache_version
        url = urllib.request.urlopen('https://github.com/mozilla/geckodriver/releases/latest').geturl()
        if '/tag/' not in url:
            raise Exception("게코 드라이버 버전을 찾을 수 없음")

        setattr(self, "_require_version", url.split('/')[-1])

        return url.split('/')[-1]

    @property
    def current_version(self) -> str:
        if (cache_version := getattr(self, "_current_version", False)) is not False:
            return cache_version
        version = subprocess.check_output([self.binary_path, '--version'])
        version = re.findall(r"gecko.*(\d+\.\d+\.\d+)", version.decode())
        if len(version) == 0:
            raise Exception("설치된 드라이버 버전을 찾을 수 없음")

        if version[0]:
            setattr(self, "_current_version", "v"+version[0])

        return "v"+version[0]

    @property
    def get_download_url(self) -> str:
        platform, architecture = self.get_platform_architecture()

        if platform == 'win':
            compression = 'zip'
        else:
            compression = 'tar.gz'

        return f'https://github.com/mozilla/geckodriver/releases/download/{self.require_version}' \
               f'/geckodriver-{self.require_version}-{platform}{architecture}.{compression}'

    def download(self) -> str:
        if not os.path.isfile(self.binary_path) or not self.has_require_version():
            response = urllib.request.urlopen(self.get_download_url)
            if response.getcode() != 200:
                raise urllib.error.URLError('Not Found')
            archive = BytesIO(response.read())
            if sys.platform.startswith("win"):
                with zipfile.ZipFile(archive) as zip_file:
                    zip_file.extract(self.binary_name, self.driver_dir)
            else:
                import tarfile
                tar = tarfile.open(fileobj=archive, mode='r:gz')
                tar.extract(self.binary_name, self.driver_dir)
                tar.close()
        if not os.access(self.binary_path, os.X_OK):
            os.chmod(self.binary_path, 0o744)
        return self.binary_path

    def has_require_version(self) -> bool:
        return self.current_version == self.require_version

    @staticmethod
    def get_platform_architecture() -> typing.Tuple[str, str]:
        if sys.platform.startswith('linux') and sys.maxsize > 2 ** 32:
            platform = 'linux'
            architecture = '64'
        elif sys.platform == 'darwin':
            platform = 'mac'
            architecture = 'os'
        elif sys.platform.startswith('win'):
            platform = 'win'
            from platform import machine as get_machine
            if get_machine().endswith('64'):
                architecture = '64'
            else:
                architecture = '32'
        else:
            raise RuntimeError('Could not determine geckodriver download URL for this platform.')
        return platform, architecture


if __name__ == '__main__':
    print(FireFoxInstaller().download())
