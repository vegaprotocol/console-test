import pytest
from playwright.sync_api import expect, Page

skip_reason = "Skipping until we fix waiting for trading page to load"


@pytest.mark.skip(reason=skip_reason)
@pytest.mark.usefixtures("risk_accepted")
def test_share_usage_data(page: Page):
    page.goto("/#/settings")
    telemetry_checkbox = page.locator("#telemetry-approval")
    expect(telemetry_checkbox).to_have_attribute("data-state", "unchecked")

    page.click('[for="telemetry-approval"]')
    expect(telemetry_checkbox).to_have_attribute("data-state", "checked")
    page.reload()
    # Re-select the element after reloading the page
    telemetry_checkbox = page.locator("#telemetry-approval")
    expect(telemetry_checkbox).to_have_attribute("data-state", "checked")

    page.click('[for="telemetry-approval"]')
    expect(telemetry_checkbox).to_have_attribute("data-state", "unchecked")
    page.reload()

    # Re-select the element after reloading the page
    telemetry_checkbox = page.locator("#telemetry-approval")
    expect(telemetry_checkbox).to_have_attribute("data-state", "unchecked")


# Define a mapping of icon selectors to toast selectors
ICON_TO_TOAST = {
    'aria-label="arrow-top-left icon"': 'class="group absolute z-20 top-0 left-0 p-[8px_16px_16px_16px] max-w-full max-h-full overflow-x-hidden overflow-y-auto"',
    'aria-label="arrow-up icon"': 'class="group absolute z-20 top-0 left-[50%] translate-x-[-50%] p-[8px_16px_16px_16px] max-w-full max-h-full overflow-x-hidden overflow-y-auto"',
    'aria-label="arrow-top-right icon"': 'class="group absolute z-20 top-0 right-0 p-[8px_16px_16px_16px] max-w-full max-h-full overflow-x-hidden overflow-y-auto"',
    'aria-label="arrow-bottom-left icon"': 'class="group absolute z-20 bottom-0 left-0 p-[8px_16px_16px_16px] max-w-full max-h-full overflow-x-hidden overflow-y-auto"',
    'aria-label="arrow-down icon"': 'class="group absolute z-20 bottom-0 left-[50%] translate-x-[-50%] p-[8px_16px_16px_16px] max-w-full max-h-full overflow-x-hidden overflow-y-auto"',
    'aria-label="arrow-bottom-right icon"': 'class="group absolute z-20 bottom-0 right-0 p-[8px_16px_16px_16px] max-w-full max-h-full overflow-x-hidden overflow-y-auto"',
}


@pytest.mark.skip(reason=skip_reason)
@pytest.mark.usefixtures("risk_accepted")
def test_toast_positions(page: Page):
    page.goto("/#/settings")
    for icon_selector, toast_selector in ICON_TO_TOAST.items():
        # Click the icon
        page.click(f"[{icon_selector}]")
        # Expect that the toast is displayed
        expect(page.locator(f"[{toast_selector}]")).to_be_visible()


@pytest.mark.skip(reason=skip_reason)
@pytest.mark.usefixtures("risk_accepted")
def test_dark_mode(page: Page):
    page.goto("/#/settings")
    assert page.query_selector("html").get_attribute("class") == None
    page.get_by_role("switch").click()
    assert page.query_selector("html").get_attribute("class") == "dark"
