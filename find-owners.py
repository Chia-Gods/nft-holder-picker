import asyncio
import json
import requests
import time
from typing import List, Dict, Optional
from nft import get_nft_info
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH

MINTGARDEN_API = "https://api.mintgarden.io"
RATE_LIMIT_DELAY = 1  # seconds between API calls

def get_collection_nfts(collection_id: str) -> List[str]:
    """
    Fetch all NFTs from a collection using MintGarden API
    Args:
        collection_id: The collection ID from MintGarden
    Returns:
        List of NFT IDs
    Raises:
        Exception: If API call fails
    """
    endpoint = f"{MINTGARDEN_API}/collections/{collection_id}/nfts"
    all_nfts = []
    params = {
        "size": 100  # Maximum allowed size
    }
    
    try:
        while True:
            response = requests.get(endpoint, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                print("Rate limited. Waiting 60 seconds...")
                time.sleep(10)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            nfts = data.get("items", [])
            all_nfts.extend([nft["encoded_id"] for nft in nfts if "encoded_id" in nft])
            
            # Check if there are more pages
            next_cursor = data.get("next")
            if not next_cursor or next_cursor == ">":
                break
                
            # Update params for next page
            params["cursor"] = next_cursor
            
            # Add delay between requests to avoid rate limiting
            time.sleep(1)  # 1 second delay between requests
            
        return all_nfts
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch collection NFTs: {str(e)}")

async def process_nfts(nft_ids: List[str], target_height: Optional[int] = None) -> List[Dict]:
    """
    Process a list of NFTs and get their current owners
    Args:
        nft_ids: List of NFT IDs to process
        target_height: Optional target block height
    Returns:
        List of dictionaries containing NFT information
    """
    results = []
    total = len(nft_ids)
    
    for index, nft_id in enumerate(nft_ids, 1):
        print(f"\nProcessing NFT {index}/{total}: {nft_id}")
        try:
            nft_info = await get_nft_info(nft_id)
            if nft_info.get("error"):
                print(f"Error processing NFT: {nft_info['error']}")
            elif nft_info.get("current_address"):
                print(f"Current owner: {nft_info['current_address']}")
            results.append(nft_info)
        except Exception as e:
            print(f"Failed to process NFT: {str(e)}")
            results.append({"nft_id": nft_id, "error": str(e)})
        
        # Rate limiting
        if index < total:
            time.sleep(RATE_LIMIT_DELAY)
    
    return results

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
        nft_ids = get_collection_nfts(collection_id)
        
        if not nft_ids:
            print("No NFTs found in collection")
            return
            
        print(f"Found {len(nft_ids)} NFTs in collection")
        
        results = await process_nfts(nft_ids, target_height)
        
        # Save results to file
        output_file = "nft_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
