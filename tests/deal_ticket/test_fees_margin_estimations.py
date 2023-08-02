import logging
import pytest
from collections import namedtuple
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

notional = "deal-ticket-fee-notional"
fees = "deal-ticket-fee-fees"
margin_required = "deal-ticket-fee-margin-required"
item_value = "item-value"
market_trading_mode = "market-trading-mode"

wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]


def setup_continuous_market(vega, page):
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

    vega.wait_for_total_catchup()
    vega.forward("10s")

    page.goto(f"http://localhost:{vega.console_port}/#/markets/{market_id}")

    submit_order(vega, "Key 1", market_id, "SIDE_BUY", 1, 110)

    vega.wait_for_total_catchup()
    vega.forward("10s")


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

@pytest.mark.usefixtures("auth")
def test_margin_and_fees_estimations(vega: VegaService, page: Page):
    # setup continuous trading market with one user buy trade
    setup_continuous_market(vega, page)
    market_id = vega.all_markets()[0].id

    # submit order from UI and verify fees and margin
    expect(page.get_by_test_id(notional)).to_have_text("Notional- BTC")
    expect(page.get_by_test_id(fees)).to_have_text("Fees- tDAI")
    expect(page.get_by_test_id(margin_required)).to_have_text("Margin required0.00 tDAI")
    page.get_by_test_id("order-size").type("200")
    page.get_by_test_id("order-price").type("20")

    vega.wait_fn(1)
    vega.wait_for_total_catchup()

    expect(page.get_by_test_id(notional)).to_have_text("Notional4,000.00 BTC")
    expect(page.get_by_test_id(fees)).to_have_text("Fees~402.00 tDAI")
    expect(page.get_by_test_id(margin_required)).to_have_text("Margin required1,661.72707 - 1,661.88832 tDAI")
    

    page.get_by_test_id("place-order").click()

    vega.wait_fn(1)
    vega.wait_for_total_catchup()

    expect(page.get_by_test_id(margin_required)).to_have_text("Margin required1,661.72707 - 1,661.88832 tDAI ")
    page.get_by_test_id("toast-close").click()
    
    # submit order by sim function
    order = submit_order(vega, "Key 1", market_id, "SIDE_BUY", 400, 38329483272398.838)
    vega.wait_for_total_catchup() 
    vega.forward("10s")
    expect(page.get_by_test_id(margin_required)).to_have_text("Margin required897,716,007,278,879.50 - 897,716,007,278,895.20 tDAI ")
    expect(page.get_by_test_id("deal-ticket-warning-margin")).to_contain_text("You may not have enough margin available to open this position.") 

    # cancel order and verify that warning margin disappeared 
    vega.cancel_order("Key 1", market_id, order)
    vega.wait_for_total_catchup() 
    vega.forward("10s")
    expect(page.get_by_test_id("deal-ticket-warning-auction")).to_contain_text("Any orders placed now will not trade until the auction ends") 
    
    # add order at the current price so that it is possible to change the status to price monitoring
    submit_order(vega, "Key 1", market_id, "SIDE_SELL", 1, 110)
    vega.wait_for_total_catchup() 
    vega.forward("10s")
    expect(page.get_by_test_id(margin_required)).to_have_text("Margin required1,684.36688 - 1,700.53688 tDAI")
    expect(page.get_by_test_id(market_trading_mode).get_by_test_id(item_value)).to_have_text("Continuous")
    
    #verify if we can submit order after reverted margin
    page.get_by_test_id("place-order").click()
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    expect(page.get_by_test_id("toast-content")).to_contain_text("Your transaction has been confirmed") 
