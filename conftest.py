import docker
import pytest
import os

from vega_sim.null_service import VegaServiceNull
from playwright.sync_api import Browser, BrowserContext, Page
from config import container_name

docker_client = docker.from_env()

# Capture traces on tests
@pytest.fixture(scope="function", autouse=True)
def page_with_trace(request, browser):
    with browser.new_context() as context:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        with context.new_page() as page:
            yield page
        trace_path = os.path.join("traces", request.node.name + "trace.zip")
        if request.node.rep_call.failed:
            context.tracing.stop(path=trace_path)
        else:
            context.tracing.stop(path=trace_path)

# Start VegaServiceNull and start up docker container for website
@pytest.fixture(scope="function", autouse=True)
def vega():
    print("\nStarting VegaServiceNull")
    with VegaServiceNull(
        run_with_console=False,
        launch_graphql=False,
        retain_log_files=True,
        use_full_vega_wallet=True,
        store_transactions=True,
    ) as vega:

        # docker setup
        container = docker_client.containers.run(container_name, detach=True, ports={'80/tcp': vega.console_port})
        print(f'Container {container.id} started')

        yield vega

        try:
            container.stop()
            print(f"Container '{container_name}' stopped successfully.")
        except docker.errors.NotFound:
            print(f"Container '{container_name}' not found.")
        except docker.errors.APIError as e:
            print(f"An error occurred while stopping the container: {e}")
            
# Setup window._env_ variables. Note: This is named `page` so that the `page` argument
# tests can be used normally.
@pytest.fixture(scope="function", autouse=True)
def page(vega, page_with_trace):
    # Set window._env_ so built docker image data uses datanode from vega market sim
    window_env = f"window._env_ = Object.assign({{}}, window._env_, {{ VEGA_URL: 'http://localhost:{vega.data_node_rest_port}/graphql' }})"
    page_with_trace.add_init_script(
        script=window_env
    )

    # Just pass on the main page object
    return page_with_trace


