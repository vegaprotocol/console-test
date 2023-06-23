
import logging
import pytest
import helpers

from collections import namedtuple
from playwright.sync_api import Page, expect

from vega_sim.null_service import VegaServiceNull

WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Set up parties in the market/ Submit liquidity provision/ Control midprice
MM_WALLET = WalletConfig("mm", "pin")

TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, TERMINATE_WALLET]

def test_settlement(page: Page):
    market_name = "BTC:DAI_Mar22"
    logging.basicConfig(level=logging.INFO)

    with VegaServiceNull(
        run_with_console=False,
        launch_graphql=False,
        retain_log_files=True,
        use_full_vega_wallet=True,
        store_transactions=True,
    ) as vega:
        console_port = helpers.setup(page, vega.data_node_rest_port)

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
  
        vega.forward("10s")

        page.goto(f"http://localhost:{console_port}/#/markets/all")
        # Manually change node to one served by vega-sim
        page.get_by_text("Change node").click()
        page.query_selector('[data-testid="custom-node"] input').fill(f"http://localhost:{vega.data_node_rest_port}/graphql")
        page.get_by_text("Connect to this node").click()

        # Navigate to chosen market
        result = page.get_by_text(market_name)
        result.first.click()
        assert market_id in page.url 
        expect(page.get_by_text(market_name).first).to_be_attached()

        vega.settle_market(
            settlement_key=TERMINATE_WALLET.name,
            settlement_price=100,
            market_id=market_id,
        )

        vega.wait_for_total_catchup()
        vega.forward("10s")

        helpers.teardown()
        print("END")

if __name__ == "__main__":
        pytest.main([__file__])