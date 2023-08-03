from typing import List, Tuple
from vega_sim.service import VegaService


def submit_order(
    vega: VegaService,
    wallet_name: str,
    market_id: str,
    side: str,
    volume: float,
    price: float,
):
    return vega.submit_order(
        trading_key=wallet_name,
        market_id=market_id,
        time_in_force="TIME_IN_FORCE_GTC",
        order_type="TYPE_LIMIT",
        side=side,
        volume=volume,
        price=price,
    )


def submit_multiple_orders(
    vega: VegaService,
    wallet_name: str,
    market_id: str,
    side: str,
    volume_price_pair: List[Tuple[float, float]],
):
    for volume, price in volume_price_pair:
        submit_order(vega, wallet_name, market_id, side, volume, price)


def submit_liquidity(vega: VegaService, wallet_name: str, market_id: str):
    vega.submit_simple_liquidity(
        key_name=wallet_name,
        market_id=market_id,
        commitment_amount=10000,
        fee=0.000,
        reference_buy="PEGGED_REFERENCE_MID",
        reference_sell="PEGGED_REFERENCE_MID",
        delta_buy=1,
        delta_sell=1,
        is_amendment=False,
    )