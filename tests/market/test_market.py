from collections import namedtuple
from playwright.sync_api import Page, expect
from market_fixtures.simple_market.simple_market import setup_simple_market

# Wallet Configurations
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]

row_selector = '[data-testid="tab-all-markets"] .ag-center-cols-container .ag-row'
trading_mode_col = '[col-id="tradingMode"]'
state_col = '[col-id="state"]'

initial_commitment: float = 100
mint_amount: float = 10000
initial_price: float = 1
initial_volume: float = 1
initial_spread: float = 0.1
market_name = "BTC:DAI_YYYYYYYYY"


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


def test_open_market(setup_simple_market, vega, page):
    market_id = vega.all_markets()[0].id
    page.goto(f"http://localhost:{vega.console_port}/#/markets/all")
    page.get_by_text("continue").click()
    expect(page.locator(row_selector).locator(trading_mode_col)
           ).to_have_text("Opening auction")
    expect(page.locator(row_selector).locator('[col-id="state"]')
           ).to_have_text("Pending")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/")
    result = page.get_by_text(market_name)
    result.first.click()
    page.get_by_test_id(
        "market-trading-mode").get_by_text("Opening auction").hover()
    expect(page.get_by_test_id("opening-auction-sub-status").first).to_have_text(
        "Opening auction: Not enough liquidity to open")

    vega.submit_liquidity(
        key_name=MM_WALLET.name,
        market_id=market_id,
        commitment_amount=initial_commitment,
        fee=0.002,
        buy_specs=[("PEGGED_REFERENCE_MID", 0.0005, 1)],
        sell_specs=[("PEGGED_REFERENCE_MID", 0.0005, 1)],
        is_amendment=False,
    )

    submit_order(vega, MM_WALLET, market_id, "SIDE_BUY",
                 initial_volume, initial_price)
    submit_order(vega, MM_WALLET, market_id, "SIDE_SELL",
                 initial_volume, initial_price)
    submit_order(vega, MM_WALLET, market_id, "SIDE_BUY",
                 initial_volume, initial_price + initial_spread / 2)
    submit_order(vega, MM_WALLET, market_id, "SIDE_SELL",
                 initial_volume, initial_price + initial_spread / 2)
    submit_order(vega, MM_WALLET2, market_id, "SIDE_SELL",
                 initial_volume, initial_price)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/all")
    expect(page.locator(row_selector).locator(trading_mode_col)
           ).to_have_text("Continuous")
    # commented out because we have an issue #4233
    # expect(page.locator(row_selector).locator(state_col)
    #        ).to_have_text("Pending")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/")
    result = page.get_by_text(market_name)
    result.first.click()

    expect(page.get_by_text(market_name).first).to_be_attached()
    expect(page.get_by_test_id(
        "market-trading-mode").get_by_test_id("item-value")).to_have_text("Continuous")
    expect(page.get_by_test_id(
        "market-state").get_by_test_id("item-value")).to_have_text("Active")
    # commented out because we have an issue #4233
    # expect(page.get_by_text("Opening auction")).to_be_hidden()
