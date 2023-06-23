import re
import logging
import pytest
import helpers 
from collections import namedtuple
from playwright.sync_api import Page, expect

from vega_sim.null_service import VegaServiceNull
from config import console_port 

WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Set up parties in the market/ Submit liquidity provision/ Control midprice
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")

# The party to send selling/buying MOs to hit LP orders
TRADER_WALLET = WalletConfig("Zl3pLs6Xk6SwIK7Jlp2x", "bJQDDVGAhKkj3PVCc7Rr")

# The party randomly post LOs at buy/sell side to simulate real Market situation
RANDOM_WALLET = WalletConfig("OJpVLvU5fgLJbhNPdESa", "GmJTt9Gk34BHDlovB7AJ")

# The party to terminate the market and send settlment price
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")

wallets = [MM_WALLET, MM_WALLET2, TRADER_WALLET, RANDOM_WALLET, TERMINATE_WALLET]

def test_basic(page: Page):
    market_name = "BTC:DAI_Mar22"
    logging.basicConfig(level=logging.INFO)

    with VegaServiceNull(
        run_with_console=False,
        launch_graphql=False,
        retain_log_files=True,
        use_full_vega_wallet=True,
        store_transactions=True,
    ) as vega:
        helpers.setup(page, vega.data_node_rest_port)

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

        vega.submit_liquidity(
            key_name=MM_WALLET.name,
            market_id=market_id,
            commitment_amount=10000,
            fee=0.001,
            buy_specs=[("PEGGED_REFERENCE_MID", i * 2, i) for i in range(1, 10)],
            sell_specs=[("PEGGED_REFERENCE_MID", i * 2, i) for i in range(1, 10)],
            is_amendment=False,
        )
        vega.submit_order(
            trading_key=MM_WALLET.name,
            market_id=market_id,
            time_in_force="TIME_IN_FORCE_GTC",
            order_type="TYPE_LIMIT",
            side="SIDE_SELL",
            volume=1,
            price=100,
        )
        vega.submit_order(
            trading_key=MM_WALLET2.name,
            market_id=market_id,
            time_in_force="TIME_IN_FORCE_GTC",
            order_type="TYPE_LIMIT",
            side="SIDE_BUY",
            volume=1,
            price=100,
        )

        to_cancel = vega.submit_order(
            trading_key=MM_WALLET.name,
            market_id=market_id,
            time_in_force="TIME_IN_FORCE_GTC",
            order_type="TYPE_LIMIT",
            side="SIDE_SELL",
            volume=10,
            price=100.5,
            wait=True,
        )

        vega.cancel_order(MM_WALLET.name, market_id, to_cancel)

        vega.submit_order(
            trading_key=MM_WALLET.name,
            market_id=market_id,
            time_in_force="TIME_IN_FORCE_GTC",
            order_type="TYPE_LIMIT",
            side="SIDE_BUY",
            volume=5,
            price=110.5,
            wait=True,
        )
        vega.submit_simple_liquidity(
            key_name=MM_WALLET.name,
            market_id=market_id,
            commitment_amount=5000,
            fee=0.002,
            reference_buy="PEGGED_REFERENCE_MID",
            reference_sell="PEGGED_REFERENCE_MID",
            delta_buy=10,
            delta_sell=10,
            is_amendment=True,
        )

        margin_levels = vega.margin_levels(MM_WALLET2.name)
        print(f"Margin levels are: {margin_levels}")

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

        print("END")
  
if __name__ == "__main__":
        pytest.main([__file__])