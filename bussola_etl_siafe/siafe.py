# pylint: disable=fixme, import-error, too-many-arguments

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

    This module maps SIAFE-Rio web interface to Python classes and methods.
"""

import os
import re
import sys
import time
from datetime import date, timedelta
from functools import cached_property
from typing import Mapping, Optional, Sequence, Union

import log  # type: ignore
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (  # NoSuchElementException,
    NoSuchAttributeException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import Select

from bussola_etl_siafe.components.filters import FilterMenu

load_dotenv("../.env")

sys.path.append(os.environ["CHROME_PATH"])


class SiafeClient:
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

    _greeting_statement_id = 'pt1:pt_aot1'
    _ug_select_id = 'pt1:selUg::content'
    _login_url: str = 'https://www5.fazenda.rj.gov.br/SiafeRio/faces/login.jsp'
    # _thematic_tab_ids: Mapping[str, str] = {
    #     'planning': 'pt1:pt_np4:0:pt_cni6::disclosureAnchor',
    #     'execution': 'pt1:pt_np4:1:pt_cni6::disclosureAnchor',
    #     'projects': 'pt1:pt_np4:2:pt_cni6::disclosureAnchor',
    #     'helpers': 'pt1:pt_np4:3:pt_cni6::disclosureAnchor',
    #     'administration': 'pt1:pt_np4:4:pt_cni6::disclosureAnchor',
    #     'reports': 'pt1:pt_np4:5:pt_cni6::disclosureAnchor',
    # }

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
        self._password = password
        self.fiscal_year = fiscal_year
        self.timeout = timeout

        log.debug('Starting Chrome WebDriver session...')
        self.driver = webdriver.Chrome(driver_path, options=driver_options)
        self.driver.implicitly_wait(self.timeout)
        self.driver.set_window_size(3840, 2160)

        log.info('Connecting to SIAFE-Rio Basic Module...')
        try:
            self._login()
        except (StaleElementReferenceException, TimeoutError):
            # Could not find greetings, something has gone wrong
            self.close()
            log.error(
                'An unexpected error occurred. Could not connect to SIAFE-Rio.'
            )
            raise ConnectionError
        else:
            log.info('Successfully signed in SIAFE-Rio Basic module.')

    def _login(self):
        """Interact with login form for SIAFE-Rio .

        Interacts with SIAFE-Rio login form, inputing user credentials,
        selecting the fiscal year and submiting the form.
        """
        login_form_ids: Mapping[str, str] = {
            'user_input': 'loginBox:itxUsuario::content',
            'password_input': 'loginBox:itxSenhaAtual::content',
            'fiscal_year_select': 'loginBox:cbxExercicio::content',
            'submit_button': 'loginBox:btnConfirmar',
        }
        self.driver.get(self._login_url)
        # insert user
        log.debug('Entering user ID')
        user_input = self.driver.find_element_by_id(
            login_form_ids['user_input']
        )
        user_input.send_keys(self.user)
        # select fiscal year
        log.debug(f'Selecting fiscal year ({self.fiscal_year})')
        fiscal_year_select = self.driver.find_element_by_id(
            login_form_ids['fiscal_year_select']
        )
        Select(fiscal_year_select).select_by_visible_text(
            str(self.fiscal_year)
        )
        # try to insert password
        for attempt in range(1, 4):
            try:
                log.debug(f'Entering user password ({attempt}/3)')
                password_input = self.driver.find_element_by_id(
                    login_form_ids['password_input']
                )
                password_value = password_input.get_attribute('value')
                assert len(password_value) == len(self._password)
                time.sleep(2)
            except (AssertionError, NoSuchAttributeException):
                password_input.send_keys(self._password)
        # submit
        log.debug('Submiting credentials')
        submit_button = self.driver.find_element_by_id(
            login_form_ids['submit_button']
        )
        submit_button.click()
        time.sleep(2)

    def greet(self) -> str:
        """Say Hello to user (for checking the connection)"""
        greetings = self.driver.find_element_by_id(
            self._greeting_statement_id
        ).text
        return greetings

    def reset(self):
        """Force driver to go back to initial page."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the current connection."""
        self.driver.close()

    @property
    def available_ugs(self) -> Sequence[Mapping[str, str]]:
        """Get available Managemet Units (UGs)."""
        log.info('Checking available budget Management Units...')
        ug_select = Select(self.driver.find_element_by_id(self._ug_select_id))
        ug_options = ug_select.options
        # UG visible text has the format '999999 - NAME OF THE UNIT'; split it
        ugs_splitted = [
            re.split(' +- +', ug_option.text, 1) for ug_option in ug_options
        ]
        # create a dict with UG name and id for each one
        available_ugs = list()
        for ug_splitted in ugs_splitted:
            if ug_splitted[0] == 'TODAS':
                # 'ALL' budget management units option
                available_ugs.append({'id': '000000', 'name': 'TODAS'})
            else:
                available_ugs.append(
                    {'id': ug_splitted[0], 'name': ug_splitted[1]}
                )
        # make available units accessible instance-wide
        self._available_ugs = available_ugs
        return self._available_ugs

    @property
    def ug(self) -> Mapping[str, str]:
        """Get current budget Management Unit (UG)."""
        log.info('Checking current Management Unit...')
        # current unit appears in the "title" attribute of the <select> element
        ug_select = self.driver.find_element_by_id(self._ug_select_id)
        ug_select_title = ug_select.get_attribute('title')
        if ug_select_title == 'TODAS':
            # 'ALL' budget management units option is selected (default)
            self._ug = {'id': '000000', 'name': 'TODAS'}
            return self._ug
        # A specific UG has been selected.
        # UG statement has the format '999999 - NAME OF THE UNIT'; split it
        ug_splitted = re.split(r' +- +', ug_select_title, 1)
        self._ug = {'id': ug_splitted[0], 'name': ug_splitted[1]}
        return self._ug

    def set_ug(self, ug_code: str = r'[0-9]{6}', ug_name: str = r'.*') -> None:
        """Set the desired Management Unit (UG).

        Arguments:
            ug_code: Six-digit numeric code of the budget Management Unit (UG).
            ug_name: Name of the budget Management Unit (UG), or a Perl-like
                regular expression for seaching for it (see
                docs.python.org/3/library/re for accepted expressions).

        Raises:
            ValueError: When no Management Unit is found for given code and/or
            name, or when multiple are found.

        Note:
            Please note that UG names are always uppercase. This method does
            not enforce this, as it might cause unexpected behaviors when
            using special sequences in regex.

        Warning:
            Currently, the budget Management Unit (UG) can be set only *after*
            the desired panel has been selected.
        """
        log.info('Changing budget Management Unit (UG)...')
        # find select menu in page
        ug_select = Select(self.driver.find_element_by_id(self._ug_select_id))
        # set 'ALL' management units option
        if ug_code == '000000' or ug_name.upper() == 'TODAS':
            log.debug('Selected ALL Management Units.')
            ug_select.select_by_visible_text('TODAS')
            self._ug = {'000000': 'TODAS'}
            log.info('Successfully set current view to all Management Units.')
            return
        # search option text that matches the given code and/or name
        log.debug('Searching Management Units that match the given pattern...')
        regexpr = re.compile(ug_code + r' +- +' + ug_name)
        ug_options = ug_select.options
        ug_options_texts = [ug_option.text for ug_option in ug_options]
        target_options_texts = list(filter(regexpr.match, ug_options_texts))
        # manage when number of matches != 1
        if len(target_options_texts) == 0:
            log.error(
                'No budget Management Unit was found with given criteria'
            )
            raise ValueError
        elif len(target_options_texts) > 1:
            log.error(
                'Multiple budget Management Units were found with given'
                + 'criteria:'
                + '\n'.join(target_options_texts)
            )
            raise ValueError
        else:
            # found one match. Now change in webdriver
            log.debug('Found exactly one match. Selecting...')
            ug_select.select_by_visible_text(target_options_texts[0])
            # update instance's UG attribute
            log.debug("Option selected. Updating client's attributes...")
            ug_splitted = re.split(r' +- +', target_options_texts[0], 1)
            self._ug = {'id': ug_splitted[0], 'name': ug_splitted[1]}
            log.info(
                'Successfully set current view to Management Unit '
                + self._ug['id']
                + ' - '
                + self._ug['name']
            )
            return

    @property
    def version(self) -> str:
        """Read only property with the SIAFE-Rio system version."""
        # TODO: get SIAFE-Rio system version in page footer.
        raise NotImplementedError
        return self.version

    @property
    def build(self) -> int:
        """Read only property with the SIAFE-Rio system build."""
        # TODO: get SIAFE-Rio system version in page footer.
        raise NotImplementedError
        return self.build

    @property
    def remaining_time(self) -> timedelta:
        """Read only property with the session's remaining time."""
        # TODO: get session's remaining time in page footer.
        raise NotImplementedError
        return self.remaining_time


