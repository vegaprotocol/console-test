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
    # Required so that we can get liquidation price
    page.pause()
    if data_test_id == "Positions":
        wait_for_graphql_response(page, 'EstimatePosition')

    page.get_by_test_id(data_test_id).click()
    expect(page.locator(
        f'[data-testid^="tab-{data_test_id.lower()}"] >> .ag-center-cols-container .ag-row-first')).to_be_visible()
    actual_text = page.locator(
        f'[data-testid^="tab-{data_test_id.lower()}"] >> .ag-center-cols-container .ag-row-first').inner_text()
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


def wait_for_graphql_response(page, query_name, timeout=500):
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
def test_limit_order_trade_open_order(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)
    # Assert that the user order is displayed on the orderbook
    orderbook_trade = page.get_by_test_id('price-11000000').nth(1)

    # 6003-ORDB-001
    # 6003-ORDB-002
    expect(orderbook_trade).to_be_visible()

    expected_open_order = [
        'BTC:DAI_Mar22',
        '+1',
        'Limit',
        'Active',
        '0/1',
        '110.00',
        "Good 'til Cancelled (GTC)",
        r'\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)',
        '-'
    ]
    verify_data_grid(page, "Open", expected_open_order)


@pytest.mark.usefixtures("auth")
def test_limit_order_trade_open_position(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    print("Assert Position:")
    # Assert that Position exists - Will fail if the order is incorrect.
    expected_position = [
        'BTC:DAI_Mar22',
        '107.50',
        '+1',
        '107.50',
        '0.00',
        'tDAI',
        '107.50',
        '0.0',
        '8.50269',
        '0.00',
        '0.00'
    ]
    # 7004-POSI-001
    # 7004-POSI-002
    verify_data_grid(page, "Positions", expected_position)


@pytest.mark.usefixtures("auth")
def test_limit_order_trade(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)

    vega.wait_for_total_catchup()
    vega.forward("10s")
    print("Assert Trades:")
    # Assert that trade exists - Will fail if the order is incorrect.
    expected_trade = [
        '107.50',
        '1',
        r'\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)'
    ]
    # 6005-THIS-001
    # 6005-THIS-002
    # 6005-THIS-003
    # 6005-THIS-004
    # 6005-THIS-005
    verify_data_grid(page, "Trades", expected_trade)


@pytest.mark.usefixtures("auth")
def test_limit_order_trade_order_trde_away(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)

    vega.wait_for_total_catchup()
    vega.forward("10s")
    # Assert that the order is no longer on the orderbook
    page.get_by_test_id('Orderbook').click()
    price_element = page.get_by_test_id('price-11000000').nth(1)
    # 6003-ORDB-010
    expect(price_element).to_be_hidden()
