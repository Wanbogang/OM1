const log = (s) => { document.getElementById('log').textContent += s + '\\n'; };

document.getElementById('connect').onclick = async () => {
  if (!window.ethereum) {
    alert('No injected wallet detected. Install MetaMask or use a compatible wallet.');
    return;
  }
  try {
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    log('Connected: ' + accounts[0]);
    document.getElementById('pay').disabled = false;
  } catch (err) {
    log('Connect error: ' + err.message);
  }
};

document.getElementById('pay').onclick = async () => {
  try {
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    const from = accounts[0];
    const txParams = { from, to: from, value: "0x0" }; // self 0-value tx
    log('Requesting wallet to send tx...');
    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [txParams]
    });
    log('Tx sent: ' + txHash);

    // contoh order id — ganti sesuai alur order kamu
    const ORDER_ID_EXAMPLE = "b0521fe8";

    // Notify server with order_id
    try {
      await fetch('http://localhost:8080/api/payment/signed', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ txHash, order_id: ORDER_ID_EXAMPLE })
      });
      log('Server notified of tx for order ' + ORDER_ID_EXAMPLE);
    } catch (e) {
      log('Notify server failed: ' + e.message);
    }
  } catch (err) {
    log('Tx error: ' + (err.message || err));
  }
};
