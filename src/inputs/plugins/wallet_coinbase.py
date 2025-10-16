import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import List, Optional

from cdp import Cdp, Wallet
from providers.factory import create_provider

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider
from providers.factory import create_provider


@dataclass
class Message:
    timestamp: float
    message: str


# TODO(Kyle): Support Cryptos other than ETH
class WalletCoinbase(FuserInput[float]):
    """
    Queries current ETH balance and reports a balance increase
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)

        # Track IO
        self.io_provider = IOProvider()
        self.messages: List[Message] = []

        self.POLL_INTERVAL = 0.5  # seconds between blockchain data updates
        self.COINBASE_WALLET_ID = os.environ.get("COINBASE_WALLET_ID")
        logging.info(f"Using {self.COINBASE_WALLET_ID} as the coinbase wallet id")

        # Initialize Wallet
        # TODO(Kyle): Create Wallet if the wallet ID is not found
        # TODO(Kyle): Support importing other wallets, following https://docs.cdp.coinbase.com/mpc-wallet/docs/wallets#importing-a-wallet
        
    # provider-based init (autopatched)
    self.provider = create_provider("coinbase", {"wallet_id": self.COINBASE_WALLET_ID})
    try:
        self.provider.init()
        ok = self.provider.connect()
        if not ok:
            logging.error("WalletCoinbase: provider.connect() failed")
            self.wallet = None
        else:
            self.wallet = True
    except Exception as e:
        logging.error(f"WalletCoinbase: provider init/connect error: {e}")
        self.wallet = None

    try:
        self.ETH_balance = float(self.provider.get_balance("eth")) if self.wallet else 0.0
    except Exception:
        self.ETH_balance = 0.0
    self.ETH_balance_previous = self.ETH_balance
  

        logging.info("Testing: WalletCoinbase: Initialized")

    async def _poll(self) -> List[float]:
        """
        Poll for Coinbase Wallet balance updates.

        Returns
        -------
        List[float]
            [current_balance, balance_change]
        """
        
    await asyncio.sleep(self.POLL_INTERVAL)

    try:
        current = float(self.provider.get_balance("eth"))
    except Exception as e:
        logging.error(f"WalletCoinbase: get_balance failed: {e}")
        current = self.ETH_balance  # fallback to previous

    balance_change = current - self.ETH_balance_previous
    self.ETH_balance_previous = current
    self.ETH_balance = current

    return [self.ETH_balance, balance_change]
  

    async def _raw_to_text(self, raw_input: List[float]) -> Optional[Message]:
        """
        Convert balance data to human-readable message.

        Parameters
        ----------
        raw_input : List[float]
            [current_balance, balance_change]

        Returns
        -------
        Message
            Timestamped status or transaction notification
        """
        balance_change = raw_input[1]

        message = ""

        if balance_change > 0:
            message = f"{balance_change:.5f}"
            logging.info(f"\n\nWalletCoinbase balance change: {message}")
        else:
            return None

        logging.debug(f"WalletCoinbase: {message}")
        return Message(timestamp=time.time(), message=message)

    async def raw_to_text(self, raw_input: List[float]):
        """
        Process balance update and manage message buffer.

        Parameters
        ----------
        raw_input : List[float]
            Raw balance data
        """
        pending_message = await self._raw_to_text(raw_input)

        if pending_message is not None:
            self.messages.append(pending_message)

    def formatted_latest_buffer(self) -> Optional[str]:
        """
        Format and clear the buffer contents. If there are multiple ETH transactions,
        combine them into a single message.

        Returns
        -------
        Optional[str]
            Formatted string of buffer contents or None if buffer is empty
        """
        if len(self.messages) == 0:
            return None

        transaction_sum = 0

        # all the messages, by definition, are non-zero
        for message in self.messages:
            transaction_sum += float(message.message)

        last_message = self.messages[-1]
        result_message = Message(
            timestamp=last_message.timestamp,
            message=f"You just received {transaction_sum:.5f} ETH.",
        )

        result = f"""
{self.__class__.__name__} INPUT
// START
{result_message.message}
// END
"""

        self.io_provider.add_input(
            self.__class__.__name__, result_message.message, result_message.timestamp
        )
        self.messages = []
        return result
