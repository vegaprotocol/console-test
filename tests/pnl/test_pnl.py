import pytest
import time
import requests
import re
from collections import namedtuple
from playwright.sync_api import expect, Page
from vega_sim.service import VegaService
from actions.vega import submit_order

from playwright.sync_api import expect

WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]

def wait_for_graphql_response(page, query_name, timeout=5000):
    response_data = {}

    def handle_response(route, request):
        if "graphql" in request.url:
            response = request.response()
            if response is not None:
                json_response = response.json()
                if json_response and 'data' in json_response:
                    data = json_response['data']
                    if query_name in data:
                        response_data['data'] = data
                        route.continue_()
                        return
        route.continue_()

    # Register the route handler
    page.route("**", handle_response)

    # Wait for the response data to be populated
    page.wait_for_timeout(timeout)

    # Unregister the route handler
    page.unroute("**", handle_response)

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
    vega.forward("10s")
    vega.wait_for_total_catchup()

def check_pnl_color_value(element, expected_color, expected_value):
    color = element.evaluate('element => getComputedStyle(element).color')
    value = element.inner_text()
    assert color == expected_color, f'Unexpected color: {color}'
    assert value == expected_value, f'Unexpected value: {value}'

def wait_for_service(url, timeout=60):
    start_time = time.time()
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
        except Exception:
            # If the connection attempt fails, wait and try again
            time.sleep(1)
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timed out waiting for service at {url}")


