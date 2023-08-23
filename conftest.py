import docker
import pytest
import os
import json
import requests
import time

from contextlib import contextmanager
from vega_sim.null_service import VegaServiceNull
from playwright.sync_api import Browser, Page
from config import container_name
from fixtures.market import (
    setup_simple_market,
    setup_opening_auction_market,
    setup_continuous_market,
)

docker_client = docker.from_env()


# Start VegaServiceNull and start up docker container for website
@contextmanager
def init_vega():
    print("\nStarting VegaServiceNull")
    with VegaServiceNull(
        run_with_console=False,
        launch_graphql=False,
        retain_log_files=True,
        use_full_vega_wallet=True,
        store_transactions=True,
        transactions_per_block=1000,
    ) as vega:
        try:
            container = docker_client.containers.run(
                container_name, detach=True, ports={"80/tcp": vega.console_port}
            )
            # docker setup
            print(f"Container {container.id} started")
            yield vega
        except docker.errors.APIError as e:
            print(f"Container {container.id} failed")
            print(e)
            raise e
        finally:
            print(f"Stopping container {container.id}")
            container.stop()


@contextmanager
def init_page(vega: VegaServiceNull, browser: Browser, request: pytest.FixtureRequest):
    with browser.new_context(
        viewport={"width": 1920, "height": 1080},
        base_url=f"http://localhost:{vega.console_port}",
    ) as context:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        with context.new_page() as page:
            try:
                # Wait for the console to be up and running before any tests are run
                attempts = 0
                while attempts < 100:
                    try:
                        code = requests.get(
                            f"http://localhost:{vega.console_port}/"
                        ).status_code
                        if code == 200:
                            break
                    except requests.exceptions.ConnectionError as e:
                        attempts += 1
                        if attempts < 100:
                            time.sleep(0.1)
                            continue
                        else:
                            raise e

                # Set window._env_ so built docker image data uses datanode from vega market sim
                env = json.dumps(
                    {
                        "VEGA_URL": f"http://localhost:{vega.data_node_rest_port}/graphql",
                        "VEGA_WALLET_URL": f"http://localhost:{vega.wallet_port}",
                    }
                )
                window_env = f"window._env_ = Object.assign({{}}, window._env_, {env})"
                page.add_init_script(script=window_env)
                yield page
            finally:
                trace_path = os.path.join("traces", request.node.name + "trace.zip")
                context.tracing.stop(path=trace_path)


# default vega & page fixtures with function scope (refreshed at each test) that can be used in tests
# separate fixtures may be defined in tests if we prefere different scope
@pytest.fixture
def vega():
    with init_vega() as vega:
        yield vega


@pytest.fixture
def page(vega, browser, request):
    with init_page(vega, browser, request) as page:
        yield page


# Set auth token so eager connection for MarketSim wallet is successful
@pytest.fixture(scope="function")
def auth(vega: VegaServiceNull, page: Page):
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
    page.add_init_script(script)

    return {
        "wallet": DEFAULT_WALLET_NAME,
        "wallet_api_token": wallet_api_token,
        "public_key": keypairs["Key 1"],
    }


# Set 'risk accepted' flag, so that the risk dialog doesn't show up
@pytest.fixture(scope="function")
def risk_accepted(page: Page):
    script = "localStorage.setItem('vega_risk_accepted', 'true'); localStorage.setItem('vega_onboarding_viewed', 'true');"
    page.add_init_script(script)


@pytest.fixture(scope="function")
def simple_market(vega, request):
    kwargs = {}
    if hasattr(request, "param"):
        kwargs.update(request.param)
    return setup_simple_market(vega, **kwargs)


@pytest.fixture(scope="function")
def opening_auction_market(vega):
    return setup_opening_auction_market(vega)


@pytest.fixture(scope="function")
def continuous_market(vega):
    return setup_continuous_market(vega)


@pytest.fixture(scope="function")
def proposed_market(vega):
    return setup_simple_market(vega, approve_proposal=False)
