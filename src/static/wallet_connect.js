/* Minimal: connect via injected provider (Metamask) and send tx hash to backend */
async function connectAndSendOrder(orderId, toAddress, valueInEther) {
  if (!window.ethereum) {
    alert("Please use a wallet or WalletConnect-enabled dapp browser");
    return;
  }
  const provider = new ethers.providers.Web3Provider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  const signer = provider.getSigner();
  const tx = await signer.sendTransaction({
    to: toAddress,
    value: ethers.utils.parseEther(valueInEther)
  });
  // kirim tx.hash ke backend untuk dimonitor
  await fetch('/api/order_with_wallet', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({order_id: orderId, tx_hash: tx.hash})
  });
  console.log("tx sent", tx.hash);
}
