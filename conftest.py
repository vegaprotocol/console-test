import docker
import pytest
import os
import json

from vega_sim.null_service import VegaServiceNull
from playwright.sync_api import Browser, Page
from config import container_name
from fixtures.market import (
    setup_simple_market,
    setup_opening_auction_market,
    setup_continuous_market,
    setup_proposed_market,
)

docker_client = docker.from_env()


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
        transactions_per_block=1000,
    ) as vega:
        # docker setup
        container = docker_client.containers.run(
            container_name, detach=True, ports={"80/tcp": vega.console_port}
        )
        print(f"Container {container.id} started")

        yield vega

        try:
            container.stop()
            print(f"Container '{container_name}' stopped successfully.")
        except docker.errors.NotFound:
            print(f"Container '{container_name}' not found.")
        except docker.errors.APIError as e:
            print(f"An error occurred while stopping the container: {e}")

            # Capture traces on tests


@pytest.fixture(scope="function", autouse=True)
def page_with_trace(vega, request, browser: Browser):
    with browser.new_context(
        base_url=f"http://localhost:{vega.console_port}"
    ) as context:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        with context.new_page() as page:
            yield page
        trace_path = os.path.join("traces", request.node.name + "trace.zip")
        try:
            if request.node.rep_call.failed:
                context.tracing.stop(path=trace_path)
        except AttributeError:
            context.tracing.stop(path=trace_path)
        else:
            context.tracing.stop()


# Setup window._env_ variables. Note: This is named `page` so that the `page` argument
# tests can be used normally.
@pytest.fixture(scope="function", autouse=True)
def page(vega, page_with_trace: Page):
    # Set window._env_ so built docker image data uses datanode from vega market sim
    env = json.dumps(
        {
            "VEGA_URL": f"http://localhost:{vega.data_node_rest_port}/graphql",
            "VEGA_WALLET_URL": f"http://localhost:{vega.wallet_port}",
        }
    )
    window_env = f"window._env_ = Object.assign({{}}, window._env_, {env})"
    page_with_trace.add_init_script(script=window_env)

    # Just pass on the main page object
    return page_with_trace


# Set auth token so eager connection for MarketSim wallet is successful
@pytest.fixture(scope="function")
def auth(vega, page_with_trace):
    DEFAULT_WALLET_NAME = "MarketSim"  # This is the default wallet name within VegaServiceNull and CANNOT be changed

    # Calling get_keypairs will internally call _load_tokens for the given wallet
    keypairs = vega.wallet.get_keypairs(DEFAULT_WALLET_NAME)
    wallet_api_token = vega.wallet.login_tokens[DEFAULT_WALLET_NAME]

    # Set token to localStorage so eager connect hook picks it up and immediately connects
    wallet_config = json.dumps(
        {
            "token": f"VWT {wallet_api_token}",
            "connector": "jsonRpc",
            "url": f"http://localhost:{vega.wallet_port}",
        }
    )

    storage_javascript = [
        # Store wallet config so eager connection is initiated
        f"localStorage.setItem('vega_wallet_config', '{wallet_config}');",
        # Ensure wallet ris dialog doesnt show, otherwise eager connect wont work
        "localStorage.setItem('vega_wallet_risk_accepted', 'true');",
        # Ensure initial risk dialog doesnt show
        "localStorage.setItem('vega_risk_accepted', 'true');",
    ]
    script = "".join(storage_javascript)
    page_with_trace.add_init_script(script)

    return {
        "wallet": DEFAULT_WALLET_NAME,
        "wallet_api_token": wallet_api_token,
        "public_key": keypairs["Key 1"],
    }


# Set 'risk accepted' flag, so that the risk dialog doesn't show up
@pytest.fixture(scope="function")
def risk_accepted(page_with_trace):
    script = "localStorage.setItem('vega_risk_accepted', 'true');"
    page_with_trace.add_init_script(script)


@pytest.fixture(scope="function")
def simple_market(vega):
    return setup_simple_market(vega)


@pytest.fixture(scope="function")
def opening_auction_market(vega):
    return setup_opening_auction_market(vega)


@pytest.fixture(scope="function")
def continuous_market(vega):
    return setup_continuous_market(vega)


@pytest.fixture(scope="function")
def proposed_market(vega):
    return setup_proposed_market(vega)
