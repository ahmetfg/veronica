from binance.client import Client
'''
    Binance api cridentials
'''
class Cridentials():
    def __init__(self):
        self.apiKey = '<YOUR_BINANCE_API_PUBLIC_KEY>'
        self.secretKey = '<YOUR_BINANCE_API_SECRET_KEY>'
        # optional
        self.comment = "<YOUR_BOT_NAME>" 
    
    def client(self):
        return Client(api_key=self.apiKey,api_secret=self.secretKey)