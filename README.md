# Console-Test

`console-test` is a repository containing end-to-end tests for a console application using vega-market-sim. This README will guide you through setting up your environment and running the tests.

## Prerequisites

- [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
- [Docker](https://www.docker.com/)

## Getting Started

1. **Install Poetry**: Follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installing-with-the-official-installer).
1. **Install Docker**: Follow the instructions on the [offical Docker website](https://docs.docker.com/desktop/).
1. **Set up a Poetry environment**:
    ```bash
    poetry shell
    ```
1. **Install the necessary dependencies**:
    ```bash
    poetry install
    ```
1. **Download the necessary binaries: Run the following command within your Python environment (use force so that the binaries are overwritten):
    ```bash
    python -m vega_sim.tools.load_binaries --force
    ```
1. **Pull the docker image of the trading app**:
   You can pull the image you want to test, for example:
    ```bash
    docker pull vegaprotocol/trading:testnet
    ```
   All available images can be found [here](https://hub.docker.com/r/vegaprotocol/trading/tags).
1. **Start Docker**: Make sure your Docker daemon is running.
1. **Run the tests**: You can run tests with:
    ```bash
    poetry run pytest -s --headed
    ```

## Running Specific Tests

To run a specific test, use the `-k` option followed by the name of the test:
```bash
poetry run pytest -k "order_match" -s
```


## Running Tests in Parallel

If you want to run tests in parallel, use the --numprocesses auto option:
```bash
poetry run pytest -s --headed --numprocesses auto
```
