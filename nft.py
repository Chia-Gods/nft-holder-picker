import asyncio
import json
import sys
from typing import List, Optional, Dict

from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_record import CoinRecord
from chia_rs import Coin
from chia.util.condition_tools import conditions_dict_for_solution
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.types.blockchain_format.program import Program
from chia.types.condition_opcodes import ConditionOpcode
from chia.wallet.nft_wallet.nft_puzzles import get_metadata_and_phs
from chia.wallet.nft_wallet.uncurry_nft import UncurriedNFT
from chia.util.bech32m import encode_puzzle_hash, decode_puzzle_hash


async def get_nft_info(nft_id: str, target_height: int) -> Dict:
    nft_info = {
        "nft_id": "",
        "current_address": "",
    }

    config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
    try:
        client = await FullNodeRpcClient.create(config["self_hostname"], config["full_node"]["rpc_port"],
                                                DEFAULT_ROOT_PATH, config)
    except Exception as e:
        raise Exception(f"Failed to create RPC client: {e}")

    launcher_coin = decode_puzzle_hash(nft_id)
    current_coin = await get_last_child(client, launcher_coin, target_height)
    coin_bytes = current_coin.name

    coin_record = await client.get_coin_record_by_name(coin_bytes)
    assert coin_record is not None

    puzz_solution = await client.get_puzzle_and_solution(coin_record.coin.parent_coin_info,
                                                         coin_record.confirmed_block_index)

    puzzle: Program = Program.from_bytes(bytes(puzz_solution.puzzle_reveal))

    uncurried_nft = UncurriedNFT.uncurry(*puzzle.uncurry())
    assert uncurried_nft is not None
    nft_id = encode_puzzle_hash(uncurried_nft.singleton_launcher_id, "nft")
    nft_info["nft_id"] = nft_id

    (_, puzzlehash) = get_metadata_and_phs(uncurried_nft, puzz_solution.solution)
    current_address = encode_puzzle_hash(puzzlehash, "xch")
    nft_info["current_address"] = current_address

    client.close()
    return nft_info


# Gets the last child coin
async def get_last_child(client: FullNodeRpcClient, coin_id: bytes32, target_height: int) -> Optional[CoinRecord]:
    current_coin = await client.get_coin_record_by_name(coin_id)

    while True:
        if current_coin is None:
            return current_coin

        if current_coin.spent_block_index == 0:
            return current_coin

        if current_coin.spent_block_index > target_height:
            return current_coin

        conditions = await get_conditions_for_coin(client, current_coin)
        if conditions is None:
            return None

        if ConditionOpcode.CREATE_COIN not in conditions:
            return None

        coins = coins_from_create_coin_condition(conditions, current_coin.coin.name())
        if len(coins) > 1:
            return None

        current_coin = await client.get_coin_record_by_name(coins[0].name())
        if current_coin is None:
            return current_coin

        if current_coin.spent_block_index == 0:
            return current_coin


async def get_conditions_for_coin(client: FullNodeRpcClient, coin: CoinRecord):
    # Height for this is the height the coin was spent at
    puzz_solution = await client.get_puzzle_and_solution(coin.name, coin.spent_block_index)

    assert puzz_solution is not None

    conditions = conditions_dict_for_solution(
        puzz_solution.puzzle_reveal,
        puzz_solution.solution,
        DEFAULT_CONSTANTS.MAX_BLOCK_COST_CLVM)

    return conditions


def coins_from_create_coin_condition(conditions, parent_coin_info: bytes32) -> List[Coin]:
    output_coins: List[Coin] = []

    for create_coin in conditions.get(ConditionOpcode.CREATE_COIN, []):
        puzzle_hash = create_coin.vars[0]
        amount = int.from_bytes(create_coin.vars[1], byteorder='big')
        output_coins.append(Coin(parent_coin_info, puzzle_hash, amount))

    return output_coins
