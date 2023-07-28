import pytest
from collections import namedtuple
from playwright.sync_api import expect, Page
from vega_sim.service import VegaService
from market_fixtures.continuous_market.continuous_market import setup_continuous_market


# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")


wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]

def submit_order(vega, wallet_name, market_id, side, volume, price, peak_size=None, minimum_visible_size=None):
    vega.submit_order(
        trading_key=wallet_name,
        market_id=market_id,
        time_in_force="TIME_IN_FORCE_GTC",
        order_type="TYPE_LIMIT",
        side=side,
        volume=volume,
        price=price,
        peak_size=peak_size,
        minimum_visible_size = minimum_visible_size,
    )

def hover_and_assert_tooltip(page, element_text):
    element = page.get_by_text(element_text)
    element.hover()
    expect(page.get_by_role("tooltip")).to_be_visible()

@pytest.mark.usefixtures("auth")
def test_iceberg_submit(setup_continuous_market,vega: VegaService,   page: Page):
    page.get_by_test_id('iceberg').click()
    page.get_by_test_id('order-peak-size').fill("2")
    page.get_by_test_id('order-minimum-size').fill("1")
    page.get_by_test_id('order-size').fill("3")
    page.get_by_test_id('order-price').fill("107")
    page.get_by_test_id('place-order').click()
    expect(page.get_by_test_id('toast-content')).to_have_text('Awaiting confirmationPlease wait for your transaction to be confirmedView in block explorer')
   
    vega.wait_fn(10)
    vega.wait_for_total_catchup()
    expect(page.get_by_test_id('toast-content')).to_have_text ('Order filledYour transaction has been confirmed View in block explorerSubmit order - filledBTC:DAI_Mar22+3 @ 107.00 tDAI')
    
    
    
@pytest.mark.usefixtures("auth")
def test_iceberg_tooltips(setup_continuous_market, page: Page):
    hover_and_assert_tooltip(page, "Iceberg")
    page.get_by_test_id('iceberg').click()
    hover_and_assert_tooltip(page, 'Peak size')
    hover_and_assert_tooltip(page, 'Minimum size')

@pytest.mark.usefixtures("auth")
def test_iceberg_validations(setup_continuous_market,  page: Page):

    page.get_by_test_id('iceberg').click()
    page.get_by_test_id('place-order').click()
    expect(page.get_by_test_id('deal-ticket-peak-error-message-size-limit')).to_be_visible()
    expect(page.get_by_test_id('deal-ticket-peak-error-message-size-limit')).to_have_text('You need to provide a peak size')
    expect(page.get_by_test_id('deal-ticket-minimum-error-message-size-limit')).to_be_visible()
    expect(page.get_by_test_id('deal-ticket-minimum-error-message-size-limit')).to_have_text('You need to provide a minimum visible size')
    page.get_by_test_id('order-peak-size').fill('1')
    page.get_by_test_id('order-minimum-size').fill('2')
    expect(page.get_by_test_id('deal-ticket-peak-error-message-size-limit')).to_be_visible()
    expect(page.get_by_test_id('deal-ticket-peak-error-message-size-limit')).to_have_text('Peak size cannot be greater than the size (0)')
    expect(page.get_by_test_id('deal-ticket-minimum-error-message-size-limit')).to_be_visible()
    expect(page.get_by_test_id('deal-ticket-minimum-error-message-size-limit')).to_have_text('Minimum visible size cannot be greater than the peak size (1)')
    page.get_by_test_id('order-minimum-size').fill('0.1')
    expect(page.get_by_test_id('deal-ticket-minimum-error-message-size-limit')).to_be_visible()
    expect(page.get_by_test_id('deal-ticket-minimum-error-message-size-limit')).to_have_text('Minimum visible size cannot be lower than 1')


@pytest.mark.usefixtures("auth")
def test_iceberg_open_order(vega: VegaService, page: Page):
     setup_continuous_market(vega, page)
     page.pause()
     submit_order(vega, "Key 1", vega.all_markets()[0].id, "SIDE_SELL", 15, 120,2, 1)
     # Assert open order

     page.pause()
     vega.forward("10s")
     vega.wait_for_total_catchup()
     page.pause()
    
     submit_order(vega, MM_WALLET2.name, vega.all_markets()[0].id, "SIDE_BUY", 5, 120)
    
     vega.forward("10s")
     vega.wait_for_total_catchup()
     page.pause()
     submit_order(vega, MM_WALLET2.name, vega.all_markets()[0].id, "SIDE_BUY", 15, 120)
    
     vega.forward("10s")
     vega.wait_for_total_catchup()
     page.pause()


# TODO: Test order submitted > shown open order > open position 
# TODO: order book - Do we want to test refresh/initial added to orderbook?
# TODO: trade - Do we want to test refresh/initial added to orderbook?
# TODO: move forward in time and see it refreshed

