from math import exp
import pytest
import vega_sim.api.governance as governance
import re

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

row_selector = '[data-testid="tab-proposed-markets"] .ag-center-cols-container .ag-row'
col_market_id = '[col-id="market"] [data-testid="market-code"]'


@pytest.mark.usefixtures("proposed_market", "risk_accepted")
def test_can_see_table_headers(proposed_market, vega: VegaService, page: Page):
    # setup market in proposed step, without liquidity provided
    market_id = proposed_market
    page.goto(f"/#/markets/{market_id}")

    # approve market
    governance.approve_proposal(
        key_name=MM_WALLET.name,
        proposal_id=market_id,
        wallet=vega.wallet,
    )
    page.goto(f"/#/markets/all")
    page.click('[data-testid="Proposed markets"]')

    # Test that you can see table headers
    headers = [
        "Market",
        "Description",
        "Settlement asset",
        "State",
        "Parent market",
        "Voting",
        "Closing date",
        "Enactment date",
        "",
    ]

    header_elements = page.locator(".ag-header-cell-text")
    for i, header in enumerate(headers):
        assert header_elements.nth(i).inner_text() == header


@pytest.mark.skip("Skipping as test won't work until SLA console changes released")
@pytest.mark.usefixtures("proposed_market", "risk_accepted")
def test_renders_markets_correctly(proposed_market, vega: VegaService, page: Page):
    # setup market in proposed step, without liquidity provided
    market_id = proposed_market
    page.goto(f"/#/markets/{market_id}")

    # approve market
    governance.approve_proposal(
        key_name=MM_WALLET.name,
        proposal_id=market_id,
        wallet=vega.wallet,
    )
    page.goto(f"/#/markets/all")
    page.click('[data-testid="Proposed markets"]')
    row = page.locator(row_selector)
    # 6001-MARK-049
    expect(row.locator(col_market_id)).to_have_text("BTC:DAI_2023")

    # 6001-MARK-050
    expect(row.locator('[col-id="description"]')).to_have_text("BTC:DAI_2023")

    # 6001-MARK-051
    expect(row.locator('[col-id="asset"]')).to_have_text("tDAI")

    # 6001-MARK-052
    # 6001-MARK-053
    expect(row.locator('[col-id="state"]')).to_have_text("Open")
    expect(row.locator('[col-id="parentMarket"]')).to_have_text("-")

    # 6001-MARK-054
    # 6001-MARK-055
    expect(row.get_by_test_id("vote-progress-bar-against")).to_be_visible()

    # 6001-MARK-056
    expect(row.locator('[col-id="closing-date"]')).not_to_be_empty()

    # 6001-MARK-057
    expect(row.locator('[col-id="enactment-date"]')).not_to_be_empty

    # 6001-MARK-058
    page.get_by_test_id("dropdown-menu").click()
    dropdown_content = '[data-testid="proposal-actions-content"]'
    first_item_link = (
        page.locator(f"{dropdown_content} [role='menuitem']").nth(0).locator("a")
    )

    # 6001-MARK-059
    expected_href = r"^https:\/\/governance\.stagnet1\.vega\.rocks\/proposals\/[a-f0-9]{64}$"
    assert first_item_link.inner_text() == 'View proposal'    
    assert re.match(expected_href, first_item_link.get_attribute('href'))
  
    # temporary skip 
    # 6001-MARK-060
    # proposed_markets_tab = page.get_by_test_id("tab-proposed-markets")
    # external_links = proposed_markets_tab.locator("font-alpha")
    # last_link = external_links.last
    # assert last_link.inner_text() == 'Propose a new market'
        
    # expected_href = f"https://governance.stagnet1.vega.rocks/proposals/propose/new-market"
    # assert last_link.get_attribute('href') == expected_href

@pytest.mark.usefixtures("proposed_market", "risk_accepted")
def test_can_drag_and_drop_columns(proposed_market, vega: VegaService, page: Page):
    # 6001-MARK-063
    # setup market in proposed step, without liquidity provided
    market_id = proposed_market
    page.goto(f"/#/markets/{market_id}")

    # approve market
    governance.approve_proposal(
        key_name=MM_WALLET.name,
        proposal_id=market_id,
        wallet=vega.wallet,
    )
    page.goto(f"/#/markets/all")
    page.click('[data-testid="Proposed markets"]')
    col_market = page.locator('[col-id="market"]').first
    col_vote = page.locator('[col-id="voting"]').first
    col_market.drag_to(col_vote)

    # Check the attribute of the dragged element
    attribute_value = col_market.get_attribute("aria-colindex")
    assert attribute_value != "1"


@pytest.mark.usefixtures("simple_market", "risk_accepted")
def test_can_see_no_markets_message(simple_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/all")
    page.get_by_test_id("Proposed markets").click()

    # 6001-MARK-061
    tab_proposed_markets = page.locator('[data-testid="tab-proposed-markets"]')
    assert "No markets" in tab_proposed_markets.text_content()
