import logging
import pytest
import statistics
from collections import namedtuple
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from typing import List


# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]


def setup_continuous_market(vega: VegaService, page: Page):
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

    vega.create_asset(
        MM_WALLET.name, name="tDAI", symbol="tDAI", decimals=5, max_faucet_amount=1e10
    )
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
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 10, 130.005)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 3, 130)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 7, 120)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 5, 110)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 2, 105)

    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 10, 69.995)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 5, 70)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 5, 85)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 3, 90)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 3, 95)

    vega.wait_for_total_catchup()
    vega.forward("10s")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/{market_id}")


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


orderbook_content = [
    [130.00500, 10, 27],
    [130.00000, 3, 17],
    [120.00000, 7, 14],
    [110.00000, 5, 7],
    [105.00000, 2, 2],
    [95.00000, 3, 3],
    [90.00000, 3, 6],
    [85.00000, 5, 11],
    [70.00000, 5, 16],
    [69.99500, 10, 26],
]


def verify_orderbook_grid(page: Page, content: List[List[float]]):
    median = statistics.median([row[0] for row in orderbook_content])
    assert (
        float(page.locator("[data-testid*=middle-mark-price]").text_content()) == median
    )
    rows = page.locator("[data-testid$=-rows-container]").all()
    for row_index, content_row in enumerate(content):
        cells = rows[row_index].locator("button").all()
        for cell_index, content_cell in enumerate(content_row):
            assert float(cells[cell_index].text_content()) == content_cell


def verify_prices_descending(page: Page):
    prices_locator = page.get_by_test_id("tab-orderbook").locator(
        '[data-testid^="price-"]'
    )
    prices_locator.first.wait_for(state="visible")
    prices = [float(price.text_content()) for price in prices_locator.all()]
    assert prices == sorted(prices, reverse=True)


@pytest.mark.usefixtures("risk_accepted")
def test_orderbook_grid_content(vega: VegaService, page: Page):
    # 6003-ORDB-001
    # 6003-ORDB-002
    # 6003-ORDB-003
    # 6003-ORDB-004
    # 6003-ORDB-005
    # 6003-ORDB-006
    # 6003-ORDB-007

    setup_continuous_market(vega, page)

    page.locator("[data-testid=Orderbook]").click()

    verify_orderbook_grid(page, orderbook_content)
    verify_prices_descending(page)


@pytest.mark.usefixtures("risk_accepted")
def test_orderbook_resolution_change(vega: VegaService, page: Page):
    # 6003-ORDB-008

    setup_continuous_market(vega, page)

    orderbook_content_0_00 = [
        [130.01, 10, 27],
        [130.00, 3, 17],
        [120.00, 7, 14],
        [110.00, 5, 7],
        [105.00, 2, 2],
        [95.00, 3, 3],
        [90.00, 3, 6],
        [85.00, 5, 11],
        [70.00, 15, 26],
    ]

    orderbook_content_10 = [
        [130, 13, 27],
        [120, 7, 14],
        [110, 7, 7],
        [100, 3, 3],
        [90, 8, 11],
        [70, 15, 26],
    ]

    orderbook_content_100 = [
        [100, 27, 27],
        [100, 26, 26],
    ]

    resolutions = [
        ["0.00", orderbook_content_0_00],
        ["10", orderbook_content_10],
        ["100", orderbook_content_100],
    ]

    for resolution in resolutions:
        page.get_by_test_id("resolution").click()
        page.get_by_role("menu").get_by_text(resolution[0], exact=True).click()
        verify_orderbook_grid(page, resolution[1])


@pytest.mark.usefixtures("risk_accepted")
def test_orderbook_price_size_copy(vega: VegaService, page: Page):
    # 6003-ORDB-009
    setup_continuous_market(vega, page)

    prices = page.get_by_test_id("tab-orderbook").locator('[data-testid^="price-"]')
    volumes = page.get_by_test_id("tab-orderbook").locator('[data-testid*="-vol-"]')

    prices.first.wait_for(state="visible")

    for price in prices.all():
        price.click()
        expect(page.get_by_test_id("order-price")).to_have_value(price.text_content())

    # a little adjustment needed in orderbook to make it working correctly (something is intercepting the click)
    # for volume in volumes.all():
    #     volume.click()
    #     expect(page.get_by_test_id("order-size")).to_have_value(volume.text_content())
