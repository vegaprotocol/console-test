from collections import namedtuple
from playwright.sync_api import Page, expect
from market_fixtures.simple_market.simple_market import setup_simple_market
from vega_sim.service import VegaService


# Wallet Configurations
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]

table_row_selector = '[data-testid="tab-all-markets"] .ag-center-cols-container .ag-row'
trading_mode_col = '[col-id="tradingMode"]'
state_col = '[col-id="state"]'
item_value = "item-value"
price_monitoring_bounds_row = "key-value-table-row"
market_trading_mode = "market-trading-mode"
market_state = "market-state"
liquidity_supplied = "liquidity-supplied"

initial_commitment: float = 100
mint_amount: float = 10000
initial_price: float = 1
initial_volume: float = 1
initial_spread: float = 0.1
market_name = "BTC:DAI_YYYYYYYYY"


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


def test_price_monitoring(setup_simple_market, vega: VegaService, page: Page):

    market_id = vega.all_markets()[0].id
    page.goto(f"http://localhost:{vega.console_port}/#/markets/all")
    page.get_by_text("continue").click()
    expect(page.locator(table_row_selector).locator(trading_mode_col)
           ).to_have_text("Opening auction")
    expect(page.locator(table_row_selector).locator('[col-id="state"]')
           ).to_have_text("Pending")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/")
    result = page.get_by_text(market_name)
    result.first.click()
    page.get_by_test_id(
        market_trading_mode).get_by_text("Opening auction").hover()
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

    expect(page.get_by_test_id(liquidity_supplied
                               ).get_by_test_id(item_value)).to_have_text("0.00 (0.00%)")

    # add orders to provide liquidity
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_BUY",
                 initial_volume, initial_price)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL",
                 initial_volume, initial_price)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_BUY",
                 initial_volume, initial_price + initial_spread / 2)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL",
                 initial_volume, initial_price + initial_spread / 2)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_SELL",
                 initial_volume, initial_price)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    expect(page.get_by_test_id(liquidity_supplied
                               ).get_by_test_id(item_value)).to_have_text("100.00 (>100%)")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/all")
    expect(page.locator(table_row_selector).locator(trading_mode_col)
           ).to_have_text("Continuous")

    # commented out because we have an issue #4233
    # expect(page.locator(row_selector).locator(state_col)
    #        ).to_have_text("Pending")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/")
    result = page.get_by_text(market_name)
    result.first.click()

    page.get_by_test_id("Info").click()
    page.get_by_test_id(
        "accordion-title").get_by_text("Price monitoring bounds 1").click()
    expect(page.get_by_test_id(
        price_monitoring_bounds_row).first.get_by_text("1.32217 BTC")).to_be_visible()
    expect(page.get_by_test_id(
        price_monitoring_bounds_row).last.get_by_text("0.79245 BTC")).to_be_visible()

    # add orders that change the price so that it goes beyond the limits of price monitoring
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 100, 110)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 100, 90)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 100, 105)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 100, 95)

    # add order at the current price so that it is possible to change the status to price monitoring
    to_cancel = submit_order(vega, MM_WALLET2.name,
                             market_id, "SIDE_BUY", 1, 105)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    expect(page.get_by_test_id(
        price_monitoring_bounds_row).first.get_by_text("135.44204 BTC")).to_be_visible()
    expect(page.get_by_test_id(
        price_monitoring_bounds_row).last.get_by_text("81.17758 BTC")).to_be_visible()
    expect(page.get_by_test_id(
        market_trading_mode).get_by_test_id(item_value)).to_have_text("Monitoring auction - price")
    expect(page.get_by_test_id(
        market_state).get_by_test_id(item_value)).to_have_text("Suspended")
    expect(page.get_by_test_id(liquidity_supplied
                               ).get_by_test_id(item_value)).to_have_text("100.00 (17.93%)")

    # cancel order to increase liquidity
    vega.cancel_order(MM_WALLET2.name, market_id, to_cancel)
    vega.wait_for_total_catchup()
    vega.forward("10s")

    expect(page.get_by_text(market_name).first).to_be_attached()
    expect(page.get_by_test_id(
        market_trading_mode).get_by_test_id(item_value)).to_have_text("Continuous")
    expect(page.get_by_test_id(
        market_state).get_by_test_id(item_value)).to_have_text("Active")
    # commented out because we have an issue #4233
    # expect(page.get_by_text("Opening auction")).to_be_hidden()
    expect(page.get_by_test_id(liquidity_supplied
                               ).get_by_test_id(item_value)).to_have_text("100.00 (>100%)")
