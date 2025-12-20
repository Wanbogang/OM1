from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

acct = w3.eth.accounts[0]
to = w3.eth.accounts[1]
tx = {"from": acct, "to": to, "value": w3.to_wei(0.001, "ether"), "gas": 21000}

tx_hash = w3.eth.send_transaction(tx)
print("TX hash:", tx_hash.hex())
