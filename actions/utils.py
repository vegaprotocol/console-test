from collections import namedtuple

from playwright.sync_api import Page
from vega_sim.null_service import VegaServiceNull
from typing import Optional

WalletConfig = namedtuple("WalletConfig", ["name", "passphrase"])
ASSET_NAME = "tDAI"

def wait_for_toast_confirmation(page: Page, timeout: int = 30000):
    page.wait_for_function("""
    document.querySelector('[data-testid="toast-content"]') && 
    document.querySelector('[data-testid="toast-content"]').innerText.includes('AWAITING CONFIRMATION')
    """, timeout=timeout)

def create_and_faucet_wallet(
    vega: VegaServiceNull,
    wallet: WalletConfig,
    symbol: Optional[str] = None,
    amount: float = 1e4,
):
    asset_id = vega.find_asset_id(symbol=symbol if symbol is not None else ASSET_NAME)
    vega.create_key(wallet.name)
    vega.mint(wallet.name, asset_id, amount)

def next_epoch(vega: VegaServiceNull):
    forwards = 0
    epoch_seq = vega.statistics().epoch_seq
    while epoch_seq == vega.statistics().epoch_seq:
        vega.wait_fn(1)
        forwards += 1
        if forwards > 2 * 10 * 60:
            raise Exception(
                "Epoch not started after forwarding the duration of two epochs."
            )
    vega.wait_fn(1)
    vega.wait_for_total_catchup()