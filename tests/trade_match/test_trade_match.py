import pytest
from playwright.sync_api import expect, Page
from vega_sim.service import VegaService

from actions.vega import submit_multiple_orders


@pytest.mark.usefixtures("opening_auction_market", "auth")
def test_trade_match_table(opening_auction_market: str, vega: VegaService, page: Page):
    positions_button = page.get_by_test_id("Positions")
    open_button = page.get_by_test_id("Open")
    closed_button = page.get_by_test_id("Closed")
    rejected_button = page.get_by_test_id("Rejected")
    all_button = page.get_by_test_id("All")
    stop_orders_button = page.get_by_test_id("Stop orders")
    fills_button = page.get_by_test_id("Fills")
    collateral_button = page.get_by_test_id("Collateral")

    positions_tab = page.get_by_test_id("tab-positions")
    open_tab = page.get_by_test_id("tab-open-orders")
    closed_tab = page.get_by_test_id("tab-closed-orders")
    rejected_tab = page.get_by_test_id("tab-rejected-orders")
    all_tab = page.get_by_test_id("tab-orders")
    stop_orders_tab = page.get_by_test_id("tab-stop-orders")
    fills_tab = page.get_by_test_id("tab-fills")
    collateral_tab = page.get_by_test_id("tab-accounts")

    row_locator = ".ag-center-cols-container .ag-row"

    page.goto(f"/#/markets/{opening_auction_market}")

    submit_multiple_orders(
        vega,
        "Key 1",
        opening_auction_market,
        "SIDE_BUY",
        [[5, 110], [5, 105], [1, 50]],
    )
    # sending order to be rejected, wait=False to avoid returning error from market-sim
    vega.submit_order(
        trading_key="Key 1",
        market_id=opening_auction_market,
        time_in_force="TIME_IN_FORCE_GTC",
        order_type="TYPE_LIMIT",
        side="SIDE_BUY",
        volume=1,
        price=10e15,
        wait=False,
    )
    vega.forward("10s")
    vega.wait_for_total_catchup()
    submit_multiple_orders(
        vega,
        "Key 1",
        opening_auction_market,
        "SIDE_SELL",
        [[5, 90], [5, 95], [1, 150]],
    )
    vega.forward("60s")
    vega.wait_for_total_catchup()

    # Positions
    positions_button.click()
    expect(positions_tab.locator(row_locator)).to_contain_text(
        "BTC:DAI_2023"
        + "426.00"
        + "-4"
        + "-"
        + "237,005.6825 - 237,230.49968"
        + "tDAI"
        + "106.50"
        + "0.0"
        + "43.94338"
        + "1.50"
        + "0.00"
    )

    # Open
    open_button.click()
    rows = open_tab.locator(row_locator).all()
    expect(rows[0]).to_contain_text(
        "BTC:DAI_2023" + "0" + "-1" + "Limit" + "Active" + "150.00" + "GTC"
    )
    expect(rows[1]).to_contain_text(
        "BTC:DAI_2023" + "0" + "+1" + "Limit" + "Active" + "50.00" + "GTC"
    )
    expect(rows[2]).to_contain_text(
        "BTC:DAI_2023" + "1" + "+5" + "Limit" + "Active" + "105.00" + "GTC"
    )

    # Closed
    closed_button.click()
    rows = closed_tab.locator(row_locator).all()
    expect(rows[0]).to_contain_text(
        "BTC:DAI_2023" + "5" + "-5" + "Limit" + "Filled" + "95.00" + "GTC"
    )
    expect(rows[1]).to_contain_text(
        "BTC:DAI_2023" + "5" + "-5" + "Limit" + "Filled" + "90.00" + "GTC"
    )
    expect(rows[2]).to_contain_text(
        "BTC:DAI_2023" + "5" + "+5" + "Limit" + "Filled" + "110.00" + "GTC"
    )

    # Rejected
    rejected_button.click()
    expect(rejected_tab.locator(row_locator)).to_contain_text(
        "BTC:DAI_2023"
        + "0"
        + "+1"
        + "Limit"
        + "Rejected: Margin check failed"
        + "10,000,000,000,000,000.00"
        + "GTC"
    )

    # All
    all_button.click()
    rows = all_tab.locator(row_locator).all()
    expect(rows[0]).to_contain_text(
        "BTC:DAI_2023" + "0" + "-1" + "Limit" + "Active" + "150.00" + "GTC"
    )
    expect(rows[1]).to_contain_text(
        "BTC:DAI_2023" + "5" + "-5" + "Limit" + "Filled" + "95.00" + "GTC"
    )
    expect(rows[2]).to_contain_text(
        "BTC:DAI_2023" + "5" + "-5" + "Limit" + "Filled" + "90.00" + "GTC"
    )
    expect(rows[3]).to_contain_text(
        "BTC:DAI_2023"
        + "0"
        + "+1"
        + "Limit"
        + "Rejected: Margin check failed"
        + "10,000,000,000,000,000.00"
        + "GTC"
    )
    expect(rows[4]).to_contain_text(
        "BTC:DAI_2023" + "0" + "+1" + "Limit" + "Active" + "50.00" + "GTC"
    )
    expect(rows[5]).to_contain_text(
        "BTC:DAI_2023" + "1" + "+5" + "Limit" + "Active" + "105.00" + "GTC"
    )
    expect(rows[6]).to_contain_text(
        "BTC:DAI_2023" + "5" + "+5" + "Limit" + "Filled" + "110.00" + "GTC"
    )

    # Stop Orders
    stop_orders_button.click()
    expect(stop_orders_tab).to_be_visible()
    expect(stop_orders_tab.locator(row_locator)).to_be_visible(visible=False)

    # Fills
    fills_button.click()
    rows = fills_tab.locator(row_locator).all()
    expect(rows[0]).to_contain_text(
        "BTC:DAI_2023"
        + "-5"
        + "106.50 tDAI"
        + "532.50 tDAI"
        + "Taker"
        + "53.51625 tDAI"
    )
    expect(rows[1]).to_contain_text(
        "BTC:DAI_2023" + "+1" + "105.00 tDAI" + "105.00 tDAI" + "-" + "0.00 tDAI"
    )
    expect(rows[2]).to_contain_text(
        "BTC:DAI_2023" + "+5" + "105.00 tDAI" + "525.00 tDAI" + "-" + "0.00 tDAI"
    )

    # Collateral
    collateral_button.click()
    expect(collateral_tab.locator(".ag-floating-top-viewport .ag-row")).to_contain_text(
        "tDAI" + "43.94338" + "0.00%" + "999,904.04037" + "999,947.98375"
    )
