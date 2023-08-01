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
