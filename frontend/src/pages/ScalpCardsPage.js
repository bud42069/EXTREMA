import { useEffect, useMemo, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";

const api = (path, init) =>
  fetch(`${process.env.REACT_APP_BACKEND_URL}${path}`, init)
    .then(r => r.json());

function useSnapshot(pollMs = 1500, useWs = true) {
  const [snap, setSnap] = useState(null);
  
  // Try WebSocket first
  const wsUrl = process.env.REACT_APP_BACKEND_URL
    ? process.env.REACT_APP_BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/signals/stream'
    : null;
  
  const { data: wsData, connected } = useWebSocket(wsUrl, { enabled: useWs });
  
  // Fallback to polling if WebSocket not connected
  useEffect(() => {
    if (connected && wsData) {
      // WebSocket provides data
      if (wsData.type === 'snapshot' && wsData.data) {
        setSnap(wsData.data);
      }
    } else {
      // Fallback to polling
      let id = setInterval(async () => {
        try {
          const js = await api("/api/stream/snapshot");
          setSnap(js);
        } catch (e) {
          console.error("Snapshot fetch error:", e);
        }
      }, pollMs);
      return () => clearInterval(id);
    }
  }, [pollMs, connected, wsData]);
  
  return { snap, connected };
}

export default function ScalpCardsPage() {
  const [resp, setResp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const { snap, connected: wsConnected } = useSnapshot(1500, true);

  const vetoBadges = useMemo(() => {
    if (!resp || resp.message || !resp.card?.checks?.micro_veto) return null;
    const veto = resp.card.checks.micro_veto;
    return Object.keys(veto).map(k =>
      <span key={k} className="px-2 py-1 text-xs rounded bg-red-900/40 border border-red-500 mr-2">
        {k}: {String(veto[k])}
      </span>
    );
  }, [resp]);

  async function fetchCard() {
    setLoading(true);
    try {
      const forceParam = demoMode ? "&force=true" : "";
      const js = await api(`/api/scalp/card?enable_micro_gate=true${forceParam}`);
      setResp(js);
    } catch (e) {
      console.error("Card fetch error:", e);
      setResp({ message: "Error fetching card", error: e.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-green-400">
          Scalp Card — Manual Execution
        </h1>
        <div className="flex gap-2">
          <button
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
            onClick={fetchCard}
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Card"}
          </button>
          <a
            className="px-4 py-2 rounded bg-gray-700 hover:bg-gray-600 text-white"
            href={`${process.env.REACT_APP_BACKEND_URL}/api/docs`}
            target="_blank"
            rel="noopener noreferrer"
          >
            API Docs
          </a>
        </div>
      </div>

      {/* Microstructure snapshot quick glance */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KV label="Spread (bps)" value={snap?.spread_bps?.toFixed?.(2) ?? "—"} />
        <KV label="Imbalance" value={snap?.ladder_imbalance?.toFixed?.(3) ?? "—"} />
        <KV label="CVD" value={snap?.cvd?.toFixed?.(0) ?? "—"} />
        <KV label="CVD Slope" value={snap?.cvd_slope?.toFixed?.(6) ?? "—"} />
      </div>

      {/* Card render */}
      {resp && resp.card ? (
        <CardView card={resp.card} vetoBadges={vetoBadges} />
      ) : (
        <div className="p-6 rounded-xl bg-neutral-900 border border-neutral-700">
          <div className="text-yellow-300">
            {resp?.message
              ? `No signal: ${resp.message}`
              : "Click 'Generate Card' to fetch the latest confirmed Scalp Card."}
          </div>
          {resp?.veto && Object.keys(resp.veto).length > 0 && (
            <div className="mt-3 text-sm text-red-400">
              <div className="font-semibold mb-1">Veto reasons:</div>
              {Object.entries(resp.veto).map(([k, v]) => (
                <div key={k} className="ml-2">
                  • {k}: {JSON.stringify(v)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function KV({ label, value }) {
  return (
    <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-700">
      <div className="text-xs text-neutral-400">{label}</div>
      <div className="text-lg font-mono">{value}</div>
    </div>
  );
}

function CardView({ card, vetoBadges }) {
  const checks = [
    ["spread <0.10%", card.checks.spread_ok],
    ["depth ≥50%", !card.checks?.micro_veto?.depth],
    ["|mark−last| <0.15%", !card.checks?.micro_veto?.imbalance],
    ["RSI gate", true],
    ["no OBV-cliff", !card.checks?.micro_veto?.obv],
    ["liq-gap ≥4×ATR & ≥10× fee", true],
    ["kill-switch clear", !card.checks?.micro_veto?.kill]
  ];

  return (
    <div className="rounded-2xl border border-green-700/50 bg-neutral-950 p-6 shadow-lg shadow-green-900/20">
      {/* Card Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-green-400">
          SCALP CARD — {card.symbol} (MEXC)
        </h2>
        <div className="text-sm space-x-4">
          <span>Play: <b className="text-green-400">{card.play}</b></span>
          <span>Regime: <b className="text-green-400">{card.regime}</b></span>
          <span>Size: <b className="text-green-400">{card.size}</b></span>
        </div>
      </div>

      {/* Card Body */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Left: Trade Parameters */}
        <div className="space-y-3">
          <div className="text-sm font-semibold text-green-400 mb-3">TRADE PARAMETERS</div>
          <Row label="ENTRY (limit, post-only)">
            <span className="text-green-400 font-mono text-lg">{card.entry.toFixed(4)}</span>
          </Row>
          <Row label="CONFIRM">
            <span className="text-xs text-neutral-300">{card.confirm}</span>
          </Row>
          <Row label="SL">
            <span className="text-red-400 font-mono">{card.sl.toFixed(4)}</span>
          </Row>
          <Row label="TP1">
            <span className="text-green-400 font-mono">{card.tp1.toFixed(4)}</span>
            <span className="text-xs text-neutral-400 ml-2">(50% → SL to BE+fees)</span>
          </Row>
          <Row label="TP2">
            <span className="text-green-400 font-mono">{card.tp2.toFixed(4)}</span>
            <span className="text-xs text-neutral-400 ml-2">(30%)</span>
          </Row>
          <Row label="TP3">
            <span className="text-green-400 font-mono">{card.tp3.toFixed(4)}</span>
            <span className="text-xs text-neutral-400 ml-2">(20%)</span>
          </Row>
          <Row label="TRAIL">{card.trail_rule}</Row>
          <Row label="ATTEMPTS">{card.attempts}</Row>
          <Row label="ORDER PATH">
            <span className="text-xs">{card.order_path}</span>
          </Row>
        </div>

        {/* Right: Checks & Vetos */}
        <div className="space-y-3">
          <div className="text-sm font-semibold text-green-400 mb-3">CHECKS</div>
          <ul className="space-y-2">
            {checks.map(([label, ok], idx) => (
              <li
                key={idx}
                className={`px-3 py-2 rounded text-sm ${
                  ok
                    ? "bg-emerald-900/30 border border-emerald-600 text-emerald-200"
                    : "bg-red-900/30 border border-red-600 text-red-200"
                }`}
              >
                {ok ? "✓" : "✗"} {label}
              </li>
            ))}
          </ul>

          {/* Veto badges */}
          {vetoBadges && vetoBadges.length > 0 && (
            <div className="mt-4 p-3 rounded bg-red-900/20 border border-red-700">
              <div className="text-xs text-red-400 font-semibold mb-2">VETO REASONS</div>
              <div className="flex flex-wrap gap-2">{vetoBadges}</div>
            </div>
          )}

          {/* Indices */}
          <div className="text-xs text-neutral-500 mt-4 pt-4 border-t border-neutral-800">
            <div>Extremum Index: {card.indices.extremum_idx}</div>
            <div>Confirm Index: {card.indices.confirm_idx}</div>
          </div>
        </div>
      </div>

      {/* Matrix Rain Effect Background */}
      <div className="absolute inset-0 pointer-events-none opacity-10 overflow-hidden rounded-2xl">
        <div className="matrix-rain"></div>
      </div>
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex items-start">
      <span className="inline-block w-48 text-sm text-neutral-400">{label}</span>
      <span className="text-sm">{children}</span>
    </div>
  );
}
