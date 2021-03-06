import requests

class Syscoin(object):

    def __init__(self, asset_guid, hostname="localhost", port=8370,
                 username="wLcuoduV84", password="G6pRRb0laT", useSSL=False):
        http = "https://" if useSSL else "http://"
        self.url = "{:}{:}:{:}/".format(http, hostname, port)
        self.auth = requests.auth.HTTPBasicAuth(username, password)
        self.guid = asset_guid
        self.addresses = []
        self.aas = {"method": "assetallocationsend",
                    "params": [1533716253, "", "sys1q33euagvrnd8tkzctlc4f78vjqhhz3tsj8lxt3e", 1]}
        self.srtww = {"method": "signrawtransactionwithwallet",
                      "params": [""]}
        self.srt = {"method": "sendrawtransaction",
                    "params": ["", 0.1]}
        # not needed if proper wallet in correct location
        # self.loadWallet()
        # self.url = self.url + "wallet/experiment"
        # self.addresses = self.generate_addresses(2)
        # for addressTo in self.addresses:
        #     self.assetAllocationSend(assetGuid, addressFrom, addressTo, amount)

    def cleanup(self, addressTo):
        # send token
        answer = self.callFunction("listaddressgroupings")
        addresses = []
        if answer.ok:
            for group in answer.json()["result"]:
                for address_tuple in group:
                    addresses.append(address_tuple[0])
        answer = self.assetAllocationBalances(self.guid, addresses)
        if answer.ok:
            for address, balance in answer.json()["result"].items():
                self.send_tokens(balance, address, addressTo)
        # send sys
        answer = self.callFunction("listaddressgroupings")
        amount = 0
        if answer.ok:
            for group in answer.json()["result"]:
                for address_tuple in group:
                    amount += address_tuple[1]
        self.sendToAddress(addressTo, amount-0.001)

    def get_blockheight(self):
        answer = self.callFunction("getblockcount")
        if answer.ok:
            return answer.json()["result"]

    def generate_addresses(self, number_of_addresses):
        addresses = []
        for index in range(number_of_addresses):
            address = self.getNewAddress(label="sim_{:d}".format(index))
            addresses.append(address)
        self.addresses += addresses
        return addresses

    def send_tokens(self, amount, addressFrom, addressTo):
        try:
            message = self.aas
            message["params"][1] = addressFrom
            answer = requests.post(self.url, auth=self.auth, json=message)
            message = self.srtww
            message["params"][0] = answer.json()["result"]["hex"]
            answer = requests.post(self.url, auth=self.auth, json=message)
            message = self.srt
            message["params"][0] = answer.json()["result"]["hex"]
            answer = requests.post(self.url, auth=self.auth, json=message)
            # hex = self.assetAllocationSend(self.guid, addressFrom,
            #                                addressTo, amount)
            # transaction = self.signRawTransactionWithWallet(hex)
            # return self.sendRawTransaction(transaction)
            return answer.json()["result"]
        except Exception as err:
            print(err)

    def prepare_send(self, amount, addressFrom, addressTo):
        message = self.aas
        message["params"][1] = addressFrom
        answer = requests.post(self.url, auth=self.auth, json=message)
        message = self.srtww
        message["params"][0] = answer.json()["result"]["hex"]
        answer = requests.post(self.url, auth=self.auth, json=message)
        return answer.json()["result"]["hex"]

    def send_sys(self, amount, addressFrom, addressTo):
        try:
            hex = self.sendFrom(addressFrom, addressTo, amount)
            transaction = self.signRawTransactionWithWallet(hex)
            return self.sendRawTransaction(transaction)  # returns txid
        except Exception as err:
            print(err)

    def send_many_sys(self, fromAddress, toAddresses, amounts):
        try:
            return self.sendMany(dict(zip(toAddresses, amounts)))
        except Exception as err:
            print(err)

    def send_many_tokens(self, addressFrom, toAddresses, amounts):
        try:
            recipients = [{"address": address, "amount": amount}
                          for address, amount in zip(toAddresses, amounts)]
            hex = self.assetAllocationSendMany(self.guid, addressFrom,
                                               recipients)
            transaction = self.signRawTransactionWithWallet(hex)
            return self.sendRawTransaction(transaction)  # returns txid
        except Exception as err:
            print(err)

    def send_tokens_final(self, amount, addressTo):
        addressFrom = self.addresses.pop()
        return (addressFrom, self.send_tokens(amount, addressFrom, addressTo))

    def get_sys_balance(self):
        answer = self.getBalance()
        return answer

    def get_token_balance(self, address):
        answer = self.assetAllocationBalance(self.guid, address)
        return answer

    def sendMany(self, targets):
        answer = self.callFunction("sendmany", {"params": ["", targets]})
        if answer.ok:
            return answer.json()["result"]
        else:
            raise Exception(answer.json()["error"]["message"])

    def getBalance(self):
        answer = self.callFunction("getbalance")
        if answer.ok:
            return answer.json()["result"]

    def getNewAddress(self, label="", addressType="bech32"):
        answer = self.callFunction("getnewaddress",
                                   {"params": [label, addressType]})
        if answer.ok:
            return answer.json()["result"]

    def getAddressesByLabel(self, label):
        return self.callFunction("getaddressesbylabel", {"params": [label]})

    def addressBalance(self, address):
        answer = self.callFunction("addressbalance", {"params": [address]})
        if answer.ok:
            return answer.json()["result"]["amount"]

    def assetAllocationBalance(self, assetGuid, address):
        answer = self.callFunction("assetallocationbalance",
                                   {"params": [assetGuid, address]})
        if answer.ok:
            return answer.json()["result"]["amount"]

    def assetAllocationBalances(self, assetGuid, addresses):
        answer = self.callFunction("assetallocationbalances",
                                   {"params": [assetGuid, addresses]})
        return answer

    def assetAllocationSend(self, assetGuid, addressFrom, addressTo, amount):
        answer = self.callFunction("assetallocationsend",
                                   {"params": [assetGuid, addressFrom,
                                               addressTo, amount]})
        if answer.ok:
            return answer.json()["result"]["hex"]
        else:
            raise Exception(answer.json()["error"]["message"])

    def assetAllocationSendMany(self, assetGuid, addressFrom, targets):
        answer = self.callFunction("assetallocationsendmany",
                                   {"params": [assetGuid, addressFrom,
                                               targets, ""]})
        if answer.ok:
            return answer.json()["result"]["hex"]
        else:
            raise Exception(answer.json()["error"]["message"])

    def createWallet(self, walletName, passphrase="", disablePrivKeys=False,
                     blank=False, avoid_reuse=False):
        return self.callFunction("createwallet",
                                 {"params": [walletName, disablePrivKeys,
                                             blank, passphrase, avoid_reuse]})

    def loadWallet(self):
        response = self.callFunction("loadwallet", {"params": ["experiment"]})
        # if response.status_code == 500:
        #     return self.createWallet("experiment", blank=False)

    def sendFrom(self, fromAddress, toAddress, amount):
        answer = self.callFunction("sendfrom", {"params": [fromAddress,
                                                           toAddress, amount]})
        if answer.ok:
            return answer.json()["result"]["hex"]
        else:
            raise Exception(answer.json()["error"]["message"])

    def sendToAddress(self, address, amount, comment="", comment_to="",
                      subtractFeeFromAmount=False, replaceable=False,
                      confTarget=1, estimateMode="UNSET", avoidReuse=False):
        return self.callFunction("sendtoaddress",
                                 {"params": [address, amount, comment,
                                             comment_to, subtractFeeFromAmount,
                                             replaceable, confTarget,
                                             estimateMode, avoidReuse]})

    def signRawTransactionWithWallet(self, hexString):
        answer = self.callFunction("signrawtransactionwithwallet",
                                   {"params": [hexString]})
        if answer.ok:
            return answer.json()["result"]["hex"]

    def sendRawTransaction(self, hexString, maxFeeRate=0.1):
        answer = self.callFunction("sendrawtransaction",
                                   {"params": [hexString, maxFeeRate]})
        if answer.ok:
            return answer.json()["result"]

    def callFunction(self, functionName, message={}):
        message["method"] = functionName
        response = self.request(message)
        if not response.ok:
            print(message)
            print(response.json())
        return response

    def request(self, message):
        return requests.post(self.url, auth=self.auth, json=message)
