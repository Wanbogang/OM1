import type { IWalletAdapter } from "@om1/wallet-core";
type Hex = `0x${string}`;
declare global { interface Window { ethereum?: any } }

export class MetaMaskAdapter implements IWalletAdapter {
  private addr: string | null = null;

  private get eth() {
    const e = typeof window !== 'undefined' ? window.ethereum : undefined;
    if (!e) throw new Error("MetaMask not found");
    return e;
  }

  async connect(): Promise<void> {
    const accounts: string[] = await this.eth.request({ method: 'eth_requestAccounts' });
    this.addr = accounts?.[0] || null;
    if (!this.addr) throw new Error("No account");
  }

  async disconnect(): Promise<void> { this.addr = null; }

  async getAddress(): Promise<string | null> { return this.addr; }

    private utf8ToHex(s: string): `0x${string}` {
    const bytes = new TextEncoder().encode(s);
    let hex = '0x';
    for (const b of bytes) hex += b.toString(16).padStart(2, '0');
    return hex as `0x${string}`;
  }

  async signMessage(message: string): Promise<string> {
    if (!this.addr) throw new Error("Not connected");
    const msg = this.utf8ToHex(message);
    // Coba urutan params yang umum lebih dulu: [msgHex, address]
    try {
      return await this.eth.request({
        method: 'personal_sign',
        params: [msg, this.addr]
      });
    } catch (e1: any) {
      // Beberapa versi MetaMask pakai urutan [address, msgHex]
      try {
        return await this.eth.request({
          method: 'personal_sign',
          params: [this.addr, msg]
        });
      } catch (e2: any) {
        // Fallback terakhir
        return await this.eth.request({
          method: 'eth_sign',
          params: [this.addr, msg]
        });
      }
    }
  }


  async sendTransaction(tx: { to: string; value?: string; data?: string; gas?: string; }): Promise<string> {
    if (!this.addr) throw new Error("Not connected");
    const req = { from: this.addr, to: tx.to, value: tx.value, data: tx.data, gas: tx.gas };
    return await this.eth.request({ method: 'eth_sendTransaction', params: [req] });
  }
}
