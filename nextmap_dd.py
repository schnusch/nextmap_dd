"""
nextmap_dd
Copyright (C) 2021  schnusch

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
from contextlib import contextmanager
import locale
import os.path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Iterator, List, Optional, cast

from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver import Firefox  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile  # type: ignore
from selenium.webdriver.firefox.options import Options as FirefoxOptions  # type: ignore
from selenium.webdriver.remote.webdriver import WebDriver  # type: ignore
from selenium.webdriver.remote.webelement import WebElement  # type: ignore
from selenium.webdriver.support import expected_conditions  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore


@contextmanager
def firefox_profile(path: Optional[str] = None) -> Iterator[FirefoxProfile]:
    profile = FirefoxProfile(path)
    try:
        yield profile
    finally:
        shutil.rmtree(profile.path, ignore_errors=True)


@contextmanager
def firefox_driver(profile:       str,
                   headless:      bool          = True,
                   minimize:      bool          = False,
                   timeout:       Optional[int] = None,
                   implicit_wait: Optional[int] = None,
                   log_path:      Optional[str] = None) -> Iterator[Firefox]:
    options = FirefoxOptions()
    if profile is not None:
        options.profile = profile
    if headless:
        options.add_argument('--headless')
    kwargs = {}
    if log_path is not None:
        kwargs['service_log_path'] = log_path
    driver = Firefox(options=options, **kwargs)
    try:
        if minimize and not headless:
            driver.minimize_window()
        if timeout is not None:
            driver.set_page_load_timeout(timeout)
        if implicit_wait is not None:
            driver.implicitly_wait(implicit_wait)
        yield driver
    finally:
        driver.close()


def try_decline_cookie_notice(driver: WebDriver):
    try:
        driver.find_element_by_css_selector('.cookie-notice .cn-decline').click()
    except NoSuchElementException:
        pass


def zoom_in(driver: WebDriver, map: WebElement, steps: int = 3):
    zoom_in = driver.execute_script('''
        return arguments[0].shadowRoot.querySelector(".leaflet-control-zoom-in");
    ''', map)
    for _ in range(steps):
        zoom_in.click()


def timestamp_image(img: bytes, name: str):
    p = subprocess.run(['convert', '-',
                        '-gravity', 'North', '-pointsize', '100',
                        '-fill', 'white', '-undercolor', '#00000080',
                        '-annotate', '0', time.strftime('\xA0%a %d.%m.%Y, %H:%M:%S%z '),
                        '-quality', '100', name], input=img)
    p.check_returncode()


def main(argv: Optional[List[str]] = None):
    locale.setlocale(locale.LC_ALL, '')

    p = argparse.ArgumentParser(description="Take a screenshot of Dresden's nextbike map")
    p.add_argument('-o', '--out',
                   metavar='<out>',
                   required=True,
                   help="write screenshot to <out>")
    p.add_argument('-z',
                   dest='zoom',
                   metavar='<zoom>',
                   type=int,
                   default=3,
                   help="number of times to zoom in (default: 3)")
    args = p.parse_args(argv)

    with firefox_profile() as profile:
        with firefox_driver(profile, headless=True, log_path='/dev/null') as driver:
            driver.set_window_size(4096 + 12, 4693)
            driver.get('https://www.nextbike.de/de/dresden/')
            WebDriverWait(driver, 30).until(
                lambda d: expected_conditions.visibility_of_element_located((By.TAG_NAME, 'website-map'))
            )
            try_decline_cookie_notice(driver)
            map = driver.find_element_by_tag_name('website-map')
            zoom_in(driver, map, args.zoom)
            png = map.screenshot_as_png
    with tempfile.NamedTemporaryFile(dir=os.path.dirname(args.out), suffix='.' + os.path.basename(args.out)) as tmp:
        timestamp_image(png, tmp.name)
        os.rename(tmp.name, args.out)
        cast(Any, tmp)._closer.delete = False


if __name__ == '__main__':
    main()
