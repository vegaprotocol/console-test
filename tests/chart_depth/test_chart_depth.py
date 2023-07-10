import pytest
import logging
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


@pytest.mark.usefixtures("auth")
def test_see_market_depth_chart(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)

    # Click on the 'Depth' tab
    page.get_by_test_id('Depth').click()

    # Check if the 'Depth' tab and the depth chart are visible
    # 6006-DEPC-001
    expect(page.get_by_test_id('tab-depth')).to_be_visible()
    expect(page.locator('.depth-chart-module_canvas__260De').first).to_be_visible()
