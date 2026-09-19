from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def find_settings_toml(name: str = "settings.toml") -> Path:
    for directory in (Path.cwd(), *Path.cwd().parents):
        candidate = directory / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{name} not found from {Path.cwd()}")


@dataclass(frozen=True, slots=True)
class RpcSettings:
    url: str


@dataclass(frozen=True, slots=True)
class WalletSettings:
    address: str


@dataclass(frozen=True, slots=True)
class ContractSettings:
    usdc_e: str
    ctf: str


@dataclass(frozen=True, slots=True)
class Settings:
    rpc: RpcSettings
    wallet: WalletSettings
    contracts: ContractSettings

    @classmethod
    def from_toml(cls, path: Path | str | None = None) -> Settings:
        config_path = Path(path) if path is not None else find_settings_toml()
        with config_path.open("rb") as file:
            data = tomllib.load(file)

        rpc = data["rpc"]
        wallet = data["wallet"]
        contracts = data["contracts"]
        return cls(
            rpc=RpcSettings(url=rpc["url"]),
            wallet=WalletSettings(address=wallet["address"]),
            contracts=ContractSettings(
                usdc_e=contracts["usdc_e"],
                ctf=contracts["ctf"],
            ),
        )


@lru_cache(maxsize=1)
def get_settings(path: str | None = None) -> Settings:
    return Settings.from_toml(path)
