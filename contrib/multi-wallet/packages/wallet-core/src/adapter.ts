export interface IWalletAdapter {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  getAddress(): Promise<string | null>;
  signMessage(message: string): Promise<string>;
  sendTransaction(tx: {
    to: string;
    value?: string;   // hex or decimal string
    data?: string;    // 0x...
    gas?: string;
  }): Promise<string>; // tx hash
}
