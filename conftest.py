import pytest
import os

from playwright.sync_api import Browser, BrowserContext, Page

@pytest.fixture(scope="function", autouse=True)
def page(request, browser):
    with browser.new_context() as context:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        with context.new_page() as page:
            yield page
        trace_path = os.path.join("traces", request.node.name + "trace.zip")
        if request.node.rep_call.failed:
            context.tracing.stop(path=trace_path)
        else:
        
            context.tracing.stop(path=trace_path)