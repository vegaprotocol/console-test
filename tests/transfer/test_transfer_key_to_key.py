import pytest 
import re
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from actions.utils import wait_for_toast_confirmation
from conftest import init_vega
from fixtures.market import setup_continuous_market

@pytest.fixture(scope="module")
def vega(request):
    with init_vega(request) as vega:
        yield vega


@pytest.fixture(scope="module")
def continuous_market(vega):
    return setup_continuous_market(vega)


@pytest.mark.usefixtures("page", "auth", "risk_accepted",)
def test_transfer_fees(continuous_market, page: Page):
    # 1003-TRAN-020
    # 1003-TRAN-021
    # 1003-TRAN-022
    # 1003-TRAN-023

    page.goto('/#/portfolio')
    page.select_option('[data-testid=transfer-form] [name="toAddress"]', index=1)
    page.get_by_test_id('select-asset').click()
    page.get_by_test_id('rich-select-option').click()
    page.locator('[data-testid=transfer-form] input[name="amount"]').fill('1')
    expect(page.get_by_test_id('transfer-fee')).to_be_visible()
    expect(page.get_by_test_id('transfer-fee')).to_have_text("0.001")

    expect(page.get_by_test_id('transfer-amount')).to_be_visible()
    expect(page.get_by_test_id('transfer-amount')).to_have_text("1.00")

    expect(page.get_by_test_id('total-transfer-fee')).to_be_visible()
    expect(page.get_by_test_id('total-transfer-fee')).to_have_text("1.001")

    # Perform the click
    page.get_by_test_id('include-transfer-fee').click()

    # Second set of checks
    expect(page.get_by_test_id('transfer-fee')).to_be_visible()
    expect(page.get_by_test_id('transfer-fee')).to_have_text("0.001")

    expect(page.get_by_test_id('transfer-amount')).to_be_visible()
    expect(page.get_by_test_id('transfer-amount')).to_have_text("0.999")

    expect(page.get_by_test_id('total-transfer-fee')).to_be_visible()
    expect(page.get_by_test_id('total-transfer-fee')).to_have_text("1.00")

@pytest.mark.usefixtures("page", "auth", "risk_accepted",)
def test_transfer_tooltips(continuous_market, page: Page):
    # 1003-TRAN-015
    # 1003-TRAN-016
    # 1003-TRAN-017
    # 1003-TRAN-018
    # 1003-TRAN-019

    page.goto('/#/portfolio')

    # Check Include Transfer Fee tooltip
    page.locator('label[for="include-transfer-fee"] div').hover()
    expect(page.locator('[data-side="bottom"] div')).to_be_visible()
    expect(page.locator('[data-side="bottom"] div').inner_text()).not_to_be_empty()

    # Check Transfer Fee tooltip
    page.locator('div:text("Transfer fee")').hover()
    expect(page.locator('[data-side="bottom"] div')).to_be_visible()
    expect(page.locator('[data-side="bottom"] div').inner_text()).not_to_be_empty()

    # Check Amount to be transferred tooltip
    page.locator('div:text("Amount to be transferred")').hover()
    expect(page.locator('[data-side="bottom"] div')).to_be_visible()
    expect(page.locator('[data-side="bottom"] div').inner_text()).not_to_be_empty()

    # Check Total amount (with fee) tooltip
    page.locator('div:text("Total amount (with fee)")').hover()
    expect(page.locator('[data-side="bottom"] div')).to_be_visible()
    expect(page.locator('[data-side="bottom"] div').inner_text()).not_to_be_empty()

@pytest.mark.usefixtures("page", "auth", "risk_accepted",)
def test_transfer_key_to_key(continuous_market, vega: VegaService, page: Page):
    # 1003-TRAN-001
    # 1003-TRAN-006
    # 1003-TRAN-007
    # 1003-TRAN-008
    # 1003-TRAN-009
    # 1003-TRAN-010
    # 1003-TRAN-023
    page.goto('/#/portfolio')
    
    expect(page.get_by_test_id('transfer-form')).to_be_visible
    page.select_option('[data-testid=transfer-form] [name="toAddress"]', index=1)
    
    page.get_by_test_id('select-asset').click()
    expect(page.get_by_test_id('rich-select-option')).to_have_count(1)
    
    page.get_by_test_id('rich-select-option').click()
    expected_asset_text = re.compile(r"tDAI tDAI999,991.49731 tDAI.{6}….{4}")
    actual_asset_text = page.get_by_test_id('select-asset').text_content().strip()
   
    assert expected_asset_text.search(actual_asset_text), f"Expected pattern not found in {actual_asset_text}"
    
    page.locator('[data-testid=transfer-form] input[name="amount"]').fill('1')
    expect(page.locator('[data-testid=transfer-form] input[name="amount"]')).not_to_be_empty()
    
    page.pause()
    page.locator('[data-testid=transfer-form] [type="submit"]').click()
    wait_for_toast_confirmation(page)
    page.pause()
    vega.forward("10s")
    vega.wait_fn(10)
    vega.wait_for_total_catchup()
    page.pause()
    expected_confirmation_text = re.compile(r"Awaiting confirmationPlease wait for your transaction to be confirmedView in block explorerTransferTo .{6}….{4}1\.00 tDAI")
    actual_confirmation_text = page.get_by_test_id('toast-content').text_content()
    print(f"Actual text is: {actual_confirmation_text}")
    assert expected_confirmation_text.search(actual_confirmation_text), f"Expected pattern not found in {actual_confirmation_text}"
    