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
TRADER_WALLET = WalletConfig("Zl3pLs6Xk6SwIK7Jlp2x", "bJQDDVGAhKkj3PVCc7Rr")
RANDOM_WALLET = WalletConfig("OJpVLvU5fgLJbhNPdESa", "GmJTt9Gk34BHDlovB7AJ")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")
USER_WALLET = WalletConfig("MarketSim", "pin")

wallets = [MM_WALLET, MM_WALLET2, TRADER_WALLET,
           RANDOM_WALLET, TERMINATE_WALLET, USER_WALLET]


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
    print("TDAI: ", tdai_id)

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
    vega.mint(
        USER_WALLET.name,
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

    submit_order(vega, MM_WALLET, market_id, "SIDE_SELL", 1, 110)
    submit_order(vega, MM_WALLET2, market_id, "SIDE_BUY", 1, 90)
    submit_order(vega, MM_WALLET, market_id, "SIDE_SELL", 1, 105)
    submit_order(vega, MM_WALLET2, market_id, "SIDE_BUY", 1, 95)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/{market_id}")

    submit_order(vega, USER_WALLET, market_id, "SIDE_BUY", 1, 110)


def submit_order(vega, wallet, market_id, side, volume, price):
    vega.submit_order(
        trading_key=wallet.name,
        market_id=market_id,
        time_in_force="TIME_IN_FORCE_GTC",
        order_type="TYPE_LIMIT",
        side=side,
        volume=volume,
        price=price,
    )


def verify_market_data(page, data_test_id, expected_pattern):
    page.get_by_test_id(data_test_id).click()

    actual_text = page.query_selector('.ag-center-cols-container').inner_text()
    lines = actual_text.strip().split('\n')
    for expected, actual in zip(expected_pattern, lines):
        if re.match(r'^\\d', expected):  # check if it's a regex
            if re.search(expected, actual):
                print(f"Matched: {expected} == {actual}")
            else:
                print(f"Not Matched: {expected} != {actual}")
        else:  # it's not a regex, so we escape it
            if re.search(re.escape(expected), actual):
                print(f"Matched: {expected} == {actual}")
            else:
                print(f"Not Matched: {expected} != {actual}")

@pytest.mark.usefixtures("auth")
def test_limit_order_trade(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)
    # Assert that the user order is displayed on the orderbook
    orderbook_trade = page.get_by_test_id('price-11000000').nth(1)
    #orderbook_trade[1].click()
    expect(orderbook_trade).to_be_visible()

    # Swap to user wallet
    page.get_by_test_id('manage-vega-wallet').click(force=True)
    page.get_by_role("menuitemradio").filter(has_text="MarketSim").click()
    page.get_by_test_id('manage-vega-wallet').click(force=True)
    # Assert that open position exists

    expected_open_position = [
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
    verify_market_data(page, "Open", expected_open_position)
    
    vega.wait_for_total_catchup()
    vega.forward("10s")

    print("Assert Position:")
    # Assert that Position exists
    expected_position = [
        'BTC:DAI_Mar22',
        '107.50',
        '+1',
        '-',
        '0.00',
        'tDAI',
        '107.50',
        '0.0',
        '8.50269',
        '0.00',
        '0.00'
    ]
    verify_market_data(page, "Positions", expected_position )
    
    print("Assert Trades:")
    # Assert that trade exists
    expected_trade = [
        '107.50',
        '1',
        r'\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)'
    ]
    verify_market_data(page, "Trades", expected_trade)

    # Assert that the order is no longer on the orderbook
    page.get_by_test_id('Orderbook').click()
    price_element = page.get_by_test_id('price-11000000').nth(1)
    expect(price_element).to_be_hidden()

if __name__ == "__main__":
    pytest.main([__file__])
