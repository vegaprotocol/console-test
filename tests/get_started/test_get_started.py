import pytest
from playwright.sync_api import expect, Page
from playwright.sync_api import expect
from vega_sim.service import VegaService

@pytest.mark.usefixtures("simple_market")
def test_get_started_dialog(page: Page):
    page.goto(f"/#/disclaimer")
    expect(page.get_by_test_id('welcome-dialog')).to_be_visible()
    expect(page.get_by_test_id('get-started-button')).to_be_visible()
    page.get_by_test_id('get-started-button').click()
    expect(page.get_by_test_id('connector-jsonRpc')).to_be_visible()
    
@pytest.mark.usefixtures("simple_market","risk_accepted")
def test_get_started_seen_already(simple_market, page: Page):
    page.goto(f"/#/markets/{simple_market}")
    locator = page.get_by_test_id('connect-vega-wallet')
    page.wait_for_selector('[data-testid="connect-vega-wallet"]', state='attached')
    expect(locator).to_be_enabled
    expect(locator).to_be_visible
    expect(locator).to_have_text('Get started')

@pytest.mark.usefixtures("simple_market")
def test_browser_wallet_installed(simple_market, page: Page):
    page.add_init_script("window.vega = {}")
    page.goto(f"/#/markets/{simple_market}")
    locator = page.get_by_test_id('connect-vega-wallet')
    page.wait_for_selector('[data-testid="connect-vega-wallet"]', state='attached')
    expect(locator).to_be_enabled
    expect(locator).to_be_visible
    expect(locator).to_have_text('Connect')

@pytest.mark.usefixtures("simple_market","risk_accepted")
def test_get_started_deal_ticket(simple_market, page: Page):
    page.goto(f"/#/markets/{simple_market}")
    locator = page.get_by_test_id('get-started-button')
    page.wait_for_selector('[data-testid="get-started-banner"]', state='attached')
    expect(page.get_by_test_id('get-started-banner')).to_be_visible
    expect(locator).to_be_enabled
    expect(locator).to_have_text('Get started')

@pytest.mark.usefixtures("simple_market","risk_accepted")
def test_browser_wallet_installed_deal_ticket(simple_market, page: Page):
    page.add_init_script("window.vega = {}")
    page.goto(f"/#/markets/{simple_market}")
    page.wait_for_selector('[data-testid="sidebar-content"]', state='visible')
    expect(page.get_by_test_id('get-started-banner')).not_to_be_visible()

@pytest.mark.usefixtures("simple_market")
def test_get_started_browse_all(vega: VegaService, page: Page):
    page.goto("/")
    page.get_by_test_id("browse-markets-button").click()
    expect(page).to_have_url(f"http://localhost:{vega.console_port}/#/markets/all")
    assert page.evaluate("localStorage.getItem('vega_onboarding_viewed')") == 'true'


@pytest.mark.usefixtures("continuous_market", "auth")
def test_redirect_default_market(continuous_market, vega:VegaService, page: Page):
    page.goto("/")
    expect(page).to_have_url(f"http://localhost:{vega.console_port}/#/markets/{continuous_market}")
