import pytest
import docker
from playwright.sync_api import Page
from config import container_name, datanode_port, console_port

docker_client = docker.from_env()

@pytest.fixture(scope="session", autouse=True)
def global_setup():
    # Start website from docker
    container = docker_client.containers.run(container_name, detach=True, ports={'80/tcp': console_port})
    print(f'Container {container.id} started')

    yield

    try:
        container.stop()
        print(f"Container '{container_name}' stopped successfully.")
    except docker.errors.NotFound:
        print(f"Container '{container_name}' not found.")
    except docker.errors.APIError as e:
        print(f"An error occurred while stopping the container: {e}")

@pytest.fixture(scope="function", autouse=True)
def before_all(page: Page):
    print("beforeEach")

    # Set VEGA_URL using window._env_. Double curly braces are used to escape so the js is valid
    window_env = f"window._env_ = Object.assign({{}}, window._env_, {{ VEGA_URL: 'http://localhost:{datanode_port}/graphql' }})"
    page.add_init_script(
        script=window_env
    )

    yield
    print("afterEach")
