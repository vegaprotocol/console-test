import pytest
import re
from playwright.sync_api import expect, Page
from vega_sim.service import VegaService

from playwright.sync_api import expect
from actions.vega import submit_order


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
        f'[data-testid^="tab-{data_test_id.lower()}"] >> .ag-center-cols-container .ag-row-first'
    ).text_content()
    lines = actual_text.strip().split("\n")
    for expected, actual in zip(expected_pattern, lines):
        # We are using regex so that we can run tests in different timezones.
        if re.match(r"^\\d", expected):  # check if it's a regex
            if re.search(expected, actual):
                print(f"Matched: {expected} == {actual}")
            else:
                print(f"Not Matched: {expected} != {actual}")
                raise AssertionError(f"Pattern does not match: {expected} != {actual}")
        else:  # it's not a regex, so we escape it
            if re.search(re.escape(expected), actual):
                print(f"Matched: {expected} == {actual}")
            else:
                print(f"Not Matched: {expected} != {actual}")
                raise AssertionError(f"Pattern does not match: {expected} != {actual}")


# Required so that we can get liquidation price - Could also become a helper
def wait_for_graphql_response(page, query_name, timeout=5000):
    response_data = {}

    def handle_response(route, request):
        if "graphql" in request.url:
            response = request.response()
            if response is not None:
                json_response = response.json()
                if json_response and "data" in json_response:
                    data = json_response["data"]
                    if query_name in data:
                        response_data["data"] = data
                        route.continue_()
                        return
        route.continue_()

    # Register the route handler
    page.route("**", handle_response)

    # Wait for the response data to be populated
    page.wait_for_timeout(timeout)

    # Unregister the route handler
    page.unroute("**", handle_response)


def submit_order(vega, wallet_name, market_id, side, volume, price):
    vega.submit_order(
        trading_key=wallet_name,
        market_id=market_id,
        time_in_force="TIME_IN_FORCE_GTC",
        order_type="TYPE_LIMIT",
        side=side,
        volume=volume,
        price=price,
    )

@pytest.mark.critical
@pytest.mark.usefixtures("opening_auction_market", "auth")
def test_limit_order_trade_open_order(
    opening_auction_market, vega: VegaService, page: Page
):
    market_id = opening_auction_market
    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 1, 110)

    page.goto(f"/#/markets/{market_id}")

    # Assert that the user order is displayed on the orderbook
    orderbook_trade = page.get_by_test_id("price-11000000").nth(1)
    # 6003-ORDB-001
    # 6003-ORDB-002
    expect(orderbook_trade).to_be_visible()

    expected_open_order = [
        "BTC:DAI_2023",
        "+1",
        "Limit",
        "Active",
        "0/1",
        "110.00",
        "Good 'til Cancelled (GTC)",
        r"\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)",
        "-",
    ]
    print("Assert Open orders:")
    verify_data_grid(page, "Open", expected_open_order)

@pytest.mark.critical
@pytest.mark.usefixtures("continuous_market", "auth")
def test_limit_order_trade_open_position(continuous_market, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    # Assert that Position exists - Will fail if the order is incorrect.
    expected_position = [
        "BTC:DAI_2023",
        "107.50",
        "+1",
        "107.50",
        "0.00",
        "tDAI",
        "107.50",
        "0.0",
        "8.50269",
        "0.00",
        "0.00",
    ]
    # 7004-POSI-001
    # 7004-POSI-002
    verify_data_grid(page, "Positions", expected_position)


@pytest.mark.usefixtures("continuous_market", "auth")
def test_limit_order_trade_order_trade_away(continuous_market, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    # Assert that the order is no longer on the orderbook
    page.get_by_test_id("Orderbook").click()
    price_element = page.get_by_test_id("price-11000000").nth(1)
    # 6003-ORDB-010
    expect(price_element).to_be_hidden()
