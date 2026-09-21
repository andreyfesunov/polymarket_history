from __future__ import annotations

import json
from typing import Any

import typer
from polymarket_history.application.check_erc20_window import CheckErc20Window
from polymarket_history.application.get_erc20_balance import GetErc20Balance
from polymarket_history.application.get_wallet_usdc_history import GetWalletUsdcHistory
from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import LATEST, BlockNumber
from polymarket_history.presentation.usdc_displayer import UsdcDisplayer


def build_cli(
    get_erc20_balance: GetErc20Balance,
    get_wallet_usdc_history: GetWalletUsdcHistory,
    check_erc20_window: CheckErc20Window,
    usdc_displayer: UsdcDisplayer,
    *,
    default_wallet: str,
    default_token: str,
) -> typer.Typer:
    app = typer.Typer(add_completion=False, no_args_is_help=True)

    @app.callback()
    def _root() -> None:
        pass

    @app.command("balance")
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

    @app.command("history")
    def history(
        from_block: int = typer.Option(..., "--from-block"),
        to_block: int = typer.Option(..., "--to-block"),
        wallet: str = typer.Option(default_wallet, "--wallet"),
        token: str = typer.Option(default_token, "--token"),
        batch_size: int = typer.Option(1000, "--batch-size"),
    ) -> None:
        transfers = get_wallet_usdc_history(
            Address(wallet),
            Address(token),
            BlockNumber(from_block),
            BlockNumber(to_block),
            batch_size,
        )
        payload = [_serialize_transfer(item, usdc_displayer) for item in transfers]
        typer.echo(json.dumps(payload, ensure_ascii=False))

    @app.command("check")
    def check(
        from_block: int = typer.Option(..., "--from-block"),
        to_block: int = typer.Option(..., "--to-block"),
        wallet: str = typer.Option(default_wallet, "--wallet"),
        token: str = typer.Option(default_token, "--token"),
        batch_size: int = typer.Option(1000, "--batch-size"),
    ) -> None:
        result = check_erc20_window(
            Address(wallet),
            Address(token),
            BlockNumber(from_block),
            BlockNumber(to_block),
            batch_size,
        )
        typer.echo(f"wallet={result.wallet}")
        typer.echo(f"token={result.token}")
        typer.echo(f"from_block={result.from_block.value}")
        typer.echo(f"to_block={result.to_block.value}")
        typer.echo(f"transfers={result.transfer_count}")
        typer.echo(f"opening_balance={result.opening_balance}")
        typer.echo(f"reconstructed_balance={result.reconstructed_balance}")
        typer.echo(f"closing_balance={result.closing_balance}")
        typer.echo(f"delta={result.delta}")
        typer.echo(f"matched={result.matched}")
        if not result.matched:
            raise typer.Exit(code=1)

    return app


def _serialize_transfer(
    transfer: Erc20Transfer,
    usdc_displayer: UsdcDisplayer,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "token": str(transfer.token),
        "block": transfer.block.value,
        "transaction_hash": transfer.transaction_hash,
        "log_index": transfer.log_index,
        "from": str(transfer.sender),
        "to": str(transfer.recipient),
        "amount": transfer.amount,
    }
    formatted = usdc_displayer.format(transfer.token, transfer.amount)
    if formatted is not None:
        row["amount_usdc"] = formatted
    return row
