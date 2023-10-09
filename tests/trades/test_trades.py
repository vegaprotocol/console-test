from collections import namedtuple
from playwright.sync_api import Page, expect
import pytest
from datetime import datetime
from conftest import init_vega
from conftest import init_page
from fixtures.market import setup_continuous_market
from actions.vega import submit_multiple_orders, submit_liquidity


WALLET_CONFIG = namedtuple("WalletConfig", ["name", "passphrase"])
MM_WALLET = WALLET_CONFIG("mm", "pin")
MM_WALLET2 = WALLET_CONFIG("mm2", "pin2")
COL_HEADER = ".ag-header-cell-text"
COL_ID_PRICE = "[col-id=price]"
COL_ID_SIZE = "[col-id=size]"
COL_ID_CREATED_AT = "[col-id=createdAt]"
TRADES_TAB = "Trades"
TRADES_TABLE = "tab-trades"

@pytest.fixture(scope="module")
def vega(request):
    with init_vega(request) as vega:
        yield vega

@pytest.fixture(scope="module")
def continuous_market(vega):
    market_id = setup_continuous_market(vega)
    submit_liquidity(vega, MM_WALLET.name, market_id)
    submit_multiple_orders(
        vega,
        MM_WALLET.name,
        market_id,
        "SIDE_SELL",
        [[10, 130], [5, 110]],
    )
    submit_multiple_orders(
        vega,
        MM_WALLET2.name,
        market_id,
        "SIDE_BUY",
        [[10, 130], [5, 110]],
    )

    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()

    return market_id


@pytest.fixture(scope="module")
def page(vega, browser, request):
    with init_page(vega, browser, request) as page:
        yield page

@pytest.mark.usefixtures("risk_accepted", "auth")
def test_show_trades(continuous_market, page: Page):
    # 6005-THIS-001
    # 6005-THIS-002
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(TRADES_TAB).click()

    expect(page.get_by_test_id(TRADES_TAB)).to_be_visible()
    expect(page.get_by_test_id(TRADES_TAB)).to_be_visible()
    expect(page.get_by_test_id(TRADES_TAB)).not_to_be_empty()

@pytest.mark.usefixtures("risk_accepted", "auth")
def test_show_trades_prices(continuous_market,  page: Page):
    # 6005-THIS-003
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(TRADES_TAB).click()

    expect(page.get_by_test_id(TRADES_TABLE).locator(f"{COL_ID_PRICE} {COL_HEADER}").first).to_have_text("Price")
    trade_prices_elements = page.get_by_test_id(TRADES_TABLE).locator(COL_ID_PRICE).element_handles()
    
    for trade_price_element in trade_prices_elements:
        inner_text = trade_price_element.inner_text()
        assert inner_text, "The inner text should not be empty"

@pytest.mark.usefixtures("risk_accepted", "auth")
def test_show_trades_sizes(continuous_market, page: Page):
    # 6005-THIS-004
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(TRADES_TAB).click()

    expect(page.get_by_test_id(TRADES_TABLE).locator(f"{COL_ID_SIZE} {COL_HEADER}").first).to_have_text("Size")
    trade_prices_elements = page.get_by_test_id(TRADES_TABLE).locator(COL_ID_SIZE).element_handles()
    
    for trade_price_element in trade_prices_elements:
        inner_text = trade_price_element.inner_text()
        assert inner_text, "The inner text should not be empty"


@pytest.mark.usefixtures("risk_accepted", "auth")
def test_show_trades_date_and_time(continuous_market, page: Page):
    # 6005-THIS-005
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(TRADES_TAB).click()

    expect(page.get_by_test_id(TRADES_TABLE).locator(f"{COL_ID_CREATED_AT} {COL_HEADER}").first).to_have_text("Created at")
    trade_prices_elements = page.get_by_test_id(TRADES_TABLE).locator(COL_ID_CREATED_AT).element_handles()
    
    for trade_price_element in trade_prices_elements:
        inner_text = trade_price_element.inner_text()
        assert inner_text, "The inner text should not be empty"

@pytest.mark.usefixtures("risk_accepted", "auth")
def test_copy_price_to_deal_ticket_form(continuous_market, page: Page):
    # 6005-THIS-007
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(TRADES_TAB).click()

    page.get_by_test_id("order-type-Limit").click()
    last_price = float(page.locator(COL_ID_PRICE).last.inner_text())
    formatted_last_price = "{:.5f}".format(last_price)
    page.locator(COL_ID_PRICE).last.click()
    expect(page.get_by_test_id("order-price")).to_have_value(formatted_last_price)

@pytest.mark.usefixtures("risk_accepted", "auth")
def test_trades_are_sorted_descending_by_datetime(continuous_market, page: Page):
    # 6005-THIS-006
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(TRADES_TAB).click()

    datetime_elements = page.get_by_test_id(TRADES_TABLE).locator(COL_ID_CREATED_AT).element_handles()

    date_times = []
    for index, el in enumerate(datetime_elements):
        if index != 0:  # ignore header
            time_str = el.text_content()
            try:
                time_obj = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')  # Update format based on actual format
            except ValueError as e:
                print(f"Failed to parse time string {time_str}: {e}")
                continue
            date_times.append(time_obj)

    # Sort the array in descending order
    sorted_date_times = sorted(date_times, reverse=True)

    # Check that the sorted array is equal to the original
    assert date_times == sorted_date_times
