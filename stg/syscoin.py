import requests
# from requests.auth import HTTPBasicAuth
import json


from stg.logger import logger


class Syscoin(object):

    def __init__(self, asset_guid, hostname="localhost", port=18370, username="u", password="kF0DpJsphi", useSSL=False):
        http = "https://" if useSSL else "http://"
        self.url = "{:}{:}:{:}/".format(http, hostname, port)
        self.auth = requests.auth.HTTPBasicAuth(username, password)
        self.guid = asset_guid
        self.addresses = []
        # not needed if proper wallet in correct location
        # self.loadWallet()
        # self.url = self.url + "wallet/experiment"
        # self.addresses = self.generate_addresses(2)
        # for addressTo in self.addresses:
        #     self.assetAllocationSend(assetGuid, addressFrom, addressTo, amount)


    def generate_addresses(self, number_of_addresses):
        addresses = []
        for index in range(1, number_of_addresses+1):
            answer = self.getNewAddress(label="sim_{:d}".format(index))
            address = json.loads(answer.text)["result"]
        self.addresses += addresses
        return addresses

    def send_tokens(self, assetGuid, amount, addressTo):
        addressFrom = self.addresses.pop()
        self.assetAllocationSend(assetGuid, addressFrom, addressTo, amount)

    def get_sys_balance(self, address):
        answer = self.addressBalance(address)
        print(answer)
        return answer

    def get_token_balance(self, address):
        answer = self.assetAllocationBalance(self.guid, address)
        print(answer)
        return answer


    def getNewAddress(self, label="", addressType="bech32"):
        return self.callFunction("getnewaddress", {"params": [label, addressType]})


    def getAddressesByLabel(self, label):
        return self.callFunction("getaddressesbylabel", {"params": [label]})


    def addressBalance(self, address):
        answer = self.callFunction("addressbalance", {"params": [address]})
        if answer.status_code == 200:
            return answer.json()["result"]["amount"]


    def assetAllocationBalance(self, assetGuid, address):
        answer = self.callFunction("assetallocationbalance", {"params": [assetGuid, address]})
        if answer.status_code == 200:
            return answer.json()["result"]["amount"]


    def assetAllocationSend(self, assetGuid, addressFrom, addressTo, amount):
        return self.callFunction("assetallocationsend", {"params": [assetGuid, addressFrom, addressTo, amount]})


    def createWallet(self, walletName, passphrase="", disablePrivKeys=False, blank=False, avoid_reuse=False):
        return self.callFunction("createwallet", {"params": [walletName, disablePrivKeys, blank, passphrase, avoid_reuse]})


    def loadWallet(self):
        response = self.callFunction("loadwallet", {"params": ["experiment"]})
        # if response.status_code == 500:
        #     return self.createWallet("experiment", blank=False)


    def sendToAddress(self, address, amount, comment="", comment_to="", subtractFeeFromAmount=False, replaceable=False, confTarget=1, estimateMode="UNSET", avoidReuse="True"):
        return self.callFunction("sendtoaddress", {"params": [address, amount, comment, comment_to, subtractFeeFromAmount, replaceable, confTarget, estimateMode, avoidReuse]})



    def createRawTransaction(self, txHeaders, payloadInfo, locktime=0, replaceable=False):
        return self.callFunction("createrawtransaction", {"params": [txHeaders, payloadInfo, locktime, replaceable]})


    def fundRawTransaction(self, hexString, options={}, isWitness=None):
        return self.callFunction("fundrawtransaction", {"params": [hexString, options, isWitness]})


    def signRawTransactionWithKey(self, hexString, privateKeys, txs=[], sigHashType="ALL"):
        return self.callFunction("signrawtransactionwithkey", {"params": [hexString, privateKeys, txs, sigHashType]})


    def sendRawTransaction(self, hexString, maxFeeRate=0.1):
        return self.callFunction("sendrawtransaction", {"params": [hexString, maxFeeRate]})


    def callFunction(self, functionName, message={}):
        message["method"] = functionName
        print(message)
        response = self.request(message)
        print(response.json())
        if not response.ok:
            print(response.status_code)
        return response


    def request(self, message):
        return requests.post(self.url, auth=self.auth, json=message)
