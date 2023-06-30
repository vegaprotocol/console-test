import logging
import pytest

from collections import namedtuple
from playwright.sync_api import Page, expect


WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Set up parties in the market/ Submit liquidity provision/ Control midprice
MM_WALLET = WalletConfig("mm", "pin")

TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, TERMINATE_WALLET]


# Use auth fixture in conftest.py but we don't need the actual return value

def test_open_market(vega, page):
    row_selector = '[data-testid="tab-all-markets"] .ag-center-cols-container .ag-row'
    trading_mode_col = '[col-id="tradingMode"]'
    state_col = '[col-id="state"]'
    initial_commitment: float = 100
    mint_amount: float = 10000
    initial_price: float = 1
    initial_volume: float = 1
    initial_spread: float = 0.1

    market_name = "BTC:DAI_YYYYYYYYY"
    logging.basicConfig(level=logging.INFO)

    for wallet in wallets:
        vega.create_key(wallet.name)

    vega.mint(
        MM_WALLET.name,
        asset="VOTE",
        amount=mint_amount,
    )

    vega.update_network_parameter(
        MM_WALLET.name, parameter="market.fee.factors.makerFee", new_value="0.1"
    )
    vega.forward("10s")
    vega.wait_for_total_catchup()

    vega.create_asset(
        MM_WALLET.name,
        name="tDAI",
        symbol="tDAI",
        decimals=5,
        max_faucet_amount=1e10,
    )

    vega.wait_for_total_catchup()
    tdai_id = vega.find_asset_id(symbol="tDAI")
    print("TDAI: ", tdai_id)

    vega.mint(
        MM_WALLET.name,
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

    vega.forward("10s")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/all")
    page.get_by_text("continue").click()
    expect(page.locator(row_selector).locator(trading_mode_col)
           ).to_have_text("Opening auction")
    expect(page.locator(row_selector).locator('[col-id="state"]')
           ).to_have_text("Pending")

    vega.submit_liquidity(
        key_name=MM_WALLET.name,
        market_id=market_id,
        commitment_amount=initial_commitment,
        fee=0.002,
        buy_specs=[("PEGGED_REFERENCE_MID", 0.0005, 1)],
        sell_specs=[("PEGGED_REFERENCE_MID", 0.0005, 1)],
        is_amendment=False,
    )

    vega.submit_order(
        trading_key=MM_WALLET.name,
        market_id=market_id,
        order_type="TYPE_LIMIT",
        time_in_force="TIME_IN_FORCE_GTC",
        side="SIDE_BUY",
        volume=initial_volume,
        price=initial_price,
    )

    vega.submit_order(
        trading_key=MM_WALLET.name,
        market_id=market_id,
        order_type="TYPE_LIMIT",
        time_in_force="TIME_IN_FORCE_GTC",
        side="SIDE_SELL",
        volume=initial_volume,
        price=initial_price,
    )

    vega.submit_order(
        trading_key=MM_WALLET.name,
        market_id=market_id,
        order_type="TYPE_LIMIT",
        time_in_force="TIME_IN_FORCE_GTC",
        side="SIDE_BUY",
        volume=initial_volume,
        price=initial_price - initial_spread / 2,
    )

    vega.submit_order(
        trading_key=MM_WALLET.name,
        market_id=market_id,
        order_type="TYPE_LIMIT",
        time_in_force="TIME_IN_FORCE_GTC",
        side="SIDE_SELL",
        volume=initial_volume,
        price=initial_price + initial_spread / 2,
    )

    vega.wait_for_total_catchup()

    vega.forward("10s")

    expect(page.locator(row_selector).locator(trading_mode_col)
           ).to_have_text("Continuous")
    # issue
    # expect(page.locator(row_selector).locator(state_col)
    #        ).to_have_text("Pending")

    # Navigate to chosen market
    result = page.get_by_text(market_name)
    result.first.click()
    assert market_id in page.url
    expect(page.get_by_text(market_name).first).to_be_attached()
    expect(page.get_by_test_id(
        "market-trading-mode").get_by_test_id("item-value")).to_have_text("Continuous")
    expect(page.get_by_test_id(
        "market-state").get_by_test_id("item-value")).to_have_text("Active")
    # issue
    # expect(page.get_by_text("Opening auction")).to_be_hidden()

    print("END")


if __name__ == "__main__":
    pytest.main([__file__])
