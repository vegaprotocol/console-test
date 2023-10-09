import pytest
import re
import vega_sim.api.governance as governance
from vega_sim.service import VegaService
from playwright.sync_api import Page, expect
from fixtures.market import setup_continuous_market
from conftest import init_vega

import vega_sim.proto.vega.data.v1 as oracles_protos
import vega_sim.proto.vega.data_source_pb2 as data_source_protos
import vega_sim.proto.vega.governance_pb2 as gov_protos
import vega_sim.proto.vega as vega_protos

@pytest.fixture(scope="class")
def vega():
    with init_vega() as vega:
        yield vega


@pytest.fixture(scope="class")
def create_settled_market(vega):
    market_id = setup_continuous_market(vega)
    vega.settle_market(
        settlement_key="FJMKnwfZdd48C8NqvYrG",
        settlement_price=110,
        market_id=market_id,
    )
    vega.forward("10s")
    vega.wait_fn(10)
    vega.wait_for_total_catchup()


class TestSettledMarket:
    @pytest.mark.usefixtures("risk_accepted", "auth")
    def test_settled_header(self, page: Page, create_settled_market):
        page.goto(f"/#/markets/all")
        page.get_by_test_id("Closed markets").click()
        headers = [
            "Market",
            "Status",
            "Settlement date",
            "Best bid",
            "Best offer",
            "Mark price",
            "Settlement price",
            "Settlement asset",
            "",
        ]

        page.wait_for_selector('[data-testid="tab-closed-markets"]', state="visible")
        page_headers = (
            page.get_by_test_id("tab-closed-markets")
            .locator(".ag-header-cell-text")
            .all()
        )
        for i, header in enumerate(headers):
            expect(page_headers[i]).to_have_text(header)

    @pytest.mark.usefixtures(
        "risk_accepted",
        "auth",
    )
    def test_settled_rows(self, page: Page, create_settled_market):
        page.goto(f"/#/markets/all")
        page.get_by_test_id("Closed markets").click()

        row_selector = page.locator(
            '[data-testid="tab-closed-markets"] .ag-center-cols-container .ag-row'
        ).first

        # 6001-MARK-001
        expect(row_selector.locator('[col-id="code"]')).to_have_text("BTC:DAI_2023Futr")
        # 6001-MARK-003
        expect(row_selector.locator('[col-id="state"]')).to_have_text("Settled")
        # 6001-MARK-004
        # 6001-MARK-005
        # 6001-MARK-009
        # 6001-MARK-008
        # 6001-MARK-010
        expect(row_selector.locator('[col-id="settlementDate"]')).to_have_text(
            "5 months ago"
        )
        expected_pattern = re.compile(r"https://.*?/oracles/[a-f0-9]{64}")
        actual_href = row_selector.locator(
            '[col-id="settlementDate"] [data-testid="link"]'
        ).get_attribute("href")
        assert expected_pattern.match(
            actual_href
        ), f"Expected href to match {expected_pattern.pattern}, but got {actual_href}"
        # 6001-MARK-011
        expect(row_selector.locator('[col-id="bestBidPrice"]')).to_have_text("0.00")
        # 6001-MARK-012
        expect(row_selector.locator('[col-id="bestOfferPrice"]')).to_have_text("0.00")
        # 6001-MARK-013 
        expect(row_selector.locator('[col-id="markPrice"]')).to_have_text("110.00")
        # 6001-MARK-014
        # 6001-MARK-015
        # 6001-MARK-016
        #tbd currently we have value unknown 
        # expect(row_selector.locator('[col-id="settlementDataOracleId"]')).to_have_text(
        #     "110.00"
        # )
        expected_pattern = re.compile(r"https://.*?/oracles/[a-f0-9]{64}")
        actual_href = row_selector.locator(
            '[col-id="settlementDataOracleId"] [data-testid="link"]'
        ).get_attribute("href")
        assert expected_pattern.match(
            actual_href
        ), f"Expected href to match {expected_pattern.pattern}, but got {actual_href}"

        # 6001-MARK-018
        expect(row_selector.locator('[col-id="settlementAsset"]')).to_have_text("tDAI")
        # 6001-MARK-020
        expect(row_selector.locator('[col-id="settlementDate"]')).to_have_text(
            "5 months ago"
        )


@pytest.mark.usefixtures("risk_accepted", "auth")
def test_terminated_market_no_settlement_date(page: Page, vega: VegaService):
    setup_continuous_market(vega)
    governance.settle_oracle(
        wallet=vega.wallet,
        oracle_name="INVALID_ORACLE",
        settlement_price=110,
        key_name="FJMKnwfZdd48C8NqvYrG",
    )
    vega.forward("60s")
    vega.wait_fn(10)
    vega.wait_for_total_catchup()
    page.goto(f"/#/markets/all")
    page.get_by_test_id("Closed markets").click()
    row_selector = page.locator(
        '[data-testid="tab-closed-markets"] .ag-center-cols-container .ag-row'
    ).first
    expect(row_selector.locator('[col-id="state"]')).to_have_text("Trading Terminated")
    expect(row_selector.locator('[col-id="settlementDate"]')).to_have_text("Unknown")

    # TODO Create test for terminated market with settlement date in future
    # TODO Create test for terminated market with settlement date in past


@pytest.mark.usefixtures("risk_accepted", "auth", "continuous_market")
def test_future_closed(page: Page, vega: VegaService, continuous_market):
    base_spec = vega.market_info(continuous_market)
    now = vega.get_blockchain_time(in_seconds=True)
    fut = base_spec.tradable_instrument.instrument.future

    now = vega.get_blockchain_time(in_seconds=True)
    print(f"Current Blockchain Time: {now}")
    update_prod = gov_protos.UpdateInstrumentConfiguration(
        code=base_spec.tradable_instrument.instrument.code,
        future=gov_protos.UpdateFutureProduct(
            quote_name=fut.quote_name,
            data_source_spec_for_trading_termination=data_source_protos.DataSourceDefinition(
                internal=data_source_protos.DataSourceDefinitionInternal(
                    time=data_source_protos.DataSourceSpecConfigurationTime(
                        conditions=[
                            oracles_protos.spec.Condition(
                                value=f"{now + 300}",
                                operator=oracles_protos.spec.Condition.Operator.OPERATOR_GREATER_THAN_OR_EQUAL,
                            )
                        ]
                    )
                )
            ),
            data_source_spec_for_settlement_data=fut.data_source_spec_for_settlement_data.data,
            data_source_spec_binding=vega_protos.markets.DataSourceSpecToFutureBinding(
                settlement_data_property=fut.data_source_spec_binding.settlement_data_property,
                trading_termination_property="vegaprotocol.builtin.timestamp",
            ),
        ),
    )

    update_status = vega.update_market(
    proposal_key="mm",
    market_id=continuous_market,
    updated_instrument=update_prod,
)
    print(f"Update Status: {update_status}")
    
    vega.forward("10s")
    vega.wait_fn(10)
    vega.wait_for_total_catchup()
    page.goto(f"/#/markets/all")
    page.pause()

