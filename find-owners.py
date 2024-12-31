import asyncio
import json
import requests
import time
from typing import List, Dict, Optional
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from nft import get_nft_info
from excluded_list import EXCLUDED_ADDRESSES

MINTGARDEN_API = "https://api.mintgarden.io"
RATE_LIMIT_DELAY = 1  # seconds between API calls
TOTAL_PROCESSED = 0
async def get_and_process_collection_nfts(collection_id: str, target_height: Optional[int] = None):
    """
    Fetch and process NFTs from a collection using MintGarden API
    Args:
        collection_id: The collection ID from MintGarden
        target_height: Optional target block height
    """
    endpoint = f"{MINTGARDEN_API}/collections/{collection_id}/nfts"
    params = {
        "size": 100  # Maximum allowed size
    }
    
    results = []
    page = 1
    
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
            current_batch = [nft["encoded_id"] for nft in nfts if "encoded_id" in nft]
            
            # Process each NFT in the current batch
            for nft_id in current_batch:
                total_processed += 1
                print(f"\nProcessing NFT {total_processed}: {nft_id}")
                try:
                    nft_info = await get_nft_info(nft_id)
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
                            "xch_address": xch_address
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
                
                # Rate limiting between NFT processing
                time.sleep(RATE_LIMIT_DELAY)
            
            # Check if there are more pages
            next_cursor = data.get("next")
            if not next_cursor or next_cursor == ">":
                break
                
            # Update params for next page
            params["cursor"] = next_cursor
            page += 1
            
            # Add delay between pages
            time.sleep(1)
            
        print(f"\nCompleted processing all NFTs: {total_processed} total")
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

        collection_id = input("Enter the collection ID: ")
        target_height = input("Enter the target block height (or press Enter to skip): ")
        target_height = int(target_height) if target_height.strip() else None

        print("\nFetching NFTs from collection...")
        results = await get_and_process_collection_nfts(collection_id, target_height)
        
        # Save results to file
        output_file = "nft_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
