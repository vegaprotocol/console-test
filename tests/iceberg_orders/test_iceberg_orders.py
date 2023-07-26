import pytest
from collections import namedtuple
from playwright.sync_api import expect

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")


wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]

def setup_continuous_market(vega, page):
    market_name = "BTC:DAI_Mar22"

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

    vega.create_asset(MM_WALLET.name, name="tDAI",
                      symbol="tDAI", decimals=5, max_faucet_amount=1e10)
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

    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 1, 110)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 1, 90)
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 1, 105)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 1, 95)

    vega.forward("10s")
    vega.wait_for_total_catchup()
    

    page.goto(f"http://localhost:{vega.console_port}/#/markets/{market_id}")

    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 1, 110)
    vega.forward("10s")
    vega.wait_for_total_catchup()
    
    vega.submit_order(
        trading_key="Key 1",
        market_id=market_id,
        order_type="TYPE_LIMIT",
        time_in_force="TIME_IN_FORCE_GTC",
        side="SIDE_SELL",
        price=120,
        volume=10,
        peak_size=5,
        minimum_visible_size=2,
    )


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
def hover_and_assert_tooltip(page, element_text):
    element = page.get_by_text(element_text)
    element.hover()
    expect(page.get_by_role("tooltip")).to_be_visible()

@pytest.mark.usefixtures("auth")
def test_iceberg_submit(vega, page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)
    
    page.get_by_test_id('iceberg').click()
    page.get_by_test_id('order-peak-size').fill("2")
    page.get_by_test_id('order-minimum-size').fill("1")
    page.get_by_test_id('order-size').fill("3")
    page.get_by_test_id('order-price').fill("107")
    page.get_by_test_id('place-order').click()
    page.pause()
    
@pytest.mark.usefixtures("auth")
def test_iceberg_tooltips(vega, page):
    setup_continuous_market(vega, page)
    hover_and_assert_tooltip(page, "Iceberg")
    page.get_by_test_id('iceberg').click()
    hover_and_assert_tooltip(page, 'Peak size')
    hover_and_assert_tooltip(page, 'Minimum size')

@pytest.mark.usefixtures("auth")
def test_iceberg_validations(vega, page):
    setup_continuous_market(vega, page)
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

# TODO: Test order submitted > shown open order > open position 
# TODO: order book - Do we want to test refresh/initial added to orderbook?
# TODO: trade - Do we want to test refresh/initial added to orderbook?
# TODO: move forward in time and see it refreshed

# TODO: market sim to use latest wallet
# ERROR OCCURREDThe transaction does not use a valid Vega command: unknown field "icebergOpts" in vega.commands.v1.OrderSubmission
# TODO: market sim position decimals
# TODO: market sim submit iceberg order
