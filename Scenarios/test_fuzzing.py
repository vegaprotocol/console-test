import pytest
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService


from vega_sim.scenario.fuzzed_markets.scenario import FuzzingScenario
from vega_sim.scenario.constants import Network

@pytest.mark.skip("comment out to run")
@pytest.mark.usefixtures("page", "risk_accepted", "continuous_market", "auth")
def test_test(page: Page, continuous_market, vega: VegaService):
    page.goto(f"/#/markets/{continuous_market}")
    scenario = FuzzingScenario(
        num_steps=100,
        # step_length_seconds=30,
        block_length_seconds=1,
        transactions_per_block=4096,
    )

    scenario.run_iteration(
            vega=vega,
            network=Network.NULLCHAIN,
        )