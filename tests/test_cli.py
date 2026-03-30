from unittest.mock import AsyncMock, patch, MagicMock
import pytest
import sys
from kirkaio.cli import main

@pytest.fixture
def mock_client():
    with patch("kirkaio.KirkaClient", autospec=True) as m:
        client_instance = m.return_value.__aenter__.return_value
        yield client_instance

def test_cli_user(mock_client):
    user = MagicMock()
    user.name = "TestUser"
    user.short_id = "S1"
    user.role = "USER"
    user.stats.kd_ratio = 1.5
    user.stats.win_rate = 50.0
    mock_client.get_user = AsyncMock(return_value=user)
    
    with patch.dict("os.environ", {"KIRKA_API_KEY": "test"}):
        with patch.object(sys, "argv", ["kirkaio", "user", "S1"]):
            main()
    mock_client.get_user.assert_called_once()

def test_cli_clan(mock_client):
    clan = MagicMock()
    clan.name = "TestClan"
    clan.member_count = 5
    clan.members = []
    mock_client.get_clan = AsyncMock(return_value=clan)
    
    with patch.dict("os.environ", {"KIRKA_API_KEY": "test"}):
        with patch.object(sys, "argv", ["kirkaio", "clan", "C1"]):
            main()
    mock_client.get_clan.assert_called_once_with("C1")

def test_cli_leaderboard(mock_client):
    mock_client.get_solo_leaderboard = AsyncMock()
    with patch.dict("os.environ", {"KIRKA_API_KEY": "test"}):
        with patch.object(sys, "argv", ["kirkaio", "leaderboard", "solo"]):
            main()
    mock_client.get_solo_leaderboard.assert_called_once()

def test_cli_no_key():
    with patch.dict("os.environ", {}, clear=True):
        with patch.object(sys, "argv", ["kirkaio", "user", "S1"]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1
