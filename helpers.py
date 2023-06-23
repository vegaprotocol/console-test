import docker
from config import container_name
import socket
from contextlib import closing
from typing import Optional, Set


docker_client = docker.from_env()
container = None

def setup(page, port):
    global container
    console_port = find_free_port()
    print("console_port", console_port)
    container = docker_client.containers.run(container_name, detach=True, ports={'80/tcp': console_port})
    print(f'Container {container.id} started')

    # Set VEGA_URL using window._env_. Double curly braces are used to escape so the js is valid
    window_env = f"window._env_ = Object.assign({{}}, window._env_, {{ VEGA_URL: 'http://localhost:{port}/graphql' }})"
    page.add_init_script(
        script=window_env
    )
    return console_port

def teardown():
    global container
    try:
        container.stop()
        print(f"Container '{container_name}' stopped successfully.")
    except docker.errors.NotFound:
        print(f"Container '{container_name}' not found.")
    except docker.errors.APIError as e:
        print(f"An error occurred while stopping the container: {e}")


def find_free_port(existing_set: Optional[Set[int]] = None):
    ret_sock = 0
    existing_set = (
        existing_set.union(set([ret_sock]))
        if existing_set is not None
        else set([ret_sock])
    )

    num_tries = 0
    while ret_sock in existing_set:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ret_sock = s.getsockname()[1]

        num_tries += 1
        if num_tries >= 100:
            # Arbitrary high number. If we try 100 times and fail to find
            # a port it seems reasonable to give up
            raise SocketNotFoundError("Failed finding a free socket")

    return ret_sock

class SocketNotFoundError(Exception):
    pass