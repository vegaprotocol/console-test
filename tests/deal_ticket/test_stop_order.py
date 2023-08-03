import pytest
from collections import namedtuple
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from actions.vega import submit_order


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
stop_orders_tab = "Stop orders"
row_table = "row"
cancel = "cancel"

@pytest.mark.usefixtures("continuous_market", "auth")
def test_stop_order_form_error_validation(continuous_market, vega: VegaService, page: Page):

    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")

    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(submit_stop_order).click()
    expect(page.get_by_test_id("stop-order-error-message-trigger-price")).to_be_visible()
    expect(page.get_by_test_id("stop-order-error-message-size")).to_be_visible()


@pytest.mark.usefixtures("continuous_market", "auth")
def test_submit_stop_order_rejected(continuous_market, vega: VegaService, page: Page):

    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")

    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(trigger_price).type("103")
    page.get_by_test_id(order_size).type("3")
    page.get_by_test_id(submit_stop_order).click()
    page.get_by_test_id(stop_orders_tab).click()

    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.get_by_test_id("toast-close").click()

    expect((page.get_by_role(row_table).locator('[col-id="market.tradableInstrument.instrument.code"]')).nth(1)).to_have_text("BTC:DAI_2023")
    expect((page.get_by_role(row_table).locator('[col-id="trigger"]')).nth(1)).to_have_text("Mark > 103.00")
    expect((page.get_by_role(row_table).locator('[col-id="expiresAt"]')).nth(1)).to_have_text("")
    expect((page.get_by_role(row_table).locator('[col-id="submission.size"]')).nth(1)).to_have_text("+3")
    expect((page.get_by_role(row_table).locator('[col-id="submission.type"]')).nth(1)).to_have_text("Market")
    expect((page.get_by_role(row_table).locator('[col-id="status"]')).nth(1)).to_have_text("Rejected")
    expect((page.get_by_role(row_table).locator('[col-id="submission.price"]')).nth(1)).to_have_text("-")
    expect((page.get_by_role(row_table).locator('[col-id="submission.timeInForce"]')).nth(1)).to_have_text("FOK")
    expect((page.get_by_role(row_table).locator('[col-id="updatedAt"]')).nth(1)).not_to_be_empty()


@pytest.mark.usefixtures("continuous_market", "auth")
def test_submit_stop_market_order_triggered(continuous_market, vega: VegaService, page: Page):

    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")

    
    submit_order(vega, "Key 1", market_id, "SIDE_SELL", 100, 110)
    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 100, 110)
    vega.wait_for_total_catchup
    vega.forward("10s")

    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(trigger_price).type("103")
    page.get_by_test_id(order_size).type("1")
    page.get_by_test_id(expire).click()
    page.get_by_test_id(submit_stop_order).click()
    page.get_by_test_id(stop_orders_tab).click()

    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.get_by_test_id("toast-close").click()

    expect((page.get_by_role(row_table).locator('[col-id="market.tradableInstrument.instrument.code"]')).nth(1)).to_have_text("BTC:DAI_2023")
    expect((page.get_by_role(row_table).locator('[col-id="trigger"]')).nth(1)).to_have_text("Mark > 103.00")
    expect((page.get_by_role(row_table).locator('[col-id="expiresAt"]')).nth(1)).to_have_text("")
    expect((page.get_by_role(row_table).locator('[col-id="submission.size"]')).nth(1)).to_have_text("-1")
    expect((page.get_by_role(row_table).locator('[col-id="submission.type"]')).nth(1)).to_have_text("Market")
    expect((page.get_by_role(row_table).locator('[col-id="status"]')).nth(1)).to_have_text("Triggered")
    expect((page.get_by_role(row_table).locator('[col-id="submission.price"]')).nth(1)).to_have_text("-")
    expect((page.get_by_role(row_table).locator('[col-id="submission.timeInForce"]')).nth(1)).to_have_text("FOK")
    expect((page.get_by_role(row_table).locator('[col-id="updatedAt"]')).nth(1)).not_to_be_empty()

