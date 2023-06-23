import pytest
import docker
import helpers
from config import container_name

# docker_client = docker.from_env()

# @pytest.fixture(scope="session", autouse=True)
# def global_setup():

#     console_port = helpers.port_getter(True)

#     # Start website from docker
#     container = docker_client.containers.run(container_name, detach=True, ports={'80/tcp': console_port})
#     print(f'Container {container.id} started')

#     yield

#     try:
#         container.stop()
#         print(f"Container '{container_name}' stopped successfully.")
#     except docker.errors.NotFound:
#         print(f"Container '{container_name}' not found.")
#     except docker.errors.APIError as e:
#         print(f"An error occurred while stopping the container: {e}")