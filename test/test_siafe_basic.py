import os

import log
import pytest
from selenium.webdriver.chrome.options import Options as ChromeOptions

from bussola_etl_siafe.siafe import ExecutionPanel, SiafeClient

USER: str = os.environ['SIAFE_USER']
PASSWORD: str = os.environ['SIAFE_PASSWORD']
CHROME_PATH: str = os.getenv('CHROME_PATH', './chromedriver')
CHROME_OPTIONS = ChromeOptions()
CHROME_OPTIONS.headless = True
FECAM_CODE: str = '240400'


log.init(verbosity=3)
CHROME_OPTIONS.add_argument("--remote-debugging-port=9515")


@pytest.fixture(scope='module')
def siafe():
    """Creates a reusable connection to Siafe Basic"""
    # create connection
    client = SiafeClient(
        user=USER,
        password=PASSWORD,
        driver_path=CHROME_PATH,
        driver_options=CHROME_OPTIONS,
    )
    # use connection in tests
    yield client
    # teardown connection after all tests in module finish
    client.close()


def test_homepage(siafe) -> None:
    """Tests if it is possible to view SIAFE-Rio homepage after connecting."""
    # assert that a welcome message is shown
    greeting = siafe.greet()
    assert 'Seja bem-vindo(a),' in greeting
    # assert that fiscal year equals to the current year
    # (default behavior when no year is specified)
    year_statement = siafe.driver.find_element_by_id('pt1:pt_aot2').text
    assert year_statement == 'Exercício 2020'
    assert siafe.ug['name'] == 'TODAS'
    # TODO: replace with assertions, when properties are implemented
    # assert that connection throws an exception when unimplemented
    # properties and methods are accessed
    with pytest.raises(NotImplementedError):
        siafe.version
    with pytest.raises(NotImplementedError):
        siafe.build
    with pytest.raises(NotImplementedError):
        siafe.remaining_time


def test_budget_execution(siafe) -> None:
    """Tests getting the budget execution panel."""
    panel = ExecutionPanel(client=siafe)
    descr = panel.description
    print(descr)
    assert 'Este módulo permite a execução orçamentária e financeira.' in descr


def test_get_available_ugs(siafe) -> None:
    """Tests getting available budget Management Units (UGs)."""
    available_ugs = siafe.available_ugs
    assert {'id': FECAM_CODE, 'name': 'FECAM'} in available_ugs


def test_set_ug(siafe) -> None:
    """Tests changing current budget Management Unit (UG)."""
    siafe.set_ug(ug_code=FECAM_CODE)
    ug = siafe.ug
    assert ug['id'] == FECAM_CODE
    assert ug['name'] == 'FECAM'
