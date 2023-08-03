import pytest
import statistics
from collections import namedtuple
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from typing import List
from actions.vega import submit_liquidity, submit_multiple_orders

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")


@pytest.fixture()
@pytest.mark.usefixtures("simple_market")
def setup_market(simple_market, vega: VegaService):
    market_id = simple_market
    submit_liquidity(vega, MM_WALLET.name, market_id)
    submit_multiple_orders(
        vega,
        MM_WALLET.name,
        market_id,
        "SIDE_SELL",
        [[10, 130.005], [3, 130], [7, 120], [5, 110], [2, 105]],
    )
    submit_multiple_orders(
        vega,
        MM_WALLET2.name,
        market_id,
        "SIDE_BUY",
        [[10, 69.995], [5, 70], [5, 85], [3, 90], [3, 95]],
    )
    vega.forward("10s")
    vega.wait_for_total_catchup()
    return market_id


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
def test_orderbook_grid_content(setup_market, page: Page):
    # 6003-ORDB-001
    # 6003-ORDB-002
    # 6003-ORDB-003
    # 6003-ORDB-004
    # 6003-ORDB-005
    # 6003-ORDB-006
    # 6003-ORDB-007
    page.goto(f"/#/markets/{setup_market}")

    page.locator("[data-testid=Orderbook]").click()

    verify_orderbook_grid(page, orderbook_content)
    verify_prices_descending(page)


@pytest.mark.usefixtures("risk_accepted")
def test_orderbook_resolution_change(setup_market, page: Page):
    # 6003-ORDB-008
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

    page.goto(f"/#/markets/{setup_market}")

    for resolution in resolutions:
        page.get_by_test_id("resolution").click()
        page.get_by_role("menu").get_by_text(resolution[0], exact=True).click()
        verify_orderbook_grid(page, resolution[1])


@pytest.mark.usefixtures("risk_accepted")
def test_orderbook_price_size_copy(setup_market, page: Page):
    # 6003-ORDB-009
    prices = page.get_by_test_id("tab-orderbook").locator('[data-testid^="price-"]')
    volumes = page.get_by_test_id("tab-orderbook").locator('[data-testid*="-vol-"]')

    page.goto(f"/#/markets/{setup_market}")
    prices.first.wait_for(state="visible")

    for price in prices.all():
        price.click()
        expect(page.get_by_test_id("order-price")).to_have_value(price.text_content())

    for volume in volumes.all():
        volume.click()
        expect(page.get_by_test_id("order-size")).to_have_value(volume.text_content())
