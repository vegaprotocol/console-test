import pytest
import logging
from collections import namedtuple
from playwright.sync_api import expect

from market_fixtures.continuous_market.continuous_market import setup_continuous_market

@pytest.mark.usefixtures("auth")
def test_see_market_depth_chart(setup_continuous_market, page):

    # Click on the 'Depth' tab
    page.get_by_test_id('Depth').click()

    # Check if the 'Depth' tab and the depth chart are visible
    # 6006-DEPC-001
    expect(page.get_by_test_id('tab-depth')).to_be_visible()
    expect(page.locator('.depth-chart-module_canvas__260De').first).to_be_visible()
 