import pytest
from collections import namedtuple
from playwright.sync_api import expect, Page
from vega_sim.service import VegaService
from actions.vega import submit_order
from conftest import init_vega
from fixtures.market import setup_continuous_market
from actions.utils import verify_trades_grid, wait_for_graphql_response, verify_orderbook_grid, verify_row

# Defined namedtuples
WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])

# Wallet Configurations
MM_WALLET = WalletConfig("mm", "pin")
MM_WALLET2 = WalletConfig("mm2", "pin2")
TERMINATE_WALLET = WalletConfig("FJMKnwfZdd48C8NqvYrG", "bY3DxwtsCstMIIZdNpKs")


wallets = [MM_WALLET, MM_WALLET2, TERMINATE_WALLET]


def hover_and_assert_tooltip(page: Page, element_text):
    element = page.get_by_text(element_text)
    element.hover()
    expect(page.get_by_role("tooltip")).to_be_visible()


class TestIcebergOrdersValidations:
    @pytest.fixture(scope="class")
    def vega(self, request):
        with init_vega(request) as vega:
            yield vega

    @pytest.fixture(scope="class")
    def continuous_market(self, vega):
        return setup_continuous_market(vega)

    @pytest.mark.usefixtures("page", "auth", "risk_accepted")
    def test_iceberg_submit(self, continuous_market, vega: VegaService, page: Page):
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

        vega.forward("10s")
        vega.wait_fn(1)
        vega.wait_for_total_catchup()
        expect(page.get_by_test_id("toast-content")).to_have_text(
            "Order filledYour transaction has been confirmed View in block explorerSubmit order - filledBTC:DAI_2023+3 @ 107.00 tDAI"
        )
        page.get_by_test_id("All").click()
        expect(
            (page.get_by_role("row").locator('[col-id="type"]')).nth(1)
        ).to_have_text("Limit (Iceberg)")


    #TODO Refactor to Jest
    @pytest.mark.usefixtures("page", "auth", "risk_accepted")
    def test_iceberg_tooltips(self, continuous_market, page: Page):
        page.goto(f"/#/markets/{continuous_market}")
        page.get_by_test_id("iceberg").hover()
        expect(page.get_by_role("tooltip")).to_be_visible()
        page.get_by_test_id("iceberg").click()
        hover_and_assert_tooltip(page, "Peak size")
        hover_and_assert_tooltip(page, "Minimum size")

    #TODO Refactor to Jest
    @pytest.mark.usefixtures("page", "auth", "risk_accepted")
    def test_iceberg_validations(self, continuous_market, page: Page):
        page.goto(f"/#/markets/{continuous_market}")
        page.get_by_test_id("iceberg").click()
        page.get_by_test_id("place-order").click()
        expect(page.get_by_test_id("deal-ticket-peak-error-message")).to_be_visible()
        expect(page.get_by_test_id("deal-ticket-peak-error-message")).to_have_text(
            "You need to provide a peak size"
        )
        expect(page.get_by_test_id("deal-ticket-minimum-error-message")).to_be_visible()
        expect(page.get_by_test_id("deal-ticket-minimum-error-message")).to_have_text(
            "You need to provide a minimum visible size"
        )
        page.get_by_test_id("order-peak-size").clear()
        page.get_by_test_id("order-peak-size").type("1")
        page.get_by_test_id("order-minimum-size").clear()
        page.get_by_test_id("order-minimum-size").type("2")
        expect(page.get_by_test_id("deal-ticket-peak-error-message")).to_be_visible()
        expect(page.get_by_test_id("deal-ticket-peak-error-message")).to_have_text(
            "Peak size cannot be greater than the size (0)"
        )
        expect(page.get_by_test_id("deal-ticket-minimum-error-message")).to_be_visible()
        expect(page.get_by_test_id("deal-ticket-minimum-error-message")).to_have_text(
            "Minimum visible size cannot be greater than the peak size (1)"
        )
        page.get_by_test_id("order-minimum-size").clear()
        page.get_by_test_id("order-minimum-size").type("0.1")
        expect(page.get_by_test_id("deal-ticket-minimum-error-message")).to_be_visible()
        expect(page.get_by_test_id("deal-ticket-minimum-error-message")).to_have_text(
            "Minimum visible size cannot be lower than 1"
        )


@pytest.mark.usefixtures("vega", "page", "continuous_market", "auth", "risk_accepted")
def test_iceberg_open_order(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")

    submit_order(vega, "Key 1", continuous_market, "SIDE_SELL", 102, 101, 2, 1)
    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    wait_for_graphql_response(page, "Positions")
    expected_values = {
        "marketCode": "BTC:DAI_2023tDAIFutr",
        "openVolume": "-989,947.00",
        "markPrice": "101.50101.50",
        "margin": "885.704321.0x",
        "liquidationPrice": "9,756.50813",
        "realisedPNL": "-6.00",
        "unrealisedPNL": "0.00",
    }
    verify_row(page, expected_values, row_index=2)
    expected_values = {
        "instrument-code": "BTC:DAI_2023Futr",
        "remaining": "99",
        "size": "-102",
        "type": "Limit (Iceberg)",
        "status": "Active",
        "price": "101.00",
        "timeInForce": "GTC",
        "updatedAt": "",
    }
    verify_row(page, expected_values, grid_id= "Open", row_index=2)
    #TODO how do we validate trades

    trades_content = [
        [101.50, 99, ],
        [107.50, 1, ],
        
    ]
    page.pause()
    #TODO trades grid validate
    verify_trades_grid(page, trades_content)
    orderbook_content = [
        [110.00000, 1, 103],
        [101.00000, 3, 102],
        [99.00000, 99, 99],
        # mid
        [95.00000, 1, 1],
        [90.00000, 1, 2],
    ]
   
    verify_orderbook_grid(page, orderbook_content, last_trade_price = "101.50")

    
    submit_order(vega, MM_WALLET2.name, continuous_market, "SIDE_BUY", 103, 101)

    vega.forward("10s")
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    orderbook_content = [
        [110.00000, 1, 1],
        # mid
        [101.00000, 1, 1],
        [95.00000, 1, 2],
        [90.00000, 1, 3],
    ]
   
    verify_orderbook_grid(page, orderbook_content, last_trade_price = "101.00")
    expect(
        page.locator(
            '[data-testid="tab-open-orders"] .ag-center-cols-container .ag-row'
        )
    ).not_to_be_visible

    expected_values = {
        "instrument-code": "BTC:DAI_2023Futr",
        "remaining": "102",
        "size": "-102",
        "type": "Limit (Iceberg)",
        "status": "Filled",
        "price": "101.00",
        "timeInForce": "GTC",
        "updatedAt": "",
    }
    verify_row(page, expected_values, grid_id= "Closed", row_index=2)
    page.pause()
    expected_values = {
        "price": "101.00",
        "size": "3",
        "createdAt": ""
    }
    verify_row(page, expected_values, grid_id= "Trades")

    expected_values = {
        "price": "99.50",
        "size": "99",
        "createdAt": ""
    }
    verify_trades_grid(page, expected_values, grid_id= "Trades", trade_row_index=1)

   

def verify_order_label(page: Page, test_id: str, expected_text: str):
    element = page.get_by_test_id(test_id)
    expect(element).to_be_visible()
    expect(element).to_have_text(expected_text)


def verify_order_value(page: Page, test_id: str, expected_text: str):
    element = page.get_by_test_id(test_id)
    expect(element).to_be_visible()
    expect(element).to_have_text(expected_text)
