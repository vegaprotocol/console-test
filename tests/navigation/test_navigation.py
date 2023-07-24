import pytest
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService

@pytest.mark.usefixtures("risk_accepted")
def test_navigation(vega: VegaService, page: Page):
    page.goto(f"http://localhost:{vega.console_port}/#/markets/all")

    navbar = page.locator('nav[aria-label="Main"]')
    expect(navbar).to_be_visible()
    navbar.get_by_role('button', name="Stagnet").click()
    page.pause()

