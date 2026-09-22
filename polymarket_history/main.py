from __future__ import annotations

import typer
from polymarket_history.application.check_erc20_window import CheckErc20Window
from polymarket_history.application.check_erc1155_window import CheckErc1155Window
from polymarket_history.application.get_erc20_balance import GetErc20Balance
from polymarket_history.application.get_erc1155_balance import GetErc1155Balance
from polymarket_history.application.get_wallet_ctf_history import GetWalletCtfHistory
from polymarket_history.application.get_wallet_usdc_history import GetWalletUsdcHistory
from polymarket_history.application.persisting_get_wallet_ctf_history import (
    PersistingGetWalletCtfHistory,
)
from polymarket_history.application.persisting_get_wallet_usdc_history import (
    PersistingGetWalletUsdcHistory,
)
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.token import Token
from polymarket_history.infrastructure.repositories.erc20_transfer_rpc import (
    Erc20TransferRpcRepository,
)
from polymarket_history.infrastructure.repositories.erc1155_transfer_rpc import (
    Erc1155TransferRpcRepository,
)
from polymarket_history.infrastructure.repositories.polygon_rpc import (
    PolygonRpcRepository,
)
from polymarket_history.infrastructure.repositories.transfer_store_factory import (
    build_transfer_store,
)
from polymarket_history.infrastructure.settings import Settings
from polymarket_history.presentation.cli import build_cli
from polymarket_history.presentation.usdc_displayer import UsdcDisplayer


def build_app() -> typer.Typer:
    settings = Settings.from_toml()
    polygon = PolygonRpcRepository(settings.rpc)
    store = build_transfer_store(settings.database.dsn)
    get_erc20_balance = GetErc20Balance(polygon)
    get_wallet_usdc_history = PersistingGetWalletUsdcHistory(
        GetWalletUsdcHistory(Erc20TransferRpcRepository(polygon)),
        store,
    )
    check_erc20_window = CheckErc20Window(
        get_erc20_balance,
        get_wallet_usdc_history,
    )
    get_erc1155_balance = GetErc1155Balance(polygon)
    get_wallet_ctf_history = PersistingGetWalletCtfHistory(
        GetWalletCtfHistory(Erc1155TransferRpcRepository(polygon)),
        store,
    )
    check_erc1155_window = CheckErc1155Window(polygon, get_wallet_ctf_history)
    usdc_displayer = UsdcDisplayer(Token(Address(settings.contracts.usdc_e)))
    return build_cli(
        get_erc20_balance,
        get_wallet_usdc_history,
        check_erc20_window,
        get_erc1155_balance,
        get_wallet_ctf_history,
        check_erc1155_window,
        usdc_displayer,
        default_wallet=settings.wallet.address,
        default_token=settings.contracts.usdc_e,
        default_ctf=settings.contracts.ctf,
    )


def main() -> None:
    build_app()()


if __name__ == "__main__":
    main()
