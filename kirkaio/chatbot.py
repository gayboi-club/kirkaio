import asyncio
import json
import logging
import os
from typing import Any, Awaitable, Callable, Dict, Optional, Union

import aiohttp

from kirkaio.models import GlobalChatUser

log = logging.getLogger(__name__)


class Context:
    def __init__(self, packet: dict, ws: aiohttp.ClientWebSocketResponse):
        self.raw_packet = packet
        self.ws = ws
        self.type: int = packet.get(
            "type", 0
        )  # should always be 2 in a command context
        self.message: str | None = packet.get("message")
        self.user: GlobalChatUser | None = None
        usr = packet.get("user")
        if usr:
            self.user = GlobalChatUser(
                id=usr.get("id"),
                short_id=usr.get("shortId"),
                name=usr.get("name"),
                level=usr.get("level"),
                role=usr.get("role"),
            )


class KirkaChatBot:
    """
    A global chat bot for Kirka.io.
    Warning: Using this may lead to your account being banned. Use at your own risk.
    """

    def __init__(
        self,
        token: str = "",
        refresh_token: str = "",
        commands: Optional[Dict[str, Callable]] = None,
        creds_file: str = "creds.json",
        prefix: str = "=",
        skip_token_refresh: bool = False,
    ):
        self.uri = "wss://chat.kirka.io"
        self.token_url = "https://login.xsolla.com/api/oauth2/token"
        self.token = token
        self.prefix = prefix
        self.refresh_token = refresh_token
        self.commands = commands or {}
        self.creds_file = creds_file
        self.skip_token_refresh = skip_token_refresh
        self.raw_handler: Optional[Callable] = None
        self.on_connect_handler: Optional[Callable] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None

        if os.path.exists(self.creds_file):
            try:
                with open(self.creds_file, "r") as f:
                    data = json.load(f)
                    if "token" in data:
                        self.token = data["token"]
                    if "refresh_token" in data:
                        self.refresh_token = data["refresh_token"]
            except Exception as e:
                log.warning(f"Could not load credentials from {self.creds_file}: {e}")

    async def _refresh_tokens(self) -> None:
        if not self.session:
            return

        data = {
            "grant_type": "refresh_token",
            "client_id": "303",
            "redirect_uri": "https://kirka.io",
            "refresh_token": self.refresh_token,
        }
        headers = {
            "Origin": "https://kirka.io",
            "User-Agent": "Mozilla/5.0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "websocket",
            "Sec-Fetch-Site": "same-site",
        }

        async with self.session.post(self.token_url, data=data, headers=headers) as r:
            r.raise_for_status()
            res = await r.json()

            self.token = res["access_token"]
            self.refresh_token = res["refresh_token"]

            # persist updated tokens
            try:
                with open(self.creds_file, "w") as f:
                    json.dump(
                        {"token": self.token, "refresh_token": self.refresh_token}, f
                    )
            except Exception as e:
                log.error(f"Failed to update credentials file: {e}")

            log.info("Token refreshed")

    async def _handle_type_2(
        self, packet: Dict[str, Any], ws: aiohttp.ClientWebSocketResponse
    ) -> None:
        log.debug(f"Received: {packet}")

        msg = packet.get("message", "")
        user = packet.get("user", {})
        short_id = user.get("shortId", "ERRROR")

        if not msg.startswith(self.prefix):
            return

        parts = msg[len(self.prefix) :].split()
        if not parts:
            return

        cmd_name = parts[0]

        if cmd_name in self.commands:
            try:
                handler = self.commands[cmd_name]
                reply = handler(Context(packet, ws))
                if asyncio.iscoroutine(reply):
                    reply = await reply

                if reply:
                    formatted = f"#{short_id}: {reply[:100]}"
                    await ws.send_str(formatted)
            except Exception as e:
                log.error(f"Command error: {e}")

    def add_command(self, name: str, handler: Callable) -> None:
        """Register a command handler."""
        self.commands[name] = handler

    def set_on_connect(
        self,
        handler: Union[
            Callable[[aiohttp.ClientWebSocketResponse], None],
            Callable[[aiohttp.ClientWebSocketResponse], Awaitable[None]],
        ],
    ) -> None:
        """Register a handler for when the bot connects to the server."""
        self.on_connect_handler = handler

    def set_raw_handler(
        self,
        handler: Union[
            Callable[[Any, aiohttp.ClientWebSocketResponse], None],
            Callable[[Any, aiohttp.ClientWebSocketResponse], Awaitable[None]],
        ],
    ) -> None:
        """Register a handler for all raw JSON messages received."""
        self.raw_handler = handler

    async def send_message(self, message: str) -> None:
        """Send a message to the global chat."""
        if self.ws and not self.ws.closed:
            await self.ws.send_str(message)
        else:
            log.warning("Cannot send message, websocket is not connected.")

    async def listen(self) -> None:
        """Start the chat bot."""
        async with aiohttp.ClientSession() as session:
            self.session = session
            while True:  # reconnect loop
                try:
                    if not self.token and not self.skip_token_refresh:
                        log.info("no token, refreshing")
                        await self._refresh_tokens()

                    async with session.ws_connect(
                        self.uri,
                        protocols=[f"{self.token}----------0"],
                    ) as ws:
                        self.ws = ws
                        log.info("Connected to chat")

                        if self.on_connect_handler:
                            try:
                                res = self.on_connect_handler(ws)
                                if asyncio.iscoroutine(res):
                                    await res
                            except Exception as e:
                                log.error(f"On connect handler error: {e}")

                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    data = json.loads(msg.data)
                                    if self.raw_handler:
                                        try:
                                            res = self.raw_handler(data, ws)
                                            if asyncio.iscoroutine(res):
                                                await res
                                        except Exception as e:
                                            log.error(f"Raw handler error: {e}")

                                    if isinstance(data, dict) and data.get("type") == 2:
                                        await self._handle_type_2(data, ws)
                                except json.JSONDecodeError:
                                    pass
                            elif msg.type in (
                                aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR,
                            ):
                                log.warning(f"Websocket closed or errored: {msg.type}")
                                break

                except Exception as e:
                    log.error(f"Connection error: {e}")

                    # try refreshing token before reconnect
                    try:
                        await self._refresh_tokens()
                    except Exception as err:
                        log.error(f"Refresh failed: {err}")
                        await asyncio.sleep(5)
