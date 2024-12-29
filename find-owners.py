import asyncio
import requests
from nft import get_nft_info

MINTGARDEN_API = "https://api.mintgarden.io"

def get_collection_nfts(collection_id: str):
    """Fetch all NFTs from a collection using MintGarden API"""
    endpoint = f"{MINTGARDEN_API}/collections/{collection_id}/nfts"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        raise Exception(f"Failed to fetch collection NFTs: {response.status_code} - {response.text}")

async def find_owner_or_height(nft_id: str, target_height=None):
    """Recursively find the current owner or stop at the target block height."""
    nft_info = await get_nft_info(nft_id)
    return nft_info.get("current_address")

async def main():
    collection_id = input("Enter the collection ID: ")
    target_height = input("Enter the target block height (or press Enter to skip): ")
    target_height = int(target_height) if target_height else None

    try:
        # Get all NFTs from the collection
        nfts = get_collection_nfts(collection_id)
        print(f"Fetched {len(nfts)} NFTs from the collection.")

        for nft in nfts:
            nft_id = nft.get("encoded_id")  # MintGarden API returns encoded_id for NFTs
            print(f"\nProcessing NFT ID: {nft_id}")
            current_owner = await find_owner_or_height(nft_id, target_height)
            print(f"Current owner: {current_owner}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
