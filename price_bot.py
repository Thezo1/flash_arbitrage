import os
import algosdk
from flash_loan import flash_swap
from algosdk.v2client.algod import AlgodClient
from algofi_amm.v0.asset import Asset
from algofi_amm.v0.client import AlgofiAMMTestnetClient, AlgofiAMMMainnetClient
from algofi_amm.v0.config import PoolType

# algofi
from dotenv import dotenv_values

# pactfi
import pactsdk

my_path = os.path.abspath(os.path.dirname("_file_"))
ENV_PATH = os.path.join(my_path, ".env")
user = dotenv_values(ENV_PATH)
key = algosdk.mnemonic.to_private_key(user["MNEMONIC"])
sender = algosdk.mnemonic.from_private_key(key)

IS_MAINNET = True
# algofi client
if IS_MAINNET:
    amm_client_algofi = AlgofiAMMMainnetClient(user_address=sender)
else:
    amm_client_algofi = AlgofiAMMTestnetClient(user_address=sender)

# pactfi client
if IS_MAINNET:
    algod = AlgodClient("", "http://mainnet-api.algonode.network")
else:
    algod = AlgodClient("", "http://testnet-api.algonode.network")

pact = pactsdk.PactClient(algod)

while True:
    print("checking markets...")
    asset1_id = 1
    asset2_id = 31566704

    # fetch assets for algofi
    asset1_algofi = Asset(amm_client_algofi, asset1_id)
    asset2_algofi = Asset(amm_client_algofi, asset2_id)

    # fetch pool for algofi
    pool = amm_client_algofi.get_pool(
        PoolType.CONSTANT_PRODUCT_25BP_FEE, asset1_id, asset2_id
    )
    price_of_asset_algofi = pool.get_pool_price(asset1_id)

    asset1_pactfi = pact.fetch_asset(0)
    asset2_pactfi = pact.fetch_asset(asset2_id)

    pool_pactfi = pact.fetch_pools_by_assets(asset1_pactfi, asset2_pactfi)[0]

    print("========")
    print("ALGOFI")
    print(f"1 {asset2_algofi.name} = {price_of_asset_algofi} {asset1_algofi.name}")
    print("========")

    print("========")
    print("PACTFI")
    print(
        f"1 {asset2_algofi.name} = {pool_pactfi.state.secondary_asset_price} {asset1_algofi.name}"
    )
    print("========")

    # call flash_swap function from flash_loan if prices are not equal up to the second decimal
    if int(price_of_asset_algofi * 100) != int(
        pool_pactfi.state.secondary_asset_price * 100
    ):
        print("trying to swap...")

        flash_swap()
    else:
        continue
