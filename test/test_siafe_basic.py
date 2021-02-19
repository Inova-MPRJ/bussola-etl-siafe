import os
from datetime import date
from pathlib import Path

import log
import pytest
from selenium.webdriver.chrome.options import Options

from bussola_etl_siafe.components.filters import Filter
from bussola_etl_siafe.siafe import (
    BudgetExecutionSubpanel,
    CommitmentNotesTable,
    ExecutionPanel,
    SiafeClient,
)

REPO_ROOT = Path(os.path.realpath(__file__)).parent.parent
USER: str = os.environ['SIAFE_USER']
PASSWORD: str = os.environ['SIAFE_PASSWORD']
FECAM_CODE: str = '240400'
BUDGET_SOURCE: str = "104"

DRIVER_PATH = os.getenv('CHROME_PATH', os.path.join(REPO_ROOT, "chromedriver"))
DRIVER_OPTIONS = Options()
DRIVER_OPTIONS.add_argument("--remote-debugging-port=9515")

DRIVER_OPTIONS.headless = False

log.init(verbosity=3)


@pytest.fixture(scope='module')
def siafe():
    """Creates a reusable connection to Siafe Basic"""
    # create connection
    client = SiafeClient(
        user=USER,
        password=PASSWORD,
        driver_path=DRIVER_PATH,
        driver_options=DRIVER_OPTIONS,
    )
    try:
        # use connection in tests
        yield client
    finally:
        # teardown connection after all tests in module finish
        client.close()


@pytest.fixture(scope="module")
def commitment_note_page(siafe):
    page = CommitmentNotesTable(client=siafe)
    return page


def test_homepage(siafe) -> None:
    """Tests if it is possible to view SIAFE-Rio homepage after connecting."""
    # assert that a welcome message is shown
    greeting = siafe.greet()
    assert 'Seja bem-vindo(a),' in greeting
    # assert that fiscal year equals to the current year
    # (default behavior when no year is specified)
    year_statement = siafe.driver.find_element_by_id('pt1:pt_aot2').text
    assert year_statement == 'Exercício ' + str(date.today().year)
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


def test_execution(siafe) -> None:
    """Tests getting the budgetary and financial execution panel."""
    panel = ExecutionPanel(client=siafe)
    descr = panel.description
    print(descr)
    assert 'Este módulo permite a execução orçamentária e financeira.' in descr
    for subpanel_id in panel._subpanel_ids.values():
        subpanel_tab = panel.driver.find_element_by_id(subpanel_id)
        assert subpanel_tab.is_displayed()


def test_budget_execution(siafe) -> None:
    """Tests getting the budgetary execution subpanel."""
    subpanel = BudgetExecutionSubpanel(client=siafe)
    descr = subpanel.description
    print(descr)
    assert 'A execução orçamentária é a utilização dos créditos' in descr
    for table_id in subpanel._table_ids.values():
        table_link = subpanel.driver.find_element_by_id(table_id)
        assert table_link.is_displayed()


def test_commitment_table(commitment_note_page) -> None:
    """Tests fetching the commitment notes table."""
    assert not commitment_note_page.limit
    headers = commitment_note_page.properties
    assert 'Número' in headers
    assert 'Credor' in headers
    assert 'Valor' in headers


def test_empty_filters(commitment_note_page) -> None:
    """Tests checking for filters when none was set yet."""
    filters = commitment_note_page.filter_menu.filters
    print(filters)
    assert isinstance(filters, list)
    assert len(filters) == 0


def test_set_filters(commitment_note_page) -> None:
    """Test applying a new filter to the commitment notes table."""
    new_filter = Filter(
        filtered_property="Fonte", operation="igual", value=BUDGET_SOURCE
    )
    commitment_note_page.filter_menu.filters = new_filter
    commitment_note_page.filter_menu.apply()
    assert (
        new_filter in commitment_note_page.filter_menu.filters  # type:ignore
    )
    # BUG: for some reason, mypy thinks filter_menu.filters is a Filter, not
    # a list of Filters. May be related to
    # https://github.com/python/mypy/issues/3004


# def test_commitment_records(siafe) -> None:
#     """Tests reading commitment notes records from screen."""
#     table = CommitmentNotesTable(client=siafe)
#     records = table.records
#     assert len(records) > 0


# def test_get_available_ugs(siafe) -> None:
#     """Tests getting available budget Management Units (UGs)."""
#     available_ugs = siafe.available_ugs
#     assert {'id': FECAM_CODE, 'name': 'FECAM'} in available_ugs


# def test_set_ug(siafe) -> None:
#     """Tests changing current budget Management Unit (UG)."""
#     siafe.set_ug(ug_code=FECAM_CODE)
#     ug = siafe.ug
#     assert ug['id'] == FECAM_CODE
#     assert ug['name'] == 'FECAM'
