import pytest
from collections import namedtuple
from playwright.sync_api import Page, expect


# Wallet Configurations
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]

row_selector = '[data-testid="tab-all-markets"] .ag-center-cols-container .ag-row'
trading_mode_col = '[col-id="tradingMode"]'
state_col = '[col-id="state"]'

initial_commitment: float = 100
mint_amount: float = 10000
initial_price: float = 1
initial_volume: float = 1
initial_spread: float = 0.1
market_name = "BTC:DAI_YYYYYYYYY"

@pytest.fixture(scope="function")
def setup_simple_market(vega):
    for wallet in wallets:
        vega.create_key(wallet.name)

    vega.mint(
        MM_WALLET.name,
        asset="VOTE",
        amount=mint_amount,
    )

    vega.update_network_parameter(
        MM_WALLET.name, parameter="market.fee.factors.makerFee", new_value="0.1"
    )
    vega.forward("10s")
    vega.wait_for_total_catchup()

    vega.create_asset(
        MM_WALLET.name,
        name="tDAI",
        symbol="tDAI",
        decimals=5,
        max_faucet_amount=1e10,
    )

    vega.wait_for_total_catchup()
    tdai_id = vega.find_asset_id(symbol="tDAI")
    print("TDAI: ", tdai_id)

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
    vega.forward("10s")
    