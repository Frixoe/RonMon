import json
import requests
import os
import telebot
import time
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

sleep_time = 1

class RonMon:
    def __init__(self):
        self.peer_count_vald = None

    def read_config(self):
        try:
            with open(os.path.expanduser("~") + os.path.sep + ".config/ronmon/ron.json", "r") as f:
                self.config = json.load(f)
        except Exception as e:
            self.config = {"vald_url": os.getenv("VALD_URL"),
                           "remote_url": "https://api.roninchain.com/rpc",
                           "chat_id": -953422664
                          }
            print(f"Error: {e}")
            print("Loading default config...")

    def rpc_call(self, url, data):
        headers = {"Content-Type": "application/json"}
        data = json.dumps(data)
        r = requests.post(url, data=data, headers=headers)
        return json.loads(r.text)

    def get_bridge_operator_balance(self):
        data = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [ os.getenv("BRIDGE_OPERATOR_ADDRESS"), "latest" ],
                "id": 1
               }
        self.validator_balance_vald = int(self.rpc_call(self.config["vald_url"], data)["result"], 16)
        # self.validator_balance_remote = []
        # self.validator_balance_remote = int(self.rpc_call(self.config["remote_url"], data)["result"], 16)

    def get_current_block(self):
        data = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 83
               }
        self.current_block_vald = int(self.rpc_call(self.config["vald_url"], data)["result"], 16)
        # self.current_block_remote = int(self.rpc_call(self.config["remote_url"], data)["result"], 16)

    def get_peer_count(self):
        data = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "net_peerCount",
                "params": [],
                "id": 74
               }
        self.peer_count_vald = int(self.rpc_call(self.config["vald_url"], data)["result"], 16)

    def get_blockchain_info_from_validator(self):
        return { current_block: self.current_block_vald, peer_count: self.peer_count_vald, bridge_operator_balance: self.validator_balance_vald }

    def get_blockchain_info(self):
        return { current_block: self.current_block_remote, peer_count: self.peer_count_vald, bridge_operator_balance: self.validator_balance_remote }

    def alerts_BalanceLow(self):
        if self.validator_balance_vald < 150:
            bot.send_message(self.config["chat_id"], f'''Ronin Bridge Operator Balance is Low!\nBridge Operator Balance: {self.validator_balance_vald}
                              ''')
        print(f'''Ronin Bridge Operator Balance is Low!\nBridge Operator Balance: {self.validator_balance_vald}
                          ''')

    def alert_BlockNum(self):
        if self.current_block_vald < self.current_block_remote - 5:
            bot.send_message(self.config["chat_id"], f'''Block Height of Ronin Validator is Lagging\n
                              Validator Height: {self.current_block_vald}
                              Remote Node Height: {self.current_block_remote}
                              ''')
        print(f'''Block Height of Ronin Validator is Lagging\n
                          Validator Height: {self.current_block_vald}
                          Remote Node Height: {self.current_block_remote}
                          ''')

    def alert_DeficitPeers(self):
        if self.peer_count_vald < 5:
            bot.send_message(self.config["chat_id"], f'''Ronin Validator Peer Count Below 5
                              Validator Peers: {self.peer_count_vald}
                              ''')
        print(f'''Ronin Validator Peer Count Below 5
                          Validator Peers: {self.peer_count_vald}
                          ''')

    def monitor(self):
        while True:
            # self.get_peer_count()
            # self.get_current_block()
            self.get_bridge_operator_balance()
            # self.alert_BlockNum()
            # self.alert_DeficitPeers()
            self.alerts_BalanceLow()
            time.sleep(sleep_time)


ron = RonMon()
ron.read_config()

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
        Hi there, I am RonMon.
        I am here to monitor you Ronin Validator
    """)

@bot.message_handler(commands=['status'])
def send_status(message):
    status = ron.get_blockchain_info_from_validator()
    bot.reply_to(message, "Validator Status: \n" + str(status))

@bot.message_handler(commands=['rstatus'])
def send_remote_status(message):
    status = ron.get_blockchain_info()
    bot.reply_to(message, "Remote Node Status: \n" + str(status))

@bot.message_handler(commands=['silence'])
def silence_alerts(message):
    sleep_time = 172800
    bot.reply_to(message, "Setting refresh timer to 2 days! Please use /unsilence to reset the timer back to 1 second and resume monitoring.")

@bot.message_handler(commands=['unsilence'])
def silence_alerts(message):
    sleep_time = 1
    bot.reply_to(message, "Setting refresh time to 1 second!")

def start_monitoring():
    bot.send_message(ron.config["chat_id"], f"Monitoring Validator: {ron.config['vald_url']}")
    ron.monitor()

start_monitoring()
bot.infinity_polling()
