import logging
import pytest
import re
from collections import namedtuple
from playwright.sync_api import expect

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")


wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]


def setup_continuous_market(vega, page):
    market_name = "BTC:DAI_Mar22"
    logging.basicConfig(level=logging.INFO)

    for wallet in wallets:
        vega.create_key(wallet.name)

    vega.mint(
        MM_WALLET.name,
        asset="VOTE",
        amount=1e4,
    )

    vega.update_network_parameter(
        MM_WALLET.name, parameter="market.fee.factors.makerFee", new_value="0.1"
    )

    vega.forward("10s")
    vega.wait_for_total_catchup()

    vega.create_asset(MM_WALLET.name, name="tDAI",
                      symbol="tDAI", decimals=5, max_faucet_amount=1e10)
    vega.wait_for_total_catchup()

    tdai_id = vega.find_asset_id(symbol="tDAI")

    vega.mint(
        "Key 1",
        asset=tdai_id,
        amount=100e5,
    )

    vega.mint(
        MM_WALLET.name,
        asset=tdai_id,
        amount=100e5,
    )
    vega.mint(
        MM_WALLET2.name,
        asset=tdai_id,
        amount=100e5,
    )

    vega.wait_fn(10)
    vega.wait_for_total_catchup()

    vega.create_simple_market(
        market_name,
        proposal_key=MM_WALLET.name,
        settlement_asset_id=tdai_id,
        termination_key=TERMINATE_WALLET.name,
        market_decimals=5,
    )
    vega.wait_for_total_catchup()

    market_id = vega.all_markets()[0].id

    vega.submit_simple_liquidity(
        key_name=MM_WALLET.name,
        market_id=market_id,
        commitment_amount=10000,
        fee=0.000,
        reference_buy="PEGGED_REFERENCE_MID",
        reference_sell="PEGGED_REFERENCE_MID",
        delta_buy=1,
        delta_sell=1,
        is_amendment=False,
    )

    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 1, 110)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 1, 90)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 1, 105)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 1, 95)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/{market_id}")

    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 1, 110)

    vega.wait_for_total_catchup()
    vega.forward("10s")


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


# Could be turned into a helper function in the future.
def verify_data_grid(page, data_test_id, expected_pattern):
    page.get_by_test_id(data_test_id).click()
    # Required so that we can get liquidation price
    if data_test_id == "Positions":
        wait_for_graphql_response(page, 'EstimatePosition')
    expect(page.locator(
        f'[data-testid^="tab-{data_test_id.lower()}"] >> .ag-center-cols-container .ag-row-first')).to_be_visible()
    actual_text = page.locator(
        f'[data-testid^="tab-{data_test_id.lower()}"] >> .ag-center-cols-container').text_content()
    lines = actual_text.strip().split('\n')
    for expected, actual in zip(expected_pattern, lines):
        # We are using regex so that we can run tests in different timezones.
        if re.match(r'^\\d', expected):  # check if it's a regex
            if re.search(expected, actual):
                print(f"Matched: {expected} == {actual}")
            else:
                print(f"Not Matched: {expected} != {actual}")
                raise AssertionError(
                    f"Pattern does not match: {expected} != {actual}")
        else:  # it's not a regex, so we escape it
            if re.search(re.escape(expected), actual):
                print(f"Matched: {expected} == {actual}")
            else:
                print(f"Not Matched: {expected} != {actual}")
                raise AssertionError(
                    f"Pattern does not match: {expected} != {actual}")


# Required so that we can get liquidation price - Could also become a helper
def wait_for_graphql_response(page, query_name, timeout=5000):
    response_data = {}

    def handle_response(route, request):
        if "graphql" in request.url:
            response = request.response()
            if response is not None:
                json_response = response.json()
                if json_response and 'data' in json_response:
                    data = json_response['data']
                    if query_name in data:
                        response_data['data'] = data
                        route.continue_()
                        return
        route.continue_()

    # Register the route handler
    page.route("**", handle_response)

    # Wait for the response data to be populated
    page.wait_for_timeout(timeout)

    # Unregister the route handler
    page.unroute("**", handle_response)


@pytest.mark.usefixtures("auth")
def test_limit_order_new_trade_top_of_list(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)
    market_id = vega.all_markets()[0].id
    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 1, 110)

    vega.wait_for_total_catchup()
    vega.forward("10s")
    expected_trade = [
        '103.50',
        '1',
        r'\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)'
        '107.50',
        '1',
        r'\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)'
    ]
    # 6005-THIS-001
    # 6005-THIS-002
    # 6005-THIS-003
    # 6005-THIS-004
    # 6005-THIS-005
    # 6005-THIS-006
    verify_data_grid(page, "Trades", expected_trade)


@pytest.mark.usefixtures("auth")
def test_price_copied_to_deal_ticket(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)
    page.get_by_test_id('Trades').click()
    wait_for_graphql_response(page, 'Trades')
    page.locator('[col-id=price]').last.click()
    # 6005-THIS-007
    expect(page.get_by_test_id('order-price')).to_have_value('107.50000')
