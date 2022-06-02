import os
import pactsdk
from dotenv import dotenv_values
from algosdk import mnemonic
from algofi_amm.v0.asset import Asset
from algofi_amm.v0.client import AlgofiAMMTestnetClient, AlgofiAMMMainnetClient
from algofi_amm.v0.config import PoolType
from algofi_amm.utils import TransactionGroup
from algosdk.v2client.algod import AlgodClient

my_path = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(my_path, ".env")
user = dotenv_values(ENV_PATH)
sender = mnemonic.to_public_key(user["MNEMONIC"])
key = mnemonic.to_private_key(user["MNEMONIC"])

# set client for algofi
IS_MAINNET = True
if IS_MAINNET:
    amm_client = AlgofiAMMMainnetClient(user_address=sender)
else:
    amm_client = AlgofiAMMTestnetClient(user_address=sender)

# set client for pactfi
if IS_MAINNET:
    algod = AlgodClient("", "http://mainnet-api.algonode.network")
else:
    algod = AlgodClient("", "http://testnet-api.algonode.network")

pact = pactsdk.PactClient(algod)

# SET POOL ASSETS
asset1_id = 1
asset2_id = 31566704

# fetch assets for ALGOFI
swap_input_asset = Asset(amm_client, asset2_id)
swap_output_asset = Asset(amm_client, asset1_id)

# set amounts, in micro_algo, 1 algo = 1_000_000
swap_asset_amount = 1_000_000_000
# this is for conversion, change this to whatever amount you wnat to swap for, here it is 1_000 of tokens
swap_asset_amount_to_convert = 1_000
flash_loan_asset = swap_output_asset
flash_loan_amount = 1_000_000_000
min_amount_to_receive = 2

# prepare pool for ALGOFI
asset1 = Asset(amm_client, asset1_id)
asset2 = Asset(amm_client, asset2_id)
pool = amm_client.get_pool(PoolType.CONSTANT_PRODUCT_25BP_FEE, asset1_id, asset2_id)
lp_asset_id = pool.lp_asset_id
lp_asset = Asset(amm_client, lp_asset_id)

# fetch assets for PACTFI
asset1_pactfi = pact.fetch_asset(0)
asset2_pactfi = pact.fetch_asset(asset2_id)

# prepare pool for PACTFI
pool_pactfi = pact.fetch_pools_by_assets(asset1_pactfi, asset2_pactfi)[0]


# truncate price so it's easier to compare although not accurate, but it works...
def flash_swap():
    pactfi = int(pool_pactfi.state.secondary_asset_price * 100)
    algofi = int(pool.get_pool_price(asset1_id) * 100)

    # if price on pactfi is greater than price on algofi
    # buy low sell high so buy algofi sell pactfi...
    if pactfi > algofi:
        # prepare swap and some "minor" converions
        int_price1 = int(pool.get_pool_price(asset1_id) * 100)
        micro1 = int_price1 * 10_000
        swap = pool_pactfi.prepare_swap(
            asset=asset1_pactfi,
            amount=micro1 * swap_asset_amount_to_convert,
            slippage_pct=0.1,
        )
        buy = pool.get_swap_exact_for_txns(
            sender,
            swap_input_asset,
            swap_asset_amount,
            min_amount_to_receive=min_amount_to_receive,
        )
        sell = swap.prepare_tx(sender)
        gid = TransactionGroup(buy.transactions + sell.transactions)
        flash_loan_txn = pool.get_flash_loan_txns(
            sender, swap_input_asset, flash_loan_amount, group_transaction=gid
        )
        flash_loan_txn.sign_with_private_key(sender, key)
        flash_loan_txn.submit(amm_client.algod, wait=True)

    # if pactfi is less than algofi
    # buy low sell high, so buy on pacfi sell on algofi...
    elif pactfi < algofi:
        swap1 = pool_pactfi.prepare_swap(
            asset=asset2_pactfi,
            amount=swap_asset_amount,
            slippage_pct=0.1,
        )
        int_price = int(pool_pactfi.state.secondary_asset_price * 100)
        micro = int_price * 10_000
        buy1 = swap1.prepare_tx(sender)
        sell1 = pool.get_swap_exact_for_txns(
            sender,
            swap_output_asset,
            (micro * swap_asset_amount_to_convert),
            min_amount_to_receive=min_amount_to_receive,
        )
        gid1 = TransactionGroup(buy1.transactions + sell1.transactions)
        flash_loan_txn1 = pool.get_flash_loan_txns(
            sender, swap_input_asset, flash_loan_amount, group_transaction=gid1
        )
        flash_loan_txn1.sign_with_private_key(sender, key)
        flash_loan_txn1.submit(amm_client.algod, wait=True)
    else:
        print("too slow, balance has equallized")
