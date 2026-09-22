from __future__ import annotations

import json
from typing import Any

import typer
from polymarket_history.application.check_erc20_window import CheckErc20Window
from polymarket_history.application.check_erc1155_window import CheckErc1155Window
from polymarket_history.application.get_erc20_balance import GetErc20Balance
from polymarket_history.application.get_erc1155_balance import GetErc1155Balance
from polymarket_history.application.get_wallet_ctf_history import GetWalletCtfHistory
from polymarket_history.application.get_wallet_usdc_history import GetWalletUsdcHistory
from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import LATEST, BlockNumber
from polymarket_history.presentation.usdc_displayer import UsdcDisplayer


def build_cli(
    get_erc20_balance: GetErc20Balance,
    get_wallet_usdc_history: GetWalletUsdcHistory,
    check_erc20_window: CheckErc20Window,
    get_erc1155_balance: GetErc1155Balance,
    get_wallet_ctf_history: GetWalletCtfHistory,
    check_erc1155_window: CheckErc1155Window,
    usdc_displayer: UsdcDisplayer,
    *,
    default_wallet: str,
    default_token: str,
    default_ctf: str,
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
        payload = [
            _serialize_erc20_transfer(item, usdc_displayer) for item in transfers
        ]
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

    @app.command("ctf-balance")
    def ctf_balance(
        token_id: str = typer.Option(..., "--token-id"),
        wallet: str = typer.Option(default_wallet, "--wallet"),
        contract: str = typer.Option(default_ctf, "--contract"),
        block: str = typer.Option("latest", "--block"),
    ) -> None:
        block_ref = LATEST if block == "latest" else BlockNumber(int(block, 0))
        parsed_token_id = int(token_id, 0)
        result = get_erc1155_balance(
            Address(contract),
            Address(wallet),
            parsed_token_id,
            block=block_ref,
        )
        typer.echo(f"wallet={wallet}")
        typer.echo(f"contract={result.token}")
        typer.echo(f"token_id={result.token_id}")
        typer.echo(f"block={result.block.value}")
        typer.echo(f"balance={result.balance}")

    @app.command("ctf-history")
    def ctf_history(
        from_block: int = typer.Option(..., "--from-block"),
        to_block: int = typer.Option(..., "--to-block"),
        wallet: str = typer.Option(default_wallet, "--wallet"),
        contract: str = typer.Option(default_ctf, "--contract"),
        batch_size: int = typer.Option(1000, "--batch-size"),
    ) -> None:
        transfers = get_wallet_ctf_history(
            Address(wallet),
            Address(contract),
            BlockNumber(from_block),
            BlockNumber(to_block),
            batch_size,
        )
        payload = [_serialize_erc1155_transfer(item) for item in transfers]
        typer.echo(json.dumps(payload, ensure_ascii=False))

    @app.command("ctf-check")
    def ctf_check(
        from_block: int = typer.Option(..., "--from-block"),
        to_block: int = typer.Option(..., "--to-block"),
        wallet: str = typer.Option(default_wallet, "--wallet"),
        contract: str = typer.Option(default_ctf, "--contract"),
        batch_size: int = typer.Option(1000, "--batch-size"),
    ) -> None:
        result = check_erc1155_window(
            Address(wallet),
            Address(contract),
            BlockNumber(from_block),
            BlockNumber(to_block),
            batch_size,
        )
        typer.echo(f"wallet={result.wallet}")
        typer.echo(f"contract={result.token}")
        typer.echo(f"from_block={result.from_block.value}")
        typer.echo(f"to_block={result.to_block.value}")
        typer.echo(f"transfers={result.transfer_count}")
        typer.echo(f"positions={len(result.positions)}")
        typer.echo(f"matched={result.matched}")
        for position in result.positions:
            typer.echo(
                "position "
                f"token_id={position.token_id} "
                f"transfers={position.transfer_count} "
                f"opening={position.opening_balance} "
                f"reconstructed={position.reconstructed_balance} "
                f"closing={position.closing_balance} "
                f"delta={position.delta} "
                f"matched={position.matched}"
            )
        if not result.matched:
            raise typer.Exit(code=1)

    return app


def _serialize_erc20_transfer(
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


def _serialize_erc1155_transfer(transfer: Erc1155Transfer) -> dict[str, Any]:
    return {
        "contract": str(transfer.token),
        "token_id": transfer.token_id,
        "block": transfer.block.value,
        "transaction_hash": transfer.transaction_hash,
        "log_index": transfer.log_index,
        "operator": str(transfer.operator),
        "from": str(transfer.sender),
        "to": str(transfer.recipient),
        "amount": transfer.amount,
    }
