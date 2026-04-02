import os
import json
import pytest
import aiohttp
from kirkaio import KirkaChatBot

def test_chatbot_initializes_with_args():
    bot = KirkaChatBot("t1", "r1")
    assert bot.token == "t1"
    assert bot.refresh_token == "r1"
    assert bot.creds_file == "creds.json"
    
def test_chatbot_loads_from_creds_json(tmp_path):
    creds_file = tmp_path / "custom_creds.json"
    with open(creds_file, "w") as f:
        json.dump({"token": "loaded_token", "refresh_token": "loaded_refresh"}, f)
        
    bot = KirkaChatBot("old", "old_r", creds_file=str(creds_file))
    assert bot.token == "loaded_token"
    assert bot.refresh_token == "loaded_refresh"
    assert bot.creds_file == str(creds_file)
    
def test_chatbot_on_connect_handler():
    bot = KirkaChatBot("t1", "r1")
    
    def my_handler(ws):
        pass
        
    bot.set_on_connect(my_handler)
    assert bot.on_connect_handler == my_handler

def test_chatbot_raw_handler():
    bot = KirkaChatBot("t", "r")
    
    def raw_h(data, ws):
        pass
        
    bot.set_raw_handler(raw_h)
    assert bot.raw_handler == raw_h