@pytest.mark.usefixtures("continuous_market", "auth")
def test_pnl_loss_portfolio(continuous_market, vega:VegaService, page: Page):    
    page.set_viewport_size({"width":1748, "height":977})
    submit_order(vega, "Key 1", continuous_market, "SIDE_BUY", 1, 104.50000)
    page.goto(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_service(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    page.get_by_role("link", name="Portfolio").click()
    page.get_by_test_id('Positions').click()
    wait_for_graphql_response(page, 'EstimatePosition')
    page.wait_for_selector('[data-testid="tab-positions"] .ag-center-cols-container .ag-row', state='visible')

    row_element = page.query_selector('//div[@role="row" and .//div[@col-id="partyId"]/div/span[text()="Key 1"]]')
    
    unrealised_pnl = row_element.query_selector('xpath=./div[@col-id="unrealisedPNL"]')
    realised_pnl = row_element.query_selector('xpath=./div[@col-id="realisedPNL"]')

    
    check_pnl_color_value(realised_pnl, 'rgb(0, 0, 0)', '0.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(236, 0, 60)', '-4.00')

    submit_order(vega, "Key 1", continuous_market, "SIDE_SELL", 2, 101.50000)
    
    wait_for_graphql_response(page, 'EstimatePosition')
    check_pnl_color_value(realised_pnl, 'rgb(236, 0, 60)', '-8.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(0, 0, 0)', '0.00')


@pytest.mark.usefixtures("continuous_market", "auth")
def test_pnl_profit_portfolio(continuous_market, vega:VegaService, page: Page):
    page.set_viewport_size({"width":1748, "height":977})
    submit_order(vega, "Key 1", continuous_market, "SIDE_BUY", 1, 104.50000)
    page.goto(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_service(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    page.get_by_role("link", name="Portfolio").click()
    page.get_by_test_id('Positions').click()
    wait_for_graphql_response(page, 'EstimatePosition')
    page.wait_for_selector('[data-testid="tab-positions"] .ag-center-cols-container .ag-row', state='visible')

    selector = '//div[@role="row" and .//div[@col-id="partyId"]/div/span[text()="mm"]]'
 
    row_element = page.query_selector(selector)
    unrealised_pnl = row_element.query_selector('xpath=./div[@col-id="unrealisedPNL"]')
    realised_pnl = row_element.query_selector('xpath=./div[@col-id="realisedPNL"]')

    
    check_pnl_color_value(realised_pnl, 'rgb(0, 0, 0)', '0.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(1, 145, 75)', '4.00')
    
    submit_order(vega, "Key 1", continuous_market, "SIDE_SELL", 2, 101.50000)
    wait_for_graphql_response(page, 'EstimatePosition')
    check_pnl_color_value(realised_pnl, 'rgb(1, 145, 75)', '8.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(0, 0, 0)', '0.00')
 
@pytest.mark.usefixtures("continuous_market", "auth")
def test_pnl_neutral_portfolio(continuous_market, vega:VegaService, page: Page):
    page.set_viewport_size({"width":1748, "height":977})
    page.goto(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_service(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    page.get_by_role("link", name="Portfolio").click()
    page.get_by_test_id('Positions').click()
    wait_for_graphql_response(page, 'EstimatePosition')
    page.wait_for_selector('[data-testid="tab-positions"] .ag-center-cols-container .ag-row', state='visible')
    realised_pnl = page.locator(".ag-row-even > div:nth-child(9)").first
    unrealised_pnl = page.locator(".ag-row-even > div:nth-child(9)").first

    check_pnl_color_value(realised_pnl, 'rgb(0, 0, 0)', '0.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(0, 0, 0)', '0.00')
    

@pytest.mark.usefixtures("continuous_market", "auth")
def test_pnl_loss_trading(continuous_market, vega:VegaService, page: Page):
    submit_order(vega, "Key 1", continuous_market, "SIDE_BUY", 1, 104.50000)
    page.set_viewport_size({"width":1748, "height":977})
    page.goto(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_service(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_graphql_response(page, 'EstimatePosition')

    realised_pnl = page.locator('[col-id="realisedPNL"]').last
    unrealised_pnl = page.locator('[col-id="unrealisedPNL"]').last
    page.wait_for_selector('[id^="cell-marketName-"]', state='visible')

    check_pnl_color_value(realised_pnl, 'rgb(0, 0, 0)', '0.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(236, 0, 60)', '-4.00')

    submit_order(vega, "Key 1", continuous_market, "SIDE_SELL", 2, 101.50000)
    
    wait_for_graphql_response(page, 'EstimatePosition')
    check_pnl_color_value(realised_pnl, 'rgb(236, 0, 60)', '-8.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(0, 0, 0)', '0.00')

    

@pytest.mark.usefixtures("continuous_market", "auth")
def test_pnl_profit_trading(continuous_market, vega:VegaService, page: Page):
    submit_order(vega, "Key 1", continuous_market, "SIDE_BUY", 1, 104.50000)
    page.set_viewport_size({"width":1748, "height":977})

    page.goto(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_service(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    page.get_by_test_id('manage-vega-wallet').click()
    page.get_by_role('menuitemradio').nth(1).click(position={ "x": 10, "y": 10})
    element_locator = page.get_by_test_id("manage-vega-wallet")
    element_locator.click(force=True)
    wait_for_graphql_response(page, 'EstimatePosition')
    page.wait_for_selector('[id^="cell-marketName-"]', state='visible')

    realised_pnl = page.locator('.ag-center-cols-container .ag-row >> css=[col-id="realisedPNL"]')
    unrealised_pnl = page.locator('.ag-center-cols-container .ag-row >> css=[col-id="unrealisedPNL"]')

    check_pnl_color_value(realised_pnl, 'rgb(0, 0, 0)', '0.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(1, 145, 75)', '4.00')

    submit_order(vega, "Key 1", continuous_market, "SIDE_SELL", 2, 101.50000)
    wait_for_graphql_response(page, 'EstimatePosition')
    check_pnl_color_value(realised_pnl, 'rgb(1, 145, 75)', '8.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(0, 0, 0)', '0.00')

@pytest.mark.usefixtures("continuous_market", "auth")
def test_pnl_neutral_trading(continuous_market, vega:VegaService, page: Page):
    page.set_viewport_size({"width":1748, "height":977})
    page.goto(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_service(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
    wait_for_graphql_response(page, 'EstimatePosition')
    page.wait_for_selector('[id^="cell-marketName-"]', state='visible')
    
    realised_pnl = page.locator('.ag-center-cols-container .ag-row >> css=[col-id="realisedPNL"]')
    unrealised_pnl = page.locator('.ag-center-cols-container .ag-row >> css=[col-id="unrealisedPNL"]')

    check_pnl_color_value(realised_pnl, 'rgb(0, 0, 0)', '0.00')
    check_pnl_color_value(unrealised_pnl, 'rgb(0, 0, 0)', '0.00')
        