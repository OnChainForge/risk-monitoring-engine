import logging
from web3 import Web3
from web3.exceptions import TransactionNotFound

from app.config import settings

logger = logging.getLogger("blockchain")

w3 = Web3(Web3.HTTPProvider(settings.ethereum_rpc_url))


def fetch_transaction(tx_hash: str) -> dict:
    """
    Fetches an Ethereum transaction by hash and normalizes it into a
    flat payload dict that the rule engine can evaluate.
    """
    try:
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except TransactionNotFound:
        raise ValueError(f"Transaction {tx_hash} not found on the network")
    except Exception as e:
        logger.error(f"Error fetching transaction {tx_hash}: {e}")
        raise

    value_eth = float(w3.from_wei(tx["value"], "ether"))
    gas_price_gwei = float(w3.from_wei(tx["gasPrice"], "gwei"))
    is_contract_call = tx["input"] != "0x" and tx["input"] != b""

    payload = {
        "tx_hash": tx_hash,
        "from": tx["from"],
        "to": tx["to"],
        "value_eth": value_eth,
        "gas_used": receipt["gasUsed"],
        "gas_price_gwei": gas_price_gwei,
        "status": receipt["status"],  # 1 = success, 0 = failed
        "block_number": tx["blockNumber"],
        "is_contract_call": is_contract_call,
        "to_is_contract": w3.eth.get_code(tx["to"]) != b"" if tx["to"] else False,
    }

    logger.info(f"Fetched and normalized transaction {tx_hash}")
    return payload