@pytest.mark.usefixtures("continuous_market", "auth")
def test_submit_stop_limit_order_pending(continuous_market, vega: VegaService, page: Page):
   
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")

    
    submit_order(vega, "Key 1", market_id, "SIDE_SELL", 100, 110)
    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 100, 110)
    vega.wait_for_total_catchup
    vega.forward("10s")

    page.get_by_test_id("deal-ticket-warning-margin").is_visible()

    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_limit_order_btn).is_visible()
    page.get_by_test_id(stop_limit_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(trigger_below).click()
    page.get_by_test_id(trigger_price).type("102")
    page.get_by_test_id(order_price).type("99")
    page.get_by_test_id(order_size).type("1")
    
    page.get_by_test_id(expire).click()
    page.get_by_test_id(submit_stop_order).click()
    page.get_by_test_id(stop_orders_tab).click()

    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.get_by_test_id("toast-close").click()

    expect((page.get_by_role(row_table).locator('[col-id="market.tradableInstrument.instrument.code"]')).nth(1)).to_have_text("BTC:DAI_2023")
    expect((page.get_by_role(row_table).locator('[col-id="trigger"]')).nth(1)).to_have_text("Mark < 102.00")
    expect((page.get_by_role(row_table).locator('[col-id="expiresAt"]')).nth(1)).to_have_text("")
    expect((page.get_by_role(row_table).locator('[col-id="submission.size"]')).nth(1)).to_have_text("-1")
    expect((page.get_by_role(row_table).locator('[col-id="submission.type"]')).nth(1)).to_have_text("Limit")
    expect((page.get_by_role(row_table).locator('[col-id="status"]')).nth(1)).to_have_text("Pending")
    expect((page.get_by_role(row_table).locator('[col-id="submission.price"]')).nth(1)).to_have_text("99.00")
    expect((page.get_by_role(row_table).locator('[col-id="submission.timeInForce"]')).nth(1)).to_have_text("FOK")
    expect((page.get_by_role(row_table).locator('[col-id="updatedAt"]')).nth(1)).not_to_be_empty()

@pytest.mark.usefixtures("continuous_market", "auth")
def test_submit_stop_limit_order_cancel(continuous_market, vega: VegaService, page: Page):

    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")

    
    submit_order(vega, "Key 1", market_id, "SIDE_SELL", 100, 110)
    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 100, 110)
    vega.wait_for_total_catchup
    vega.forward("10s")

    page.get_by_test_id("deal-ticket-warning-margin").is_visible()

    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_limit_order_btn).is_visible()
    page.get_by_test_id(stop_limit_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(trigger_below).click()
    page.get_by_test_id(trigger_price).type("102")
    page.get_by_test_id(order_price).type("99")
    page.get_by_test_id(order_size).type("1")
    
    page.get_by_test_id(expire).click()
    page.get_by_test_id(submit_stop_order).click()
    page.get_by_test_id(stop_orders_tab).click()

    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.get_by_test_id("toast-close").click()

    page.get_by_test_id(cancel).click()
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.get_by_test_id("toast-close").click()

    expect((page.get_by_role(row_table).locator('[col-id="market.tradableInstrument.instrument.code"]')).nth(1)).to_have_text("")
    
@pytest.mark.usefixtures("continuous_market", "auth")
def test_stop_order_form_validation(continuous_market, vega: VegaService, page: Page):

    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")


    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    expect(page.get_by_test_id("sidebar-content").get_by_text("Trigger")).to_be_visible()
    expect(page.locator('[for="triggerDirection-risesAbove"]')).to_have_text("Rises above")
    expect(page.locator('[for="triggerDirection-fallsBelow"]')).to_have_text("Falls below")
    page.get_by_test_id(trigger_price).click()
    expect(page.get_by_test_id(trigger_price)).to_be_empty
    expect(page.locator('[for="triggerType-price"]')).to_have_text("Price")
    expect(page.locator('[for="triggerType-trailingPercentOffset"]')).to_have_text("Trailing Percent Offset")    
    expect(page.locator('[for="input-price-quote"]')).to_have_text("Size")
    page.get_by_test_id(order_size).click()
    expect(page.get_by_test_id(order_size)).to_be_empty
  



    
 
 
