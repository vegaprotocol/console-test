from numpy import size
import pytest
from collections import namedtuple
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from market_fixtures.continuous_market.continuous_market import setup_continuous_market


# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

stop_order_btn = "order-type-Stop"
stop_limit_order_btn = "order-type-StopLimit"
stop_market_order_btn =  "order-type-StopMarket"
order_side_sell = "order-side-SIDE_SELL"
trigger_above = "triggerDirection-risesAbove"
trigger_below = "triggerDirection-fallsBelow"
trigger_price = "triggerPrice"
trigger_type_price = "triggerType-price"
trigger_type_trailing_percent_offset = "triggerType-trailingPercentOffset"
order_size = "order-size"
order_price = "order-price"
order_tif = "order-tif"
expire = "expire"
expiry_strategy = '[for="expiryStrategy"]'
expiry_strategy_submit = "expiryStrategy-submit"
expiry_strategy_cancel = "expiryStrategy-cancel"
date_picker_field = "date-picker-field"
submit_stop_order = "place-order"

@pytest.mark.usefixtures("auth")
def test_stop_order_form_error_validation(vega: VegaService, setup_continuous_market, page: Page):

    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(submit_stop_order).click()
    expect(page.get_by_test_id("stop-order-error-message-trigger-price")).to_be_visible()
    expect(page.get_by_test_id("stop-order-error-message-size")).to_be_visible()


@pytest.mark.usefixtures("auth")
def test_submit_stop_order(vega: VegaService, setup_continuous_market, page: Page):


    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(trigger_price).type("1")
    page.get_by_test_id(order_size).type("1")
    page.get_by_test_id(submit_stop_order).click()

    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.pause()

@pytest.mark.usefixtures("auth")
def test_stop_order_form_validation(vega: VegaService, setup_continuous_market, page: Page):


    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    expect(page.get_by_test_id("sidebar-content").get_by_text("Trigger")).to_be_visible()
    expect(page.locator('[for="triggerDirection-risesAbove"]')).to_have_text("Rises above")
    expect(page.locator('[for="triggerDirection-fallsBelow"]')).to_have_text("Falls below")
    page.get_by_test_id(trigger_price).click()
    expect(page.get_by_test_id(trigger_price)).to_be_empty
    # expect(page.get_by_test_id('[for="triggerType-price"]')).to_have_text("Price")
    # expect(page.get_by_test_id('[for="triggerType-trailingPercentOffset"]')).to_have_text("Trailing Percent Offset")    
    # expect(page.locator('[for="triggerDirection-fallsBelow"]')).to_have_text("Falls below")


    
 
 
