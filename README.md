# console-test

End-to-end tests for console using vega-market-sim

## Get started

1. [Install poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
1. `poetry shell`
1. `poetry install`
1. Download the binaries by running `python -m vega_sim.tools.load_binaries` within your Python environment
1. Pull the docker image of the trading app you want to test with `docker pull vegaprotocol/trading:testnet`. All images can be found [here](https://hub.docker.com/r/vegaprotocol/trading/tags)
1. Run the scenario and tests with `poetry run pytest -s --headed`


To run tests in parallel `poetry run pytest -s --headed --numprocesses auto`