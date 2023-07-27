import pytest
import vega_sim.api.governance as governance

from collections import namedtuple
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]

market_name = "BTC:DAI_YYYYYYYYY"


def setup_market(vega: VegaService):
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

    # creates a market before proposal is approved
    market_id = vega.create_simple_market(
        market_name,
        proposal_key=MM_WALLET.name,
        settlement_asset_id=tdai_id,
        termination_key=TERMINATE_WALLET.name,
        market_decimals=5,
        approve_proposal=False,
        forward_time_to_enactment=False,
    )
    vega.wait_for_total_catchup()

    return market_id


def submit_order(vega: VegaService, wallet_name, market_id, side, volume, price):
    vega.submit_order(
        trading_key=wallet_name,
        market_id=market_id,
        time_in_force="TIME_IN_FORCE_GTC",
        order_type="TYPE_LIMIT",
        side=side,
        volume=volume,
        price=price,
    )


@pytest.mark.usefixtures("risk_accepted")
def test_market_lifecycle(vega: VegaService, page: Page):
    trading_mode = page.get_by_test_id("market-trading-mode").get_by_test_id(
        "item-value"
    )
    market_state = page.get_by_test_id("market-state").get_by_test_id("item-value")

    # setup market in proposed step, without liquidity provided
    market_id = setup_market(vega)
    page.goto(f"http://localhost:{vega.console_port}/#/markets/{market_id}")

    # check that market is in proposed state
    expect(trading_mode).to_have_text("No trading")
    expect(market_state).to_have_text("Proposed")

    # approve market
    governance.approve_proposal(
        key_name=MM_WALLET.name,
        proposal_id=market_id,
        wallet=vega.wallet,
    )

    # "wait" for market to be approved and enacted
    vega.forward("60s")
    vega.wait_for_total_catchup()

    # check that market is in pending state
    expect(trading_mode).to_have_text("Opening auction")
    expect(market_state).to_have_text("Pending")

    # Add liquidity and place some orders. Orders should match to produce the uncrossing price. A market can only move from opening auction to continuous trading when the enactment date has passed, there is sufficient liquidity and an uncrossing price is produced.
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
    submit_order(vega, MM_WALLET.name, market_id, "SIDE_SELL", 1, 100)
    submit_order(vega, MM_WALLET2.name, market_id, "SIDE_BUY", 1, 100)

    vega.forward("10s")
    vega.wait_for_total_catchup()

    # check market state is now active and trading mode is continuous
    expect(trading_mode).to_have_text("Continuous")
    expect(market_state).to_have_text("Active")

    # put invalid oracle to trigger market termination
    governance.settle_oracle(
        wallet=vega.wallet,
        oracle_name="INVALID_ORACLE",
        settlement_price=1,
        key_name=TERMINATE_WALLET.name,
    )
    vega.forward("60s")
    vega.wait_for_total_catchup()

    # market state should be changed to "Trading Terminated" because of the invalid oracle
    expect(trading_mode).to_have_text("No trading")
    expect(market_state).to_have_text("Trading Terminated")

    # settle market
    vega.settle_market(
        settlement_key=TERMINATE_WALLET.name,
        settlement_price=100,
        market_id=market_id,
    )
    vega.forward("10s")
    vega.wait_for_total_catchup()

    # check market state is now settled
    expect(trading_mode).to_have_text("No trading")
    expect(market_state).to_have_text("Settled")
