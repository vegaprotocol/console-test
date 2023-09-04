import pytest
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from fixtures.market import setup_simple_market, setup_simple_successor_market


@pytest.fixture
@pytest.mark.usefixtures("vega")
def successor_market(vega: VegaService):
    parent_market_id = setup_simple_market(vega)
    tdai_id = vega.find_asset_id(symbol="tDAI")

    return setup_simple_successor_market(
        vega, parent_market_id, tdai_id, "successor_market"
    )


@pytest.mark.usefixtures("page", "risk_accepted")
def test_succession_line(page: Page, successor_market):
    page.goto(f"/#/markets/{successor_market}")
    page.get_by_test_id("Info").click()

    page.get_by_text("Succession line").click()

    expect(page.get_by_test_id("succession-line-item").first).to_contain_text(
        "BTC:DAI_2023BTC:DAI_2023"
    )
    expect(
        page.get_by_test_id("succession-line-item").first.get_by_role("link")
    ).to_be_attached
    expect(page.get_by_test_id("succession-line-item").last).to_contain_text(
        "successor_marketsuccessor_market"
    )
    expect(
        page.get_by_test_id("succession-line-item").last.get_by_role("link")
    ).to_be_attached
    expect(
        page.get_by_test_id("succession-line-item").last.get_by_test_id("icon-bullet")
    ).to_be_visible
