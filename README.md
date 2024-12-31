# nft-holder-picker
Tool to choose a winner at random from a list of holders of a particular NFT project. At this time this is intended for
the Chia Gods collection only. Updates will be created in the future to make this more friendly for any collection.

## Prerequisites

1. A running Chia full node
2. Python 3.11 or 3.12
3. The following Python packages:
    - `chia-blockchain`
    - `requests`

## What It Does

This tool:
1. Connects to the MintGarden API to fetch NFT collection data
2. Verifies current ownership through your local Chia node
3. Tracks unique holders while excluding specified addresses (from `excluded_list.py`)
4. Processes up to 250 NFTs from a collection (Based on the collection size for Chia Gods)
5. Saves the results to a JSON file for further processing

## How to Use

1. Clone this repository:
   ```bash
   git clone https://github.com/Chia-Gods/nft-holder-picker.git
   cd nft-holder-picker
   ```
   
2. Create a local venv and install requirements:
   ```bash
   python3 -m venv venv
   . ./venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run the script with your collection ID and target height:
   ```bash
   python3 find_owners.py <collection_id> <target_height>
   ```

## Example

```bash
python3 find_owners.py col1zpqtfv9yynf0q95sg27n44r25vphg6n8rlzn6v3j6r8mm52zjvlq8hcqru 6427100
```

The script will output progress:
```
Fetching NFTs from collection...
Fetching page 1...
Processing NFT 1: nft1...
Current owner: xch1...
Processing NFT 2: nft2...
Current owner: xch2...
```

Results are saved to `nft_results.json`:
```json
[
  {
    "nft_id": "nft1l7x8jw9zakwv9hydv2695cn2vxd53q4rpu0pzl4mg797r6e2k42ssypshe",
    "name": "Chia Gods #5",
    "xch_address": "xch19gavsvangp87dcsrwlkqzz8p9mgjavw2jknh6scfn97cpxc2t78q7q9tnw"
  },
  {
    "nft_id": "nft1zuvy9n9e2nwpkn6a652c07nm52q9gwu8yu8qfw6cruf2et6g2jmsmr3k6w",
    "name": "Chia Gods #8",
    "xch_address": "xch17d68m7kdc6655fcw5funeyzwthfuvur4ke764l8ty2kp5j2lrjjsh4ddyv"
  },
]
```

## Finding Your Collection ID

1. Visit MintGarden.io
2. Navigate to your collection
3. The collection ID is in the URL:
    - Example: `https://mintgarden.io/collections/col1zpqtfv9yynf0q95sg27n44r25vphg6n8rlzn6v3j6r8mm52zjvlq8hcqru`
    - The ID is the `col1...` part

## Troubleshooting

- Ensure your Chia node is running and fully synced
- Check that you have the correct permissions for your Chia config
- Verify your collection ID is correct
- Make sure all required Python packages are installed
