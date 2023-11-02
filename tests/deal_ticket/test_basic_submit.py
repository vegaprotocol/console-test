import pytest
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from datetime import datetime, timedelta
from conftest import init_vega
from fixtures.market import setup_continuous_market
from actions.utils import wait_for_toast_confirmation, verify_row

order_size = "order-size"
order_price = "order-price"
place_order = "place-order"
order_side_sell = "order-side-SIDE_SELL"
market_order = "order-type-Market"
tif = "order-tif"
expire = "expire"

@pytest.fixture(scope="module")
def vega(request):
    with init_vega(request) as vega:
        yield vega

@pytest.fixture(scope="module")
def continuous_market(vega):
    return setup_continuous_market(vega)

@pytest.mark.usefixtures("page", "auth", "risk_accepted")
def test_limit_buy_order_GTT(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    page.get_by_test_id(order_size).fill("10")
    page.get_by_test_id(order_price).fill("120")
    page.get_by_test_id(tif).select_option("Good 'til Time (GTT)")
    expires_at = datetime.now() + timedelta(days=1)
    expires_at_input_value = expires_at.strftime("%Y-%m-%dT%H:%M:%S")
    page.get_by_test_id("date-picker-field").fill(expires_at_input_value)
    # 7002-SORD-011
    expect(page.get_by_test_id("place-order").locator("span").first).to_have_text(
        "Place limit order"
    )
    expect(page.get_by_test_id("place-order").locator("span").last).to_have_text(
        "10 BTC @ 120.00 BTC"
    )
    page.get_by_test_id(place_order).click()
    wait_for_toast_confirmation(page)
    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    # 7002-SORD-017
    expected_values = {
        "instrument-code": "BTC:DAI_2023Futr",
        "remaining": "10",
        "size": "+10",
        "type": "Limit",
        "status": "Filled",
        "price": "120.00",
        "timeInForce": "GTT",
        "updatedAt": ""
    }
    verify_row(page, expected_values, grid_id="All")


@pytest.mark.usefixtures("page", "auth", "risk_accepted")
def test_limit_buy_order(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    
    page.get_by_test_id(order_size).fill("10")
    page.get_by_test_id(order_price).fill("120")
    page.get_by_test_id(place_order).click()
    wait_for_toast_confirmation(page)
    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.get_by_test_id("All").click()
    # 7002-SORD-017
    expected_values = {
        "instrument-code": "BTC:DAI_2023Futr",
        "remaining": "10",
        "size": "+10",
        "type": "Limit",
        "status": "Filled",
        "price": "120.00",
        "timeInForce": "GTC",
        "updatedAt": ""
    }
    verify_row(page, expected_values, grid_id="All")


@pytest.mark.usefixtures("page", "auth", "risk_accepted")
def test_limit_sell_order(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    page.get_by_test_id(order_size).fill("10")
    page.get_by_test_id(order_price).fill("100")
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(tif).select_option("Good for Normal (GFN)")
    # 7002-SORD-011
    expect(page.get_by_test_id("place-order").locator("span").first).to_have_text(
        "Place limit order"
    )
    expect(page.get_by_test_id("place-order").locator("span").last).to_have_text(
        "10 BTC @ 100.00 BTC"
    )
    page.get_by_test_id(place_order).click()
    wait_for_toast_confirmation(page)
    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    expected_values = {
        "instrument-code": "BTC:DAI_2023Futr",
        "remaining": "10",
        "size": "-10",
        "type": "Limit",
        "status": "Filled",
        "price": "100.00",
        "timeInForce": "GFN",
        "updatedAt": ""
    }
    verify_row(page, expected_values, grid_id="All")


@pytest.mark.usefixtures("page", "auth", "risk_accepted")
def test_market_sell_order(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    page.get_by_test_id(market_order).click()
    page.get_by_test_id(order_size).fill("10")
    page.get_by_test_id(order_side_sell).click()
    # 7002-SORD-011
    expect(page.get_by_test_id("place-order").locator("span").first).to_have_text(
        "Place market order"
    )
    expect(page.get_by_test_id("place-order").locator("span").last).to_have_text(
        "10 BTC @ market"
    )
    page.get_by_test_id(place_order).click()
    wait_for_toast_confirmation(page)
    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    expected_values = {
        "instrument-code": "BTC:DAI_2023Futr",
        "remaining": "10",
        "size": "-10",
        "type": "Market",
        "status": "Filled",
        "price": "-",
        "timeInForce": "IOC",
        "updatedAt": ""
    }
    verify_row(page, expected_values, grid_id="All")


@pytest.mark.usefixtures("page", "auth", "risk_accepted")
def test_market_buy_order(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    page.get_by_test_id(market_order).click()
    page.get_by_test_id(order_size).fill("10")
    page.get_by_test_id(tif).select_option("Fill or Kill (FOK)")
    page.get_by_test_id(place_order).click()
    wait_for_toast_confirmation(page)
    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    # 7002-SORD-010
    # 0003-WTXN-012
    # 0003-WTXN-003
    expected_values = {
        "instrument-code": "BTC:DAI_2023Futr",
        "remaining": "10",
        "size": "+10",
        "type": "Market",
        "status": "Filled",
        "price": "-",
        "timeInForce": "FOK",
        "updatedAt": ""
    }
    verify_row(page, expected_values, grid_id="All")
