from __future__ import annotations

import typer
from polymarket_history.application.get_erc20_balance import GetErc20Balance
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import LATEST, BlockNumber
from polymarket_history.presentation.usdc_displayer import UsdcDisplayer


def build_cli(
    get_erc20_balance: GetErc20Balance,
    usdc_displayer: UsdcDisplayer,
    *,
    default_wallet: str,
    default_token: str,
) -> typer.Typer:
    app = typer.Typer(add_completion=False, no_args_is_help=False)

    @app.callback(invoke_without_command=True)
    def balance(
        wallet: str = typer.Option(default_wallet, "--wallet"),
        token: str = typer.Option(default_token, "--token"),
        block: str = typer.Option("latest", "--block"),
    ) -> None:
        block_ref = LATEST if block == "latest" else BlockNumber(int(block, 0))
        result = get_erc20_balance(Address(token), Address(wallet), block=block_ref)
        typer.echo(f"wallet={wallet}")
        typer.echo(f"token={result.token}")
        typer.echo(f"block={result.block.value}")
        typer.echo(f"balance_raw={result.balance}")
        formatted = usdc_displayer.format(result.token, result.balance)
        if formatted is not None:
            typer.echo(f"balance_usdc={formatted}")

    return app