class ExecutionPanel(SiafeClient):
    """SIAFE-Rio panel for budgetary and financial execution.

    This component contains the budgetary and financial execution. The
    budgetary execution is the usage of credit consigned in the Public Budget
    or in the Anual Budget Bill (LOA). The financial execution represents the
    usage of financial resources, to accomplish projects and/or activities
    attributed to the Budgetary Units by the Public Budget.
    """

    _tab_id = 'pt1:pt_np4:1:pt_cni6::disclosureAnchor'
    _subpanel_ids = {
        'budgetary': 'pt1:pt_np3:0:pt_cni4::disclosureAnchor',
        'financial': 'pt1:pt_np3:1:pt_cni4::disclosureAnchor',
        'accountancy': 'pt1:pt_np3:2:pt_cni4::disclosureAnchor',
        'contracts and covenants': 'pt1:pt_np3:3:pt_cni4::disclosureAnchor',
    }

    def __init__(self, client: SiafeClient):
        self.driver = client.driver
        tab = self.driver.find_element_by_id(self._tab_id)
        for attempt in range(1, 4):
            tab.click()  # access budget execution tab
            try:
                self.description  # check that panel description appeared
                break
            except StaleElementReferenceException:
                if attempt < 3:
                    log.debug(
                        'Could not access budget execution. '
                        + f'Try again... (attempt {attempt}/3)'
                    )
                    continue  # did not appear. Try again.
                else:
                    log.error('Could not access budget execution.')
                    raise

    @property
    def description(self):
        """Panel description"""
        description = self.driver.find_element_by_xpath(
            r"//div[@id='pt1:pt_pgl4::c']/span"
        ).text
        return description


