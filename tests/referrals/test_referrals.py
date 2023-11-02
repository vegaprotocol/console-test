import pytest
import requests
from playwright.sync_api import Page, expect
from vega_sim.service import VegaService
from conftest import init_vega
from fixtures.market import setup_continuous_market
from actions.utils import WalletConfig, create_and_faucet_wallet

PARTY_A = WalletConfig("party_a", "party_a")
PARTY_B = WalletConfig("party_b", "party_b")

@pytest.fixture(scope="module")
def vega(request):
    with init_vega(request) as vega:
        yield vega


@pytest.fixture(scope="module")
def continuous_market(vega):
    return setup_continuous_market(vega)


@pytest.mark.usefixtures("page", "auth", "risk_accepted")
def test_referral(continuous_market, vega: VegaService, page: Page):
    page.goto(f"/#/markets/{continuous_market}")
    
    create_and_faucet_wallet(vega=vega, wallet=PARTY_A)
    vega.wait_for_total_catchup()
    create_and_faucet_wallet(vega=vega, wallet=PARTY_B)
    vega.wait_for_total_catchup()

    vega.create_referral_set(key_name=PARTY_A.name)
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.pause()
    print(vega.list_referral_sets())
    page.pause()
    referral_set_id = list(vega.list_referral_sets().keys())[0]
    print(referral_set_id)
    page.pause()
    try:
        vega.apply_referral_code(key_name=PARTY_B.name, id=referral_set_id)
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error occurred: {err}")
        print(f"Full response: {err.response.text}") # Printing full response for detailed error
        raise
    page.pause()
    vega.wait_fn(1)
    vega.wait_for_total_catchup()
    page.pause()
    expect(page)
