from playwright.sync_api import Page, expect
import re

from typing import List

def wait_for_toast_confirmation(page: Page, timeout: int = 30000):
    page.wait_for_function("""
    document.querySelector('[data-testid="toast-content"]') && 
    document.querySelector('[data-testid="toast-content"]').innerText.includes('AWAITING CONFIRMATION')
    """, timeout=timeout)

def verify_row(page: Page, expected_values: dict, grid_id: str = None, row_index: int = 2):
    # Click the specified grid only if grid_id is provided
    if grid_id is not None:
        page.get_by_test_id(grid_id).click()
    
    row_locator = f'[role="row"][aria-rowindex="{row_index}"]'
    page.wait_for_selector(row_locator)
    row_element = page.locator(row_locator)
    
    for index, (col_id, expected_value) in enumerate(expected_values.items(), start=1):
        aria_colindex = str(index) 
        cell_locator = f'[role="gridcell"][col-id="{col_id}"][aria-colindex="{aria_colindex}"]'
        
        cell_element = row_element.locator(cell_locator)
        
        # Assertion to ensure cell is displayed
        assert cell_element.is_visible(), f"Cell with col-id {col_id} is not displayed"
        
        # Assertion to ensure cell text is not empty
        assert cell_element.text_content(), f"Cell with col-id {col_id} is empty"
        
        # Check if the cell text contains the expected value
        expect(cell_element).to_contain_text(expected_value), f"Expected cell element: {cell_locator} to contain value :{expected_value}"

import re
from playwright.sync_api import expect
from typing import List

def verify_trades_grid(page: Page, content: List[List[float]]):
    page.get_by_test_id("Trades").click()
    first_treegrid = page.locator('[role="treegrid"]').first
    rows = first_treegrid.locator('[role="row"]').all()

    for row_index, content_row in enumerate(content):
        # Skip the first row in the UI
        cells = rows[row_index + 1].locator("button").all()

        if len(cells) < len(content_row):
            raise Exception(f"Number of cells in UI row {row_index + 1} ({len(cells)}) is less than expected ({len(content_row)})")

        for cell_index, content_cell in enumerate(content_row):
            cell_value = float(cells[cell_index].text_content())
            assert cell_value == content_cell  # Using Python's built-in assert

        # Check for the existence of the third item (the date)
        if len(cells) < 3:
            raise Exception(f"Third item (date) missing in row {row_index + 1}")

        # Check if the third item matches the regex pattern for time
        third_item_text = cells[2].text_content()
        time_pattern = r"\d{2}:\d{2}:\d{2}"
        assert re.match(time_pattern, third_item_text) is not None  # Using Python's built-in assert


def verify_orderbook_grid(page: Page, content: List[List[float]], last_trade_price: str = None):
    rows = page.locator("[data-testid$=-rows-container]").all()
    for row_index, content_row in enumerate(content):
        cells = rows[row_index].locator("button").all()
        for cell_index, content_cell in enumerate(content_row):
            assert float(cells[cell_index].text_content()) == content_cell
    expect(page.locator('[title="Last traded price"]')).to_contain_text(last_trade_price)
    

def wait_for_graphql_response(page, query_name, timeout=5000):
    response_data = {}

    def handle_response(route, request):
        if "graphql" in request.url:
            response = request.response()
            if response is not None:
                json_response = response.json()
                if json_response and "data" in json_response:
                    data = json_response["data"]
                    if query_name in data:
                        response_data["data"] = data
                        route.continue_()
                        return
        route.continue_()

    # Register the route handler
    page.route("**", handle_response)

    # Wait for the response data to be populated
    page.wait_for_timeout(timeout)

    # Unregister the route handler
    page.unroute("**", handle_response)
