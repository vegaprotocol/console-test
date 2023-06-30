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


def create_keys(vega):
    for wallet in wallets:
        vega.create_key(wallet.name)


def mint_amount(vega, wallet_name, asset, amount):
    vega.mint(wallet_name, asset=asset, amount=amount)


def update_network_parameter(vega, wallet_name, parameter, new_value):
    vega.update_network_parameter(
        wallet_name, parameter=parameter, new_value=new_value)


def verify_order_in_book(page, price_id):
    bid_bar_element = page.query_selector('[data-testid="bid-bar"]')

    if bid_bar_element:
        price_element = bid_bar_element.query_selector(
            f'[data-testid="{price_id}"]')

        if price_element:
            expect(price_element).to_be_visible()


def manage_vega_wallet(page, wallet_name):
    page.query_selector('[data-testid="manage-vega-wallet"]').click()
    page.query_selector(
        f'[data-testid="keypair-list"] div[role="menuitemradio"]:has-text("{wallet_name}")').click()
    page.query_selector('[data-testid="manage-vega-wallet"]').click(force=True)


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


def navigate_to_market(page, vega, market_name, market_id):
    page.goto(f"http://localhost:{vega.console_port}/#/markets/{market_id}")
    result = page.get_by_text(market_name)
    result.first.click()


def check_order_hidden(page, price):
    page.query_selector('[data-testid="Orderbook"]').click()
    bid_bar_element = page.query_selector('[data-testid="bid-bar"]')

    if bid_bar_element:
        price_element = bid_bar_element.query_selector(
            f'[data-testid="price-{price}"]')

        if price_element:
            # Assert Order should not be displayed on the book
            expect(price_element).to_be_hidden()


def verify_market_data(page, data_test_id, expected_pattern):
    page.get_by_test_id(data_test_id).click()
    row = page.query_selector(
        f'[data-testid="{data_test_id}"] .ag-center-cols-container .ag-row')

    if row:
        actual_text = row.evaluate("""
            element => Array.from(element.children).filter(e => e.tagName === 'DIV').map(e => e.textContent.trim()).join(' ')
        """)
        print(
            f"{data_test_id}: Expected Text: {expected_pattern} actual Text: {actual_text}")
        assert re.fullmatch(
            expected_pattern, actual_text), f"{data_test_id} Expected match to pattern: '{expected_pattern}', but got: '{actual_text}'"


@pytest.mark.usefixtures("auth")
def test_order_match2(vega, page):
    market_name = "BTC:DAI_Mar22"
    logging.basicConfig(level=logging.INFO)

    create_keys(vega)

    mint_amount(vega, MM_WALLET.name, "VOTE", 1e4)

    update_network_parameter(vega, MM_WALLET.name,
                             "market.fee.factors.makerFee", "0.1")

    vega.forward("10s")
    vega.wait_for_total_catchup()

    vega.create_asset(MM_WALLET.name, name="tDAI",
                      symbol="tDAI", decimals=5, max_faucet_amount=1e10)
    vega.wait_for_total_catchup()

    tdai_id = vega.find_asset_id(symbol="tDAI")
    print("TDAI: ", tdai_id)

    mint_amount(vega, MM_WALLET.name, tdai_id, 100e5)
    mint_amount(vega, MM_WALLET2.name, tdai_id, 100e5)
    mint_amount(vega, USER_WALLET.name, tdai_id, 100e5)

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

    navigate_to_market(page, vega, market_name, market_id)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    submit_order(vega, USER_WALLET, market_id, "SIDE_BUY", 1, 110)

    verify_order_in_book(page, 'price-11000000')

    manage_vega_wallet(page, 'MarketSim')

    verify_market_data(
        page, "Open", r"BTC:DAI_Mar22 \+1 Limit Active 0\/1 110\.00 Good 'til Cancelled \(GTC\) 5\/9\/2023, \d{1,2}:\d{2}:\d{2} AM -")

    vega.wait_for_total_catchup()
    vega.forward("10s")

    verify_market_data(
        page, "Trades", r"107.50 1 5/9/2023, \d{1,2}:\d{2}:\d{2} AM")
    verify_market_data(
        page, "Positions", 'BTC:DAI_Mar22 107.50 +1 - 0.00 tDAI 107.50 0.0 8.50269 0.00 0.00')
    check_order_hidden(page, 11000000)

    print("END")


if __name__ == "__main__":
    pytest.main([__file__])
