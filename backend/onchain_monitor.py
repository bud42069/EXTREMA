"""
On-chain monitoring using Helius API for Solana.
Detects whale transfers, CEX flows, and staking activity.
"""
import aiohttp
import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class OnChainSignal:
    """On-chain signal detected."""
    signal_type: str  # whale_transfer | cex_inflow | cex_outflow | staking_spike
    amount: float
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    timestamp: int = 0
    significance: str = "medium"  # low | medium | high
    bias: str = "neutral"  # bullish | bearish | neutral


class HeliusOnChainMonitor:
    """
    Monitor Solana on-chain activity using Helius API.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Helius monitor.
        
        Args:
            api_key: Helius API key
        """
        self.api_key = api_key
        self.base_url = f"https://api.helius.xyz/v0"
        
        # Known CEX addresses (sample - expand as needed)
        self.cex_addresses = {
            # Binance
            "binance": ["9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"],
            # Coinbase (example)
            "coinbase": ["H8sMJSCQxfKiFTCfDR3DUMLPwcRbM61LGFJ8N4dK3WjS"],
            # Add more as identified
        }
        
        # Whale threshold (in SOL)
        self.whale_threshold = 10000  # 10k SOL
        
        # Recent activity cache
        self.recent_activity: List[OnChainSignal] = []
        self.max_cache_size = 100
    
    async def fetch_token_accounts(self, mint: str = "So11111111111111111111111111111111111111112") -> Dict:
        """
        Fetch token accounts for SOL.
        
        Args:
            mint: Token mint address (default is wrapped SOL)
        
        Returns:
            Token account data
        """
        try:
            url = f"{self.base_url}/addresses/{mint}/balances"
            params = {"api-key": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Helius API error: {response.status}")
                        return {}
        
        except Exception as e:
            logger.error(f"Error fetching token accounts: {e}")
            return {}
    
    async def get_address_transactions(self, address: str, limit: int = 10) -> List[Dict]:
        """
        Get recent transactions for an address.
        
        Args:
            address: Solana address
            limit: Number of transactions to fetch
        
        Returns:
            List of transactions
        """
        try:
            url = f"{self.base_url}/addresses/{address}/transactions"
            params = {
                "api-key": self.api_key,
                "limit": limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Helius API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return []
    
    async def detect_whale_transfers(self) -> List[OnChainSignal]:
        """
        Detect large SOL transfers (whale activity).
        
        Returns:
            List of whale transfer signals
        """
        signals = []
        
        try:
            # In production, you'd monitor mempool or recent blocks
            # For now, we'll use a simplified approach
            
            # This is a placeholder - in production you'd use Helius webhooks
            # or their transaction streaming API
            
            # Example: Monitor known whale addresses
            whale_addresses = [
                # Add known whale addresses here
            ]
            
            for address in whale_addresses:
                txs = await self.get_address_transactions(address, limit=5)
                
                for tx in txs:
                    # Parse transaction for large transfers
                    # This is simplified - actual parsing would be more complex
                    if 'amount' in tx and tx['amount'] > self.whale_threshold:
                        signal = OnChainSignal(
                            signal_type='whale_transfer',
                            amount=tx['amount'],
                            from_address=tx.get('from'),
                            to_address=tx.get('to'),
                            timestamp=tx.get('timestamp', int(datetime.now(timezone.utc).timestamp())),
                            significance='high',
                            bias='neutral'  # Determine based on context
                        )
                        signals.append(signal)
        
        except Exception as e:
            logger.error(f"Error detecting whale transfers: {e}")
        
        return signals
    
    def is_cex_address(self, address: str) -> Optional[str]:
        """
        Check if address belongs to a CEX.
        
        Args:
            address: Solana address
        
        Returns:
            CEX name if found, None otherwise
        """
        for cex_name, addresses in self.cex_addresses.items():
            if address in addresses:
                return cex_name
        return None
    
    async def detect_cex_flows(self) -> List[OnChainSignal]:
        """
        Detect CEX inflows/outflows.
        Large inflows = potentially bearish (selling pressure)
        Large outflows = potentially bullish (accumulation)
        
        Returns:
            List of CEX flow signals
        """
        signals = []
        
        try:
            # Monitor known CEX addresses
            for cex_name, addresses in self.cex_addresses.items():
                for address in addresses:
                    txs = await self.get_address_transactions(address, limit=5)
                    
                    for tx in txs:
                        if 'amount' in tx and tx['amount'] > self.whale_threshold / 2:
                            # Check if inflow or outflow
                            if tx.get('to') == address:
                                # Inflow to CEX
                                signal = OnChainSignal(
                                    signal_type='cex_inflow',
                                    amount=tx['amount'],
                                    from_address=tx.get('from'),
                                    to_address=address,
                                    timestamp=tx.get('timestamp', int(datetime.now(timezone.utc).timestamp())),
                                    significance='high',
                                    bias='bearish'  # Selling pressure
                                )
                                signals.append(signal)
                            
                            elif tx.get('from') == address:
                                # Outflow from CEX
                                signal = OnChainSignal(
                                    signal_type='cex_outflow',
                                    amount=tx['amount'],
                                    from_address=address,
                                    to_address=tx.get('to'),
                                    timestamp=tx.get('timestamp', int(datetime.now(timezone.utc).timestamp())),
                                    significance='high',
                                    bias='bullish'  # Accumulation
                                )
                                signals.append(signal)
        
        except Exception as e:
            logger.error(f"Error detecting CEX flows: {e}")
        
        return signals
    
    async def detect_staking_activity(self) -> List[OnChainSignal]:
        """
        Detect unusual staking activity.
        Large staking = bullish (locking up supply)
        Large unstaking = potentially bearish
        
        Returns:
            List of staking signals
        """
        signals = []
        
        try:
            # Placeholder for staking detection
            # In production, monitor stake account changes
            pass
        
        except Exception as e:
            logger.error(f"Error detecting staking activity: {e}")
        
        return signals
    
    async def get_on_chain_confluence(self, direction: str, lookback_minutes: int = 60) -> Dict:
        """
        Get on-chain confluence for a signal direction.
        
        Args:
            direction: 'long' or 'short'
            lookback_minutes: How far back to look for signals
        
        Returns:
            Dict with confluence information
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        # Filter recent signals
        recent_signals = [
            s for s in self.recent_activity 
            if s.timestamp >= cutoff_timestamp
        ]
        
        # Count bullish/bearish signals
        bullish_count = len([s for s in recent_signals if s.bias == 'bullish'])
        bearish_count = len([s for s in recent_signals if s.bias == 'bearish'])
        
        # Check if on-chain supports the direction
        on_chain_aligned = False
        on_chain_score = 0
        
        if direction == 'long':
            if bullish_count > bearish_count:
                on_chain_aligned = True
                on_chain_score = min(100, (bullish_count / max(1, bearish_count)) * 30)
        else:
            if bearish_count > bullish_count:
                on_chain_aligned = True
                on_chain_score = min(100, (bearish_count / max(1, bullish_count)) * 30)
        
        return {
            'aligned': on_chain_aligned,
            'score': on_chain_score,
            'recent_signals': len(recent_signals),
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'signals': [
                {
                    'type': s.signal_type,
                    'amount': s.amount,
                    'bias': s.bias,
                    'significance': s.significance
                }
                for s in recent_signals[-5:]  # Last 5 signals
            ]
        }
    
    async def monitor_loop(self):
        """
        Continuous monitoring loop.
        Runs in background and caches recent activity.
        """
        logger.info("Helius on-chain monitor started")
        
        while True:
            try:
                # Detect various signals
                whale_signals = await self.detect_whale_transfers()
                cex_signals = await self.detect_cex_flows()
                staking_signals = await self.detect_staking_activity()
                
                # Combine and cache
                all_signals = whale_signals + cex_signals + staking_signals
                
                for signal in all_signals:
                    self.recent_activity.append(signal)
                    logger.info(f"On-chain signal: {signal.signal_type} | {signal.amount:.2f} SOL | {signal.bias}")
                
                # Trim cache
                if len(self.recent_activity) > self.max_cache_size:
                    self.recent_activity = self.recent_activity[-self.max_cache_size:]
                
                # Wait before next check (5 minutes)
                await asyncio.sleep(300)
            
            except Exception as e:
                logger.error(f"Error in on-chain monitor loop: {e}")
                await asyncio.sleep(60)
    
    def enhance_signal_with_onchain(self, signal: Dict) -> Dict:
        """
        Enhance a signal with on-chain confluence data.
        
        Args:
            signal: Signal dictionary
        
        Returns:
            Enhanced signal with on-chain data
        """
        direction = signal.get('direction', 'long')
        
        # Get on-chain confluence
        on_chain = asyncio.run(self.get_on_chain_confluence(direction, lookback_minutes=60))
        
        # Add to signal
        signal['onchain_aligned'] = on_chain['aligned']
        signal['onchain_score'] = on_chain['score']
        signal['onchain_signals_count'] = on_chain['recent_signals']
        signal['onchain_recent'] = on_chain['signals']
        
        # Boost confluence score if on-chain aligned
        if on_chain['aligned']:
            signal['confluence_score'] = min(100, signal.get('confluence_score', 0) + on_chain['score'])
        
        return signal
