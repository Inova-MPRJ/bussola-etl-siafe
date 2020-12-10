import log
import os
from pathlib import Path

import pytest
from selenium.webdriver.chrome.options import Options as ChromeOptions

from bussola_etl_siafe.siafe import ConnectionBasic


USER: str = os.getenv('SIAFE_USER')
PASSWORD: str = os.getenv('SIAFE_PASSWORD')
CHROME_PATH: str = os.getenv('CHROME_PATH', './chromedriver')
CHROME_OPTIONS = ChromeOptions()
CHROME_OPTIONS.headless = False


log.init(verbosity=3)
CHROME_OPTIONS.add_argument("--remote-debugging-port=9515")


def test_connect() -> None:
    """Tests whether it is possible to connect and sign in SIAFE-Rio Basic."""
    # create connection
    assert os.path.isfile(CHROME_PATH)
    conn = ConnectionBasic(
        user=USER,
        password=PASSWORD,
        driver_path=CHROME_PATH,
        driver_options=CHROME_OPTIONS,
    )
    driver = conn.driver
    # assert that a welcome message is shown
    print(conn.greet())
    assert 'Seja bem-vindo(a),' in conn._greetings
    # assert that fiscal year equals to the current year 
    # (default behavior when no year is specified)  
    year_statement = driver.find_element_by_id('pt1:pt_aot2').text
    assert year_statement == 'Exercício 2020'
    # assert that connection throws an exception when unimplemented 
    # properties and methods are accessed
    with pytest.raises(NotImplementedError):
        conn.version
    with pytest.raises(NotImplementedError):
        conn.build
    with pytest.raises(NotImplementedError):
        conn.remaining_time
    # close connection
    driver.close()
