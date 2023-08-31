import pytest
from collections import namedtuple
from playwright.sync_api import expect, Page
from vega_sim.service import VegaService
from actions.vega import submit_order

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")


wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]


def hover_and_assert_tooltip(page, element_text):
    element = page.get_by_text(element_text)
    element.hover()
    expect(page.get_by_role("tooltip")).to_be_visible()

@pytest.mark.usefixtures("page", "vega", "continuous_market", "auth", "risk_accepted")
def test_iceberg_submit(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    page.get_by_test_id("iceberg").click()
    page.get_by_test_id("order-peak-size").type("2")
    page.get_by_test_id("order-minimum-size").type("1")
    page.get_by_test_id("order-size").type("3")
    page.get_by_test_id("order-price").type("107")
    page.get_by_test_id("place-order").click()

    expect(page.get_by_test_id("toast-content")).to_have_text(
        "Awaiting confirmationPlease wait for your transaction to be confirmedView in block explorer"
    )

    vega.wait_fn(10)
    vega.forward("10s")
    vega.wait_for_total_catchup()
    expect(page.get_by_test_id("toast-content")).to_have_text(
        "Order filledYour transaction has been confirmed View in block explorerSubmit order - filledBTC:DAI_2023+3 @ 107.00 tDAI"
    )
    page.get_by_test_id("All").click()
    expect(
        (page.get_by_role("row").locator('[col-id="type"]')).nth(1)
    ).to_have_text("Limit (Iceberg)")


@pytest.mark.usefixtures("page", "continuous_market", "auth", "risk_accepted")
def test_iceberg_tooltips(continuous_market, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    hover_and_assert_tooltip(page, "Iceberg")
    page.get_by_test_id("iceberg").click()
    hover_and_assert_tooltip(page, "Peak size")
    hover_and_assert_tooltip(page, "Minimum size")


@pytest.mark.usefixtures("page", "continuous_market", "auth", "risk_accepted")
def test_iceberg_validations(continuous_market, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    page.get_by_test_id("iceberg").click()
    page.get_by_test_id("place-order").click()
    expect(
        page.get_by_test_id("deal-ticket-peak-error-message-size-limit")
    ).to_be_visible()
    expect(
        page.get_by_test_id("deal-ticket-peak-error-message-size-limit")
    ).to_have_text("You need to provide a peak size")
    expect(
        page.get_by_test_id("deal-ticket-minimum-error-message-size-limit")
    ).to_be_visible()
    expect(
        page.get_by_test_id("deal-ticket-minimum-error-message-size-limit")
    ).to_have_text("You need to provide a minimum visible size")
    page.get_by_test_id("order-peak-size").clear()
    page.get_by_test_id("order-peak-size").type("1")
    page.get_by_test_id("order-minimum-size").clear()
    page.get_by_test_id("order-minimum-size").type("2")
    expect(
        page.get_by_test_id("deal-ticket-peak-error-message-size-limit")
    ).to_be_visible()
    expect(
        page.get_by_test_id("deal-ticket-peak-error-message-size-limit")
    ).to_have_text("Peak size cannot be greater than the size (0)")
    expect(
        page.get_by_test_id("deal-ticket-minimum-error-message-size-limit")
    ).to_be_visible()
    expect(
        page.get_by_test_id("deal-ticket-minimum-error-message-size-limit")
    ).to_have_text("Minimum visible size cannot be greater than the peak size (1)")
    page.get_by_test_id("order-minimum-size").clear()
    page.get_by_test_id("order-minimum-size").type("0.1")
    expect(
        page.get_by_test_id("deal-ticket-minimum-error-message-size-limit")
    ).to_be_visible()
    expect(
        page.get_by_test_id("deal-ticket-minimum-error-message-size-limit")
    ).to_have_text("Minimum visible size cannot be lower than 1")


@pytest.mark.usefixtures("vega", "page", "continuous_market", "auth", "risk_accepted")
def test_iceberg_open_order(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")

    submit_order(vega, "Key 1", vega.all_markets()[0].id, "SIDE_SELL", 102, 101, 2, 1)
    vega.forward("10s")
    vega.wait_for_total_catchup()

    page.wait_for_selector(".ag-center-cols-container .ag-row")
    expect(
        page.locator(
            ".ag-center-cols-container .ag-row [col-id='openVolume'] [data-testid='stack-cell-primary']"
        )
    ).to_have_text("-98")
    page.get_by_test_id("Open").click()
    page.wait_for_selector(".ag-center-cols-container .ag-row")

    expect(
        page.locator(".ag-center-cols-container .ag-row [col-id='remaining']")
    ).to_have_text("99")
    expect(
        page.locator(".ag-center-cols-container .ag-row [col-id='size']")
    ).to_have_text("-102")
    expect(
        page.locator(".ag-center-cols-container .ag-row [col-id='type'] ")
    ).to_have_text("Limit (Iceberg)")
    expect(
        page.locator(".ag-center-cols-container .ag-row [col-id='status']")
    ).to_have_text("Active")
    expect(page.get_by_test_id("price-10100000")).to_be_visible
    expect(page.get_by_test_id("ask-vol-10100000")).to_have_text("3")
    page.get_by_test_id("Trades").click()
    expect(page.locator('[id^="cell-price-"]').first).to_have_text("101.50")
    expect(page.locator('[id^="cell-size-"]').first).to_have_text("99")

    submit_order(vega, MM_WALLET2.name, vega.all_markets()[0].id, "SIDE_BUY", 103, 101)

    vega.forward("10s")
    vega.wait_for_total_catchup()
    expect(
        page.locator(
            '[data-testid="tab-open-orders"] .ag-center-cols-container .ag-row'
        )
    ).not_to_be_visible
    page.get_by_test_id("Closed").click()
    expect(
        page.locator(".ag-center-cols-container .ag-row [col-id='remaining']").first
    ).to_have_text("102")
    expect(
        page.locator(
            "[data-testid=\"tab-closed-orders\"] .ag-center-cols-container .ag-row [col-id='size']"
        ).first
    ).to_have_text("-102")
    expect(
        page.locator(
            "[data-testid=\"tab-closed-orders\"] .ag-center-cols-container .ag-row [col-id='type']"
        ).first
    ).to_have_text("Limit (Iceberg)")
    expect(
        page.locator(
            "[data-testid=\"tab-closed-orders\"] .ag-center-cols-container .ag-row [col-id='status']"
        ).first
    ).to_have_text("Filled")
    expect(page.locator('[id^="cell-price-"]').nth(2)).to_have_text("101.00")
    expect(page.locator('[id^="cell-size-"]').nth(2)).to_have_text("3")


def verify_order_label(page: Page, test_id: str, expected_text: str):
    element = page.get_by_test_id(test_id)
    expect(element).to_be_visible()
    expect(element).to_have_text(expected_text)


def verify_order_value(page: Page, test_id: str, expected_text: str):
    element = page.get_by_test_id(test_id)
    expect(element).to_be_visible()
    expect(element).to_have_text(expected_text)
