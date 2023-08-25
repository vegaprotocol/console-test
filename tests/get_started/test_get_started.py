import pytest
from playwright.sync_api import expect, Page
import json
from vega_sim.service import VegaService
from fixtures.market import setup_simple_market
from conftest import init_vega
from collections import namedtuple
from actions.vega import submit_order


@pytest.fixture(scope="module")
def vega():
    with init_vega() as vega:
        yield vega


# we can reuse vega market-sim service and market in almost all tests
@pytest.fixture(scope="module")
def simple_market(vega: VegaService):
    return setup_simple_market(vega)

@pytest.mark.usefixtures("page", "risk_accepted")
def test_get_started_seen_already(simple_market, page: Page):
    page.goto(f"/#/markets/{simple_market}")
    expect(page.get_by_test_id("order-connect-wallet")).to_be_visible
    expect(page.get_by_test_id("order-connect-wallet")).to_be_enabled
    locator = page.get_by_test_id("connect-vega-wallet")
    page.wait_for_selector('[data-testid="connect-vega-wallet"]', state="attached")
    expect(locator).to_be_enabled
    expect(locator).to_be_visible
    expect(locator).to_have_text("Get started")


@pytest.mark.usefixtures("page")
def test_browser_wallet_installed(simple_market, page: Page):
    page.add_init_script("window.vega = {}")
    page.goto(f"/#/markets/{simple_market}")
    locator = page.get_by_test_id("connect-vega-wallet")
    page.wait_for_selector('[data-testid="connect-vega-wallet"]', state="attached")
    expect(locator).to_be_enabled
    expect(locator).to_be_visible
    expect(locator).to_have_text("Connect")


@pytest.mark.usefixtures("page", "risk_accepted")
def test_get_started_deal_ticket(simple_market, page: Page):
    page.goto(f"/#/markets/{simple_market}")
    expect(page.get_by_test_id("order-connect-wallet")).to_have_text("Connect wallet")


@pytest.mark.usefixtures("page", "risk_accepted")
def test_browser_wallet_installed_deal_ticket(simple_market, page: Page):
    page.add_init_script("window.vega = {}")
    page.goto(f"/#/markets/{simple_market}")
    page.wait_for_selector('[data-testid="sidebar-content"]', state="visible")
    expect(page.get_by_test_id("get-started-banner")).not_to_be_visible()


@pytest.mark.usefixtures("page")
def test_get_started_browse_all(vega: VegaService, page: Page):
    page.goto("/")
    expect(page.get_by_test_id("welcome-dialog")).to_be_visible()
    expect(page.get_by_text("Get the Vega Wallet").first).to_be_visible()
    page.get_by_test_id("browse-markets-button").click()
    expect(page).to_have_url(f"http://localhost:{vega.console_port}/#/markets/all")


@pytest.mark.usefixtures("page", "auth")
def test_redirect_default_market(continuous_market, vega: VegaService, page: Page):
    page.goto("/")
    expect(page).to_have_url(
        f"http://localhost:{vega.console_port}/#/markets/{continuous_market}"
    )