class BudgetExecutionSubpanel(ExecutionPanel):
    """SIAFE-Rio subpanel for budgetary execution.

    Budget execution is the usage of credits consigned by the Public Budget or
    the Anual Budget Bill (LOA).
    """

    _table_ids = {
        'allocation_details': 'pt1:pt_np2:0:pt_cni3',
        'quota_releasing': 'pt1:pt_np2:1:pt_cni3',
        'credit_descentralization': 'pt1:pt_np2:2:pt_cni3',
        'credit_note': 'pt1:pt_np2:3:pt_cni3',
        'allocation_note': 'pt1:pt_np2:4:pt_cni3',
        'commitment_note': 'pt1:pt_np2:5:pt_cni3',
        'liquidation_note': 'pt1:pt_np2:6:pt_cni3',
        'reservation_note': 'pt1:pt_np2:7:pt_cni3',
        'predicted_revenue': 'pt1:pt_np2:8:pt_cni3',
    }

    def __init__(self, client: SiafeClient):
        ExecutionPanel.__init__(self, client)
        subpanel_tab = self.driver.find_element_by_id(
            self._subpanel_ids['budgetary']
        )
        subpanel_tab.click()


class CommitmentNotesTable(BudgetExecutionSubpanel):
    """A collection of Commitment Notes."""

    _cells_selector = ".xzv, .xzx"
    """CSS selector for cells with records data."""

    _filter_menu_id = 'pt1:tblDocumento:sdtFilter::body'
    """Element ID for the page <div> in which the "Filter menu" is contained.
    """

    _filter_menu_toggler_id = 'pt1:tblDocumento:sdtFilter::disAcr'
    """Element ID used for the button that toggles/collapses the filter menu.
    """

    _headers_class = 'x19p'
    """Class for table headers, containing the legible names of the fields."""

    _limit_checkbox_id = 'pt1:tblDocumento:chkRemoveLimit::content'
    """Element ID for the checkbox that enables or disables the limit in the
        number of observations shown in the table.
    """

    _loaded_table_class = "xza"
    """Class for the table with loaded records (with no headers)."""

    _rows_class = 'xzy'
    """Class for individual records in the table."""

    _scroller_id = "pt1:tblDocumento:tabViewerDec::scroller"
    """Element ID for the scrollable div where registries are shown.
    """

    def __init__(self, client=SiafeClient):
        BudgetExecutionSubpanel.__init__(self, client)
        table_link = self.driver.find_element_by_id(
            self._table_ids['commitment_note']
        )
        table_link.click()
        self.limit = False

    def _switch_limit(self) -> None:
        """Place/remove the limit on the number of displayed notes."""
        limit_checkbox = self.driver.find_element_by_id(
            self._limit_checkbox_id
        )
        limit_checkbox.click()

    @property
    def description(self):
        # tables do not have a description; overwrite parent's property
        self._description = None
        return self._description

    @property
    def limit(self) -> bool:
        """Get the current state of the number of notes displayed (limited or not)."""
        limit_checkbox = self.driver.find_element_by_id(
            self._limit_checkbox_id
        )
        limit_checkbox_status = limit_checkbox.get_attribute('checked')
        if limit_checkbox_status is None:
            self._limit = True
            return self._limit
        else:
            self._limit = False
            return self._limit

    @limit.setter
    def limit(self, value: bool) -> None:
        """Choose whether to show all notes (False) or only the first 1000 (True)."""
        if self.limit != value:
            self._switch_limit()
            self._limit = value

    @property
    def filter_menu(self):
        return FilterMenu(self)

    @cached_property
    def properties(self) -> Sequence[str]:
        """Get note properties."""
        table_headers = self.driver.find_elements_by_class_name(
            self._headers_class
        )
        properties = [column_header.text for column_header in table_headers]
        self._properties = properties
        return self._properties

    def _scroll(self) -> None:
        """Scroll records table, so that more records are loaded"""
        loaded_table = self.driver.find_element_by_class_name(
            self._loaded_table_class
        )
        scroll_by = loaded_table.size["height"]
        self.driver.execute_script(
            f"document.getElementById('{self._scroller_id}').scrollBy({{"
            + f"top: {scroll_by}, left: 0, behavior: 'smooth'}});"
        )
        time.sleep(5)

    @cached_property
    def records(self):
        """List all records for table."""

        # remove records limit
        self.limit = False

        records = list()
        while True:
            # save number of records before adding the ones in the screen
            records_num = len(records)

            # read records in the current screen
            loaded_table = self.driver.find_element_by_class_name(
                self._loaded_table_class
            )
            row_elements = loaded_table.find_elements_by_class_name(
                self._rows_class
            )
            for row_element in row_elements:
                record = dict()
                cell_elements = row_element.find_elements_by_css_selector(
                    self._cells_selector
                )
                cell_values = [
                    cell_element.text for cell_element in cell_elements
                ]
                # save to `records` variable
                for index, value in enumerate(cell_values):
                    property_ = self.properties[index]
                    record[property_] = value
                if record not in records:
                    records.append(record)
                    print(record)

            # check if anything new was added
            if len(records) == records_num:  # break if not
                break
            else:  # keep scrolling if so
                self._scroll()
                # BUG: Siafe reloads "Budgetary Execution" page instead of
                # fetching new records.

        return records
