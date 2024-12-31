import asyncio
import json
import re
import sys

import requests
import time
from typing import Optional
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from nft import get_nft_info
from excluded_list import EXCLUDED_ADDRESSES

MINTGARDEN_API = "https://api.mintgarden.io"
RATE_LIMIT_DELAY = 1  # seconds between API calls
TOTAL_PROCESSED = 0

async def get_and_process_collection_nfts(client: FullNodeRpcClient, collection_id: str, target_height: Optional[int] = None):
    """
    Fetch and process NFTs from a collection using MintGarden API
    Args:
        client: FullNodeRpcClient
        collection_id: The collection ID from MintGarden
        target_height: Optional target block height
    """
    global TOTAL_PROCESSED

    endpoint = f"{MINTGARDEN_API}/collections/{collection_id}/nfts"
    params = {
        "size": 100,  # Maximum allowed size
    }

    page = 1
    results = []
    seen_nfts = []

    try:
        while TOTAL_PROCESSED < 250:
            print(f"\rFetching page {page}...", end="")
            response = requests.get(endpoint, params=params)

            # Handle rate limiting with fixed 60-second delay
            if response.status_code == 429:
                print("\nRate limited. Waiting 60 seconds...")
                time.sleep(60)
                continue

            response.raise_for_status()
            data = response.json()

            nfts = data.get("items", [])

            # Process each NFT in the current batch
            for nft_record in nfts:
                nft_id = nft_record["encoded_id"]
                TOTAL_PROCESSED += 1
                if nft_id in seen_nfts:
                    print(f"Already processed {nft_id}")
                seen_nfts.append(nft_id)

                print(f"\nProcessing NFT {TOTAL_PROCESSED}: {nft_id}")
                try:
                    nft_info = await get_nft_info(client, nft_id, target_height)
                    print(nft_info)
                    if isinstance(nft_info, str):
                        nft_info = json.loads(nft_info)

                    if nft_info and isinstance(nft_info, dict) and "current_address" in nft_info:
                        xch_address = nft_info["current_address"]

                        # Skip excluded addresses
                        if xch_address in EXCLUDED_ADDRESSES:
                            continue

                        owner_info = {
                            "nft_id": nft_id,
                            "name": nft_record["name"],
                            "xch_address": xch_address,
                        }
                        print(f"Current owner: {xch_address}")
                        results.append(owner_info)
                    else:
                        print(f"No owner information found for NFT")
                        results.append({
                            "nft_id": nft_id,
                            "error": "No owner information found"
                        })
                except Exception as e:
                    print(f"Failed to process NFT: {str(e)}")
                    results.append({
                        "nft_id": nft_id,
                        "error": str(e)
                    })

            # Check if there are more pages
            next_cursor = data.get("next")
            if not next_cursor or next_cursor == ">":
                break

            # Update params for next page
            params["page"] = next_cursor
            page += 1

            # Add delay between pages
            time.sleep(RATE_LIMIT_DELAY)

        print(f"\nCompleted processing all NFTs: {TOTAL_PROCESSED} total")
        return results

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch collection NFTs: {str(e)}")

async def main():
    try:
        # Check if Chia config exists
        try:
            config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
        except Exception as e:
            print("Error: Chia configuration not found. Is Chia installed and initialized?")
            return

        try:
            client = await FullNodeRpcClient.create(config["self_hostname"], config["full_node"]["rpc_port"],
                                                DEFAULT_ROOT_PATH, config)
        except Exception as e:
            raise Exception(f"Failed to create RPC client: {e}")

        collection_id = sys.argv[1]
        target_height = int(sys.argv[2])

        print(f"\nFetching NFTs from collection {collection_id} before height {target_height}...")
        results = await get_and_process_collection_nfts(client, collection_id, target_height)
        results.sort(key=lambda x: int(re.search(r'\d+', x["name"]).group()), reverse=False)

        # Save results to file
        output_file = "nft_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_file}")

        # Get the header hash of the cutoff block
        final_block = await client.get_block_record_by_height(target_height)
        print(final_block.header_hash.hex())

        client.close()

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
