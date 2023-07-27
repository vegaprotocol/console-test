import pytest
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService

@pytest.mark.usefixtures("risk_accepted")
def test_network_switcher(vega: VegaService, page: Page):
    setup(vega, page)
    navbar = page.locator('nav[aria-label="Main"]')
    assert_network_switcher(navbar)
    
@pytest.mark.usefixtures("risk_accepted")
def test_navbar_pages(vega: VegaService, page: Page):
    setup(vega, page)
    navbar = page.locator('nav[aria-label="Main"]')
    assert_links(navbar)

@pytest.mark.usefixtures("risk_accepted")
def test_navigation_mobile(vega: VegaService, page: Page):
    setup(vega, page)
    page.set_viewport_size({
        "width": 800,
        "height": 1040
    })
    navbar = page.locator('nav[aria-label="Main"]')

    # region navigation
    burger = navbar.get_by_test_id("navbar-mobile-burger")
    expect(burger).to_be_visible()
    burger.click()
    menu = navbar.get_by_test_id("navbar-menu-content")
    expect(menu).to_be_visible()
    assert_links(menu)
    assert_network_switcher(menu)
    menu.get_by_role("button", name="Close menu").click()
    # endregion

    # region wallet
    wallet_button = navbar.get_by_test_id("navbar-mobile-wallet")
    expect(wallet_button).to_be_visible()
    wallet_button.click()
    dialog = page.get_by_test_id("dialog-content")
    expect(dialog.get_by_test_id("wallet-dialog-title")).to_be_visible()
    # endregion

def setup(vega, page):
    page.goto(f"http://localhost:{vega.console_port}/#/disclaimer")

def assert_links(container):
    pages = [
        {"name": "Markets", "href": "#/markets/all"},
        {"name": "Trading", "href": "#/markets/"},
        {"name": "Portfolio", "href": "#/portfolio"}
    ]

    for page in pages:
        link = container.get_by_role("link", name=page["name"])
        expect(link).to_be_visible()
        expect(link).to_have_attribute("href", page["href"])

    # False indicates external link configured by env var
    resource_pages = [
        {"name": "Docs", "href": False},
        {"name": "Give Feedback", "href": False },
        {"name": "Disclaimer", "href": "#/disclaimer"}
    ]   

    container.get_by_role("button", name="Resources").click()

    dropdown = container.get_by_test_id("navbar-content-resources")

    for resource_page in resource_pages:
        page_name = resource_page["name"]
        page_href = resource_page["href"]
        link = dropdown.get_by_role("link", name=page_name)
        expect(link).to_be_visible()
        if not page_href:
            href = link.get_attribute("href")
            expect(link).to_have_attribute("target", "_blank")
            assert len(href) >= 0, f"href for {page_name} is empty"
        else:
            expect(link).to_have_attribute("href", page_href)

def assert_network_switcher(container):
    network_switcher_trigger = container.get_by_role('button', name="Stagnet")
    network_switcher_trigger.click()
    dropdown = container.get_by_test_id("navbar-content-network-switcher")
    expect(dropdown).to_be_visible()
    links = dropdown.get_by_role("link")
    expect(links).to_have_count(2)
    expect(container.get_by_role("link", name="Mainnet")).to_be_visible()
    expect(container.get_by_role("link", name="Fairground testnet")).to_be_visible()