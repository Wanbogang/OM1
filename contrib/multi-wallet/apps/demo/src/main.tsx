import { createRoot } from 'react-dom/client';
import { WalletConnectAdapter } from '../../../packages/walletconnect/src/index';
import { MetaMaskAdapter } from '../../../packages/metamask/src/index';

const pid = import.meta.env.VITE_WC_PROJECT_ID;
const chains = (import.meta.env.VITE_EIP155_CHAINS || 'eip155:11155111').split(','); // Sepolia
let provider: 'wc' | 'mm' = 'wc';
let wc = new WalletConnectAdapter({ projectId: pid, chains });
let mm = new MetaMaskAdapter();

function setStatus(t:string){ const el=document.getElementById('status'); if(el) el.textContent=t; console.log('[STATUS]',t); }
function getActive(){ return provider==='wc' ? wc : mm; }

async function onConnect(){ try{ setStatus('Connecting...'); await getActive().connect(); const a=await getActive().getAddress(); setStatus(`Connected: ${a}`);}catch(e:any){ setStatus(`Connect error: ${e?.message||e}`); }}
async function onSign(){ try{ const s=await getActive().signMessage('hello from OM1 demo'); setStatus(`Signed: ${s.slice(0,18)}…`);}catch(e:any){ setStatus(`Sign error: ${e?.message||e}`);} }
async function onSendTx(){ try{ const a=await getActive().getAddress(); if(!a) throw new Error('Not connected'); const h=await getActive().sendTransaction({ to:a, value:'0x0' }); setStatus(`Tx: ${h.slice(0,12)}…`);}catch(e:any){ setStatus(`Tx error: ${e?.message||e}`);} }

function App(){
  const masked = pid ? (pid.slice(0,6)+'…'+pid.slice(-4)) : '(no PID)';
  return (
    <div style={{padding:16,fontFamily:'ui-sans-serif'}}>
      <h1>OM1 Multi-Wallet Demo</h1>
      <p>Render OK — jika ini terlihat, React jalan.</p>
      <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
        <label>Provider:&nbsp;</label>
        <select onChange={(e)=>{provider=(e.target as HTMLSelectElement).value as any; setStatus(`Provider: ${provider}`);}}>
          <option value="wc">WalletConnect</option>
          <option value="mm">MetaMask (ext)</option>
        </select>
      </div>
      <div style={{display:'flex', gap:8}}>
        <button onClick={onConnect}>Connect</button>
        <button onClick={onSign}>Sign Msg</button>
        <button onClick={onSendTx}>Send Tx</button>
      </div>
      <div id="status" style={{marginTop:8}}>-</div>
      <small style={{opacity:.6}}>PID: {masked} | Chains: {chains.join(',')}</small>
    </div>
  );
}
createRoot(document.getElementById('root')!).render(<App/>);
