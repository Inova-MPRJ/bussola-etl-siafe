# Copyright 2020 Ministério Público do Estado do Rio de Janeiro

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Interfaces for interacting with SIAFE-Rio in an automated way.

    Rio de Janeiro's Integrated System for Budget Management (SIAFE-Rio) is the
    main tool for recording, monitoring and enforcing information regarding to 
    the State of Rio de Janeiro's public budget, assets and financial 
    execution.

    This module maps SIAFE-Rio web interface to Python classes and 
"""


import os
import log
import time
from datetime import date, timedelta
from enum import Enum
from typing import Mapping, Union, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchAttributeException
)
from selenium.webdriver.support.ui import Select


class ConnectionBasic():
    """Chrome WebDriver signed in SIAFE-Rio Basic Module.

    SIAFE-Rio Basic Module provides the most commonly used information in the
    system as standardized tables and reports. This class uses the provided 
    credentials and a Chrome WebDriver (controlled by Selenium) to establish a
    connection and sign in the Basic Module, providing an automated interface
    to interact with the system.
    
    Arguments:
        user: User name or number in SIAFE system (usually, the user's Natural 
            Person Registry number - CPF).
        password: User password in SIAFE system.
        driver_path: Path to the ChromeDriver executable (available at 
            https://sites.google.com/a/chromium.org/chromedriver/downloads).
        
    Keyword Arguments:
        fiscal_year: Fiscal year for budget planning and execution. Defaults to
            the current year.
        timeout: Maximum time to wait for an element while browsing the page
            (in seconds). Defaults to 10 seconds.
    
    Attributes:
        driver: Chrome WebDriver logged in SIAFE with provided credentials.
        build: SIAFE-Rio current build. Not implemented yet.
        fiscal_year: Fiscal year for budget planning and execution information
            shown in the system.
        remaining_time: Remaining time for the current session. Not implemented
            yet.
        timeout: Maximum time to wait for an element while browsing the page
            (in seconds).
        user: User name or number currently signed in the SIAFE system.
        version: SIAFE-Rio current version. Not implemented yet.

    Raises:
        NotImplementedError: When a method or attribute that is not 
            implemented yet is called.
        TimeoutException: If an element cannot be located after the specified 
            timeout.
    """
    
    _login_url: str = 'https://www5.fazenda.rj.gov.br/SiafeRio/faces/login.jsp'
    _login_form_ids: Mapping[str, str] = {
        'user_input': 'loginBox:itxUsuario::content',
        'password_input': 'loginBox:itxSenhaAtual::content',
        'fiscal_year_select': 'loginBox:cbxExercicio::content',
        'submit_button': 'loginBox:btnConfirmar',
    }
    _homepage_ids: Mapping[str, str] = {
        'greeting_statement': 'pt1:pt_aot1',
    }
    
    def __init__(
        self,
        user: str,
        password: str,
        driver_path: Union[str, bytes, os.PathLike],
        driver_options: Optional[ChromeOptions] = None,
        fiscal_year: int = date.today().year,
        timeout: int = 10,
    ):
        self.user = user
        self.__password = password
        self.fiscal_year = fiscal_year
        self.timeout = timeout
        log.debug('Starting Chrome WebDriver session...')
        self.driver = webdriver.Chrome(driver_path, options=driver_options)
        self.driver.implicitly_wait(self.timeout)
        log.info('Connecting to SIAFE-Rio Basic Module...')
        self._login()
        time.sleep(5)
        try:
            self._greetings = self.driver.find_element_by_id(
                    self._homepage_ids['greeting_statement']
            ).text
        except (StaleElementReferenceException, TimeoutError):
            # Could not find greetings, something has gone wrong
            driver.close()
            log.error(
                'An unexpected error occurred. ' + 
                'Could not connect to SIAFE-Rio.'
            )
            raise ConnectionError
        else:
            log.info('Successfully signed in SIAFE-Rio Basic module!')

    def _login(self):
        """Interact with login form for SIAFE-Rio .
        
        Interacts with SIAFE-Rio login form, inputing user credentials, 
        selecting the fiscal year and submiting the form.
        """
        self.driver.get(self._login_url)
        # insert user
        log.debug('Entering user ID')
        user_input = self.driver.find_element_by_id(
            self._login_form_ids['user_input'])
        user_input.send_keys(self.user)
        # select fiscal year
        log.debug(f'Selecting fiscal year ({self.fiscal_year})')
        fiscal_year_select = self.driver.find_element_by_id(
            self._login_form_ids['fiscal_year_select'])
        Select(fiscal_year_select).select_by_visible_text(
            str(self.fiscal_year))
        # try to insert password
        log.debug('Entering user password')
        for attempt in range(1, 4):
            try:
                password_input = self.driver.find_element_by_id(
                    self._login_form_ids['password_input'])
                password_value = password_input.get_attribute('value')
                assert len(password_value) == len(self.__password)
                time.sleep(5)
            except (AssertionError, NoSuchAttributeException) as e:
                password_input.send_keys(self.__password)
        # submit
        log.debug('Submiting credentials')
        submit_button = self.driver.find_element_by_id(
            self._login_form_ids['submit_button'])
        submit_button.click()
        time.sleep(5)

    def greet(self):
        """Say Hello to user (for checking the connection)"""
        return self._greetings

    @property
    def version(self) -> str:
        """Read only property with the SIAFE-Rio system version."""
        # TODO: get SIAFE-Rio system version in page footer.
        raise NotImplementedError
        return self._version

    @property
    def build(self) -> int:
        """Read only property with the SIAFE-Rio system build."""
        # TODO: get SIAFE-Rio system version in page footer.
        raise NotImplementedError
        return self._build

    @property
    def remaining_time(self) -> timedelta:
        """Read only property with the session's remaining time."""
        # TODO: get session's remaining time in page footer.
        raise NotImplementedError
        return self._remaining_time


class ConnectionFlexvision():
    """Chrome WebDriver signed in SIAFE-Rio Flexvision Module.

    SIAFE-Rio Flexvision provides tools to query and create custom reports 
    based on State-level budgetary, financial and patrimonial information, 
    available in a data cube model.
    
    Arguments:
        user: User name or number in SIAFE system (usually, the user's Natural 
            Person Registry number - CPF).
        password: User password in SIAFE system.
        driver_path: Path to the ChromeDriver executable (available at 
            https://sites.google.com/a/chromium.org/chromedriver/downloads).

    Raises:
        NotImplementedError: This class is not implemented yet.
    """

    login_url:str = 'http://flexvision.fazenda.rj.gov.br:7002/Flexvision/faces/login.jsp'

    def __init__(
        self,
        username: str,
        password: str,
        driver_path: Union[str, bytes, os.PathLike]
    ):
        raise NotImplementedError