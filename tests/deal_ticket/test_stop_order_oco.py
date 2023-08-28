import pytest
from collections import namedtuple
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from actions.vega import submit_order
from datetime import datetime, timedelta

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

stop_order_btn = "order-type-Stop"
stop_limit_order_btn = "order-type-StopLimit"
stop_market_order_btn = "order-type-StopMarket"
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
market_name_col = '[col-id="market.tradableInstrument.instrument.code"]'
trigger_col = '[col-id="trigger"]'
expiresAt_col = '[col-id="expiresAt"]'
size_col = '[col-id="submission.size"]'
submission_type = '[col-id="submission.type"]'
status_col = '[col-id="status"]'
price_col = '[col-id="submission.price"]'
timeInForce_col = '[col-id="submission.timeInForce"]'
updatedAt_col = '[col-id="updatedAt"]'
close_toast = "toast-close"
trigger_direction_fallsBelow_oco = "triggerDirection-fallsBelow-oco"
oco = "oco"
trigger_price_oco = "triggerPrice-oco"
order_size_oco = "order-size-oco"
order_limit_price_oco = "order-price-oco"

def wait_for_graphql_response(page, query_name, timeout=5000):
    response_data = {}

    def handle_response(route, request):
        if "graphql" in request.url:
            response = request.response()
            if response is not None:
                json_response = response.json()
                if json_response and "data" in json_response:
                    data = json_response["data"]
                    if query_name in data:
                        response_data["data"] = data
                        route.continue_()
                        return
        route.continue_()

    # Register the route handler
    page.route("**", handle_response)

    # Wait for the response data to be populated
    page.wait_for_timeout(timeout)

    # Unregister the route handler
    page.unroute("**", handle_response)

def create_position(vega: VegaService, market_id):
    submit_order(vega, "Key 1", market_id, "SIDE_SELL", 100, 110)
    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 100, 110)
    vega.forward("10s")
    vega.wait_for_total_catchup

@pytest.mark.usefixtures("page", "vega", "continuous_market", "auth", "risk_accepted")
def test_submit_stop_order_oco_rejected(continuous_market, vega: VegaService, page: Page):
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(stop_orders_tab).click() 
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(trigger_price).fill("103")
    page.get_by_test_id(order_size).fill("3")
    
    expect(page.get_by_test_id("stop-order-warning-message-trigger-price")).to_have_text("Stop order will be triggered immediately")
    
    page.get_by_test_id(oco).click()
    expect(page.get_by_test_id(trigger_direction_fallsBelow_oco)).to_be_checked
    
    page.get_by_test_id(trigger_price_oco).fill("102")
    page.get_by_test_id(order_size_oco).fill("2")
    page.get_by_test_id(submit_stop_order).click()
    vega.wait_fn(1)
    vega.forward("10s")
    vega.wait_for_total_catchup()
    
    page.get_by_test_id(close_toast).click()
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_role(row_table).locator(market_name_col).nth(1).is_visible()

    expect((page.get_by_role(row_table).locator(market_name_col)).nth(1)).to_have_text(
        "BTC:DAI_2023Futr"
    )
    expect((page.get_by_role(row_table).locator(trigger_col)).nth(1)).to_have_text(
        "Mark < 102.00"
    )
    expect((page.get_by_role(row_table).locator(expiresAt_col)).nth(1)).to_have_text("")
    expect((page.get_by_role(row_table).locator(size_col)).nth(1)).to_have_text("+2")
    expect((page.get_by_role(row_table).locator(submission_type)).nth(1)).to_have_text(
        "Market"
    )
    expect((page.get_by_role(row_table).locator(status_col)).nth(1)).to_have_text(
        "RejectedOCO"
    )
    expect((page.get_by_role(row_table).locator(price_col)).nth(1)).to_have_text("-")
    expect((page.get_by_role(row_table).locator(timeInForce_col)).nth(1)).to_have_text(
        "FOK"
    )
    expect(
        (page.get_by_role(row_table).locator(updatedAt_col)).nth(1)
    ).not_to_be_empty()

    expect((page.get_by_role(row_table).locator(market_name_col)).nth(2)).to_have_text(
        "BTC:DAI_2023Futr"
    )
    expect((page.get_by_role(row_table).locator(trigger_col)).nth(2)).to_have_text(
        "Mark > 103.00"
    )
    expect((page.get_by_role(row_table).locator(expiresAt_col)).nth(2)).to_have_text("")
    expect((page.get_by_role(row_table).locator(size_col)).nth(2)).to_have_text("+3")
    expect((page.get_by_role(row_table).locator(submission_type)).nth(2)).to_have_text(
        "Market"
    )
    expect((page.get_by_role(row_table).locator(status_col)).nth(2)).to_have_text(
        "RejectedOCO"
    )
    expect((page.get_by_role(row_table).locator(price_col)).nth(2)).to_have_text("-")
    expect((page.get_by_role(row_table).locator(timeInForce_col)).nth(2)).to_have_text(
        "FOK"
    )
    expect(
        (page.get_by_role(row_table).locator(updatedAt_col)).nth(2)
    ).not_to_be_empty()

@pytest.mark.usefixtures("page", "vega", "continuous_market", "auth", "risk_accepted")
def test_submit_stop_oco_market_order_triggered(continuous_market, vega: VegaService, page: Page):
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(stop_orders_tab).click()
    create_position(vega, market_id)
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(trigger_price).fill("103")
    page.get_by_test_id(order_size).fill("3")
    
    expect(page.get_by_test_id("stop-order-warning-message-trigger-price")).to_have_text("Stop order will be triggered immediately")
    
    page.get_by_test_id(oco).click()
    expect(page.get_by_test_id(trigger_direction_fallsBelow_oco)).to_be_checked
    
    page.get_by_test_id(trigger_price_oco).fill("102")
    page.get_by_test_id(order_size_oco).fill("2")
    page.get_by_test_id(submit_stop_order).click()
    vega.wait_fn(1)
    vega.forward("10s")
    vega.wait_for_total_catchup()
    
    page.get_by_test_id(close_toast).click()
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_role(row_table).locator(market_name_col).nth(1).is_visible()

    expect((page.get_by_role(row_table).locator(market_name_col)).nth(1)).to_have_text(
        "BTC:DAI_2023Futr"
    )
    expect((page.get_by_role(row_table).locator(trigger_col)).nth(1)).to_have_text(
        "Mark < 102.00"
    )
    expect((page.get_by_role(row_table).locator(expiresAt_col)).nth(1)).to_have_text("")
    expect((page.get_by_role(row_table).locator(size_col)).nth(1)).to_have_text("+2")
    expect((page.get_by_role(row_table).locator(submission_type)).nth(1)).to_have_text(
        "Market"
    )
    expect((page.get_by_role(row_table).locator(status_col)).nth(1)).to_have_text(
        "StoppedOCO"
    )
    expect((page.get_by_role(row_table).locator(price_col)).nth(1)).to_have_text("-")
    expect((page.get_by_role(row_table).locator(timeInForce_col)).nth(1)).to_have_text(
        "FOK"
    )
    expect(
        (page.get_by_role(row_table).locator(updatedAt_col)).nth(1)
    ).not_to_be_empty()

    expect((page.get_by_role(row_table).locator(market_name_col)).nth(2)).to_have_text(
        "BTC:DAI_2023Futr"
    )
    expect((page.get_by_role(row_table).locator(trigger_col)).nth(2)).to_have_text(
        "Mark > 103.00"
    )
    expect((page.get_by_role(row_table).locator(expiresAt_col)).nth(2)).to_have_text("")
    expect((page.get_by_role(row_table).locator(size_col)).nth(2)).to_have_text("+3")
    expect((page.get_by_role(row_table).locator(submission_type)).nth(2)).to_have_text(
        "Market"
    )
    expect((page.get_by_role(row_table).locator(status_col)).nth(2)).to_have_text(
        "TriggeredOCO"
    )
    expect((page.get_by_role(row_table).locator(price_col)).nth(2)).to_have_text("-")
    expect((page.get_by_role(row_table).locator(timeInForce_col)).nth(2)).to_have_text(
        "FOK"
    )
    expect(
        (page.get_by_role(row_table).locator(updatedAt_col)).nth(2)
    ).not_to_be_empty()


@pytest.mark.usefixtures("page", "vega", "continuous_market", "auth", "risk_accepted")
def test_submit_stop_oco_market_order_pending(continuous_market, vega: VegaService, page: Page):
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(stop_orders_tab).click()
    create_position(vega, market_id)
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_market_order_btn).is_visible()
    page.get_by_test_id(stop_market_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(trigger_below).click()
    page.get_by_test_id(trigger_price).fill("102")
    page.get_by_test_id(order_size).fill("3")
    page.get_by_test_id(oco).click()
    expect(page.get_by_test_id(trigger_direction_fallsBelow_oco)).to_be_checked
    page.get_by_test_id(trigger_price_oco).fill("104")
    page.get_by_test_id(order_size_oco).fill("2")
    page.get_by_test_id(submit_stop_order).click()
    vega.wait_fn(1)
    vega.forward("10s")
    vega.wait_for_total_catchup()
    
    page.get_by_test_id(close_toast).click()
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_role(row_table).locator(market_name_col).nth(1).is_visible()

    expect((page.get_by_role(row_table).locator(status_col)).nth(1)).to_have_text(
        "PendingOCO"
    )

    expect((page.get_by_role(row_table).locator(status_col)).nth(2)).to_have_text(
        "PendingOCO"
    )

@pytest.mark.usefixtures("page", "vega", "continuous_market", "auth", "risk_accepted")
def test_submit_stop_oco_limit_order_pending(continuous_market, vega: VegaService, page: Page):
    market_id = continuous_market
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id(stop_orders_tab).click()
    create_position(vega, market_id)
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_test_id(stop_order_btn).click()
    page.get_by_test_id(stop_limit_order_btn).is_visible()
    page.get_by_test_id(stop_limit_order_btn).click()
    page.get_by_test_id(order_side_sell).click()
    page.get_by_test_id(trigger_below).click()
    page.get_by_test_id(trigger_price).fill("102")
    page.get_by_test_id(order_size).fill("3")
    page.get_by_test_id(order_price).fill("103")
    page.get_by_test_id(oco).click()
    expect(page.get_by_test_id(trigger_direction_fallsBelow_oco)).to_be_checked
    page.get_by_test_id(trigger_price_oco).fill("104")
    page.get_by_test_id(order_size_oco).fill("2")
    page.get_by_test_id(order_limit_price_oco).fill("99")
    page.get_by_test_id(submit_stop_order).click()
    vega.wait_fn(1)
    vega.forward("10s")
    vega.wait_for_total_catchup()
    
    page.get_by_test_id(close_toast).click()
    wait_for_graphql_response(page, "stopOrders")
    page.get_by_role(row_table).locator(market_name_col).nth(1).is_visible()

    expect((page.get_by_role(row_table).locator(submission_type)).nth(1)).to_have_text(
        "Limit"
    )
    expect((page.get_by_role(row_table).locator(submission_type)).nth(2)).to_have_text(
        "Limit"
    )
    expect((page.get_by_role(row_table).locator(price_col)).nth(1)).to_have_text(
        "103.00"
    )
    expect((page.get_by_role(row_table).locator(price_col)).nth(2)).to_have_text(
        "99.00"
    )