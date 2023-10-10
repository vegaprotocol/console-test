import os
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.usefixtures("page", "auth", "risk_accepted", "continuous_market")
def test_ledger_entries_downloads(page: Page):
    page.goto("/#/portfolio")
    page.get_by_test_id("Ledger entries").click()
    expect(page.get_by_test_id("ledger-download-button")).to_be_enabled()

    # 7007-LEEN-001
    # Get the user's Downloads directory
    downloads_directory = os.path.expanduser("~") + "/Downloads/"
    page.pause()
    # Start waiting for the download
    with page.expect_download() as download_info:
    # Perform the action that initiates download
        page.get_by_test_id("ledger-download-button").click()
    download = download_info.value
    # Wait for the download process to complete and save the downloaded file in the Downloads directory
    download.save_as(os.path.join(downloads_directory, download.suggested_filename))

    # Verify the download by asserting that the file exists
    downloaded_file_path = os.path.join(downloads_directory, download.suggested_filename)
    assert os.path.exists(downloaded_file_path), f"Download failed! File not found at: {downloaded_file_path}"

