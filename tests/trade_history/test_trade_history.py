import pytest
import re
from playwright.sync_api import expect
from actions.vega import submit_order
from conftest import init_vega
from actions.utils import wait_for_graphql_response
import logging

logger = logging.getLogger()


@pytest.fixture(scope="module")
def vega():
    with init_vega() as vega:
        yield vega


# Could be turned into a helper function in the future.
def verify_data_grid(page, data_test_id, expected_pattern):
    page.get_by_test_id(data_test_id).click()
    # Required so that we can get liquidation price
    if data_test_id == "Positions":
        wait_for_graphql_response(page, "EstimatePosition")
    expect(
        page.locator(
            f'[data-testid^="tab-{data_test_id.lower()}"] >> .ag-center-cols-container .ag-row-first'
        )
    ).to_be_visible()
    actual_text = page.locator(
        f'[data-testid^="tab-{data_test_id.lower()}"] >> .ag-center-cols-container'
    ).text_content()
    lines = actual_text.strip().split("\n")
    for expected, actual in zip(expected_pattern, lines):
        # We are using regex so that we can run tests in different timezones.
        if re.match(r"^\\d", expected):  # check if it's a regex
            if re.search(expected, actual):
                logger.info(f"Matched: {expected} == {actual}")
            else:
                logger.info(f"Not Matched: {expected} != {actual}")
                raise AssertionError(f"Pattern does not match: {expected} != {actual}")
        else:  # it's not a regex, so we escape it
            if re.search(re.escape(expected), actual):
                logger.info(f"Matched: {expected} == {actual}")
            else:
                logger.info(f"Not Matched: {expected} != {actual}")
                raise AssertionError(f"Pattern does not match: {expected} != {actual}")

@pytest.mark.usefixtures("page", "continuous_market", "auth", "risk_accepted")
def test_limit_order_new_trade_top_of_list(continuous_market, vega, page):
    submit_order(vega, "Key 1", continuous_market, "SIDE_BUY", 1, 110)
    page.goto(f"/#/markets/{continuous_market}")

    vega.forward("10s")
    vega.wait_fn(10)
    vega.wait_for_total_catchup()
    expected_trade = [
        "103.50",
        "1",
        r"\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)" "107.50",
        "1",
        r"\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)",
    ]
    # 6005-THIS-001
    # 6005-THIS-002
    # 6005-THIS-003
    # 6005-THIS-004
    # 6005-THIS-005
    # 6005-THIS-006
    verify_data_grid(page, "Trades", expected_trade)


@pytest.mark.usefixtures("page", "continuous_market", "auth", "risk_accepted")
def test_price_copied_to_deal_ticket(continuous_market, page):
    page.goto(f"/#/markets/{continuous_market}")
    page.get_by_test_id("Trades").click()
    wait_for_graphql_response(page, "Trades")
    page.locator("[col-id=price]").last.click()
    # 6005-THIS-007
    expect(page.get_by_test_id("order-price")).to_have_value("107.50000")
