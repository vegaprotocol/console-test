import pytest
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from fixtures.market import (
    setup_simple_market,
    setup_simple_successor_market
)

@pytest.mark.usefixtures("risk_accepted")
def test_succession_line(vega: VegaService, page: Page):
    parent_market_id = setup_simple_market(vega)
    tdai_id = vega.find_asset_id(symbol="tDAI")
    market_id = setup_simple_successor_market(vega, parent_market_id, tdai_id, "successor_market")
    
    page.goto(f"/#/markets/{market_id}")
    page.get_by_test_id('Info').click()
    page.get_by_text('Succession line').click()

    expect(page.get_by_test_id('succession-line-item').first).to_contain_text('BTC:DAI_2023BTC:DAI_2023')
    expect(page.get_by_test_id('succession-line-item').first.get_by_role('link')).to_be_attached
    expect(page.get_by_test_id('succession-line-item').last).to_contain_text('successor_marketsuccessor_market')
    expect(page.get_by_test_id('succession-line-item').last.get_by_role('link')).to_be_attached
    expect(page.get_by_test_id('succession-line-item').last.get_by_test_id('icon-bullet')).to_be_visible