import UniversalProvider from "@walletconnect/universal-provider";
import { WalletConnectModal } from "@walletconnect/modal";
import type { IWalletAdapter } from "@om1/wallet-core";
import { stringToHex } from "viem";

type Hex = `0x${string}`;

export class WalletConnectAdapter implements IWalletAdapter {
  private provider: UniversalProvider | null = null;
  private address: string | null = null;
  private chains: string[];
  private projectId: string;

  constructor(opts: { projectId: string; chains?: string[] }) {
    this.projectId = opts.projectId;
    this.chains = opts.chains?.length ? opts.chains : ["eip155:8453"];
  }
  async connect(): Promise<void> {
    const pid =
      this.projectId ||
      (import.meta as any)?.env?.VITE_WC_PROJECT_ID ||
      "";
    if (!pid) throw new Error("Missing WalletConnect projectId");

    if (!this.provider) {
      this.provider = await UniversalProvider.init({ projectId: pid });

      const modal = new WalletConnectModal({
        projectId: pid,
        standaloneChains: this.chains
      });

      const open = (uri: any) => {
        const u = typeof uri === "string" ? uri : (uri?.uri || "");
        if (u) modal.openModal({ uri: u });
      };

      // dukung varian event dari lib
      // @ts-ignore
      this.provider.on?.("display_uri", open);
      // @ts-ignore
      this.provider.client?.on?.("display_uri", open);

      (this as any)._wc_modal = modal;
    }
    const session = await this.provider.connect({
      namespaces: {
        eip155: {
          chains: this.chains,
          methods: ["eth_sendTransaction", "personal_sign", "eth_signTypedData"],
          events: ["accountsChanged", "chainChanged"]
        }
      }
    });

    try { (this as any)._wc_modal?.closeModal(); } catch {}

    const accs = session.namespaces?.eip155?.accounts ?? [];
    this.address = accs.length ? accs[0].split(":").pop() || null : null;
    if (!this.address) throw new Error("No account");
  }
  async disconnect(): Promise<void> {
    if (this.provider) {
      try { await this.provider.disconnect(); } catch {}
    }
    this.address = null;
  }

  async getAddress(): Promise<string | null> {
    return this.address;
  }

  async signMessage(message: string): Promise<string> {
    if (!this.provider || !this.address) throw new Error("Not connected");
    const msgHex: Hex = stringToHex(message);
    const sig = await this.provider.request({
      method: "personal_sign",
      params: [msgHex, this.address]
    }) as string;
    return sig;
  }

  async sendTransaction(tx: { to: string; value?: string; data?: string; gas?: string; }): Promise<string> {
    if (!this.provider || !this.address) throw new Error("Not connected");
    const req = { from: this.address, to: tx.to, value: tx.value, data: tx.data, gas: tx.gas };
    const hash = await this.provider.request({
      method: "eth_sendTransaction",
      params: [req]
    }) as string;
    return hash;
  }
}
