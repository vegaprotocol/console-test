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