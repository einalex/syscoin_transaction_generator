import time
import json
import random
from math import ceil
from stg.logger import logger
# TODO: research tx size
TX_SIZE = 260 / 1024
SETUP_DURATION = 60


class Simulator(object):

    def __init__(self, syscoin, pattern, value, num_nodes, fee, assetGuid,
                 hubAddress):
        self.hub_address = hubAddress
        self.syscoin = syscoin
        self.assetGuid = assetGuid
        self.value = value
        self.sys_fee = 0.00002750
        self.token_fee = 0.00005820
        self.num_nodes = num_nodes
        try:
            self.set_pattern(pattern)
        except Exception:
            pass
        self.blocks = []
        self.report = ""

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.minutes = {int(key) for key in pattern.keys()}
        self.num_addresses = ceil(max(list(pattern.values()))/12)
        self.number_of_transactions = sum(pattern.values())
        self.duration = max(self.minutes) - min(self.minutes)
        self.node_count = min(self.num_nodes, self.number_of_transactions)
        self.gas_cost = self.sys_fee * (2 * self.number_of_transactions) \
            + self.token_fee * (2 * self.number_of_transactions)
        self.token_amount = self.value * self.number_of_transactions

    def distribute_funds(self):
        self.syscoin.generate_addresses(self.num_addresses)
        at_least = self.number_of_transactions // self.num_addresses
        counts = [at_least] * self.num_addresses
        rest = self.number_of_transactions % self.num_addresses
        counts = list(map(lambda c: c + 1, counts[:rest])) + counts[rest:]
        sys_amounts = list(map(lambda c: c * 2 * self.token_fee
                               + c * self.sys_fee, counts))
        token_amounts = list(map(lambda c: c * self.value, counts))
        self.syscoin.send_many_tokens(self.hub_address, self.syscoin.addresses,
                                      token_amounts)
        self.syscoin.send_many_sys(self.hub_address, self.syscoin.addresses,
                                   sys_amounts)

    def wait_for_block(self):
        first = self.syscoin.get_blockheight()
        logger.info("Waiting for block {:d}.".format(first + 1))
        second = first
        while first == second:
            second = self.syscoin.get_blockheight()
            time.sleep(1)
        logger.info("Reached block {:d}.".format(second))

    def multi_token_fee(self, recipients):
        return round((5240 + 600 * recipients) / 10**8, 8)

    def multi_sys_fee(self, recipients):
        return round((1160 + 310 * recipients) / 10**8, 8)

    def distribute_funds_single(self, filename="100k-address-set3.json"):
        # load addresses
        with open(filename) as f:
            addresses = json.load(f)
        first_wave_size = 4
        second_wave_size = 4
        third_wave_size = 4
        logger.info("send first wave")
        first_batch = addresses[:first_wave_size]
        sys_amount = \
            round(self.multi_sys_fee(second_wave_size)
                  + self.multi_token_fee(second_wave_size)
                  + second_wave_size * self.multi_sys_fee(third_wave_size)
                  + second_wave_size * self.multi_token_fee(third_wave_size)
                  + second_wave_size * third_wave_size * self.token_fee, 8)
        first_batch = addresses[:first_wave_size]
        sys_amounts = [sys_amount] * first_wave_size
        token_amount = second_wave_size * third_wave_size * self.value
        token_amounts = [token_amount] * first_wave_size
        self.syscoin.send_many_tokens(self.hub_address, first_batch,
                                      token_amounts)
        self.wait_for_block()
        self.syscoin.send_many_sys(self.hub_address, first_batch, sys_amounts)
        self.wait_for_block()
        logger.info("send second wave")
        offset = 0
        sys_amount = \
            round(self.multi_sys_fee(third_wave_size)
                  + self.multi_token_fee(third_wave_size)
                  + third_wave_size * self.token_fee, 8)

        sys_amounts = [sys_amount] * second_wave_size
        token_amount = third_wave_size * self.value
        token_amounts = [token_amount] * second_wave_size
        for fromAddress in first_batch:
            toAddresses = addresses[-offset-second_wave_size:-offset]
            # print("tokens from {:}, to {:}, amount {:f}".format(fromAddress, toAddresses, token_amount))
            self.syscoin.send_many_tokens(fromAddress, toAddresses,
                                          token_amounts)
            offset += second_wave_size
        self.wait_for_block()
        offset = first_wave_size
        for fromAddress in first_batch:
            toAddresses = addresses[-offset-second_wave_size:-offset]
            # print("sys from {:}, to {:}, amount {:f}".format(fromAddress, toAddresses, sys_amount))
            self.syscoin.send_many_sys(fromAddress, toAddresses,
                                       sys_amounts)
            offset += second_wave_size
        self.wait_for_block()
        second_batch = addresses[-first_wave_size*second_wave_size:]
        # send third wave
        logger.info("send third wave")
        offset = 0
        sys_amount = self.token_fee
        sys_amounts = [sys_amount] * third_wave_size
        token_amount = self.value
        token_amounts = [token_amount] * third_wave_size
        for fromAddress in second_batch:
            toAddresses = addresses[offset:offset+third_wave_size]
            # print("tokens from {:}, to {:}, amount {:f}".format(fromAddress, toAddresses, token_amount))
            self.syscoin.send_many_tokens(fromAddress, toAddresses,
                                          token_amounts)
            offset += third_wave_size
        self.wait_for_block()
        offset = 0
        for fromAddress in second_batch:
            toAddresses = addresses[offset:offset+third_wave_size]
            # print("sys from {:}, to {:}, amount {:f}".format(fromAddress, toAddresses, sys_amount))
            self.syscoin.send_many_sys(fromAddress, toAddresses,
                                       sys_amounts)
            offset += third_wave_size
        logger.info("done")

    def send_funds_single(self, addresses):
        for fromAddress in addresses:
            self.syscoin.send_tokens(self.value, fromAddress, self.hub_address)

    def get_node_patterns(self):
        node_patterns = []
        for index in range(self.node_count):
            node_patterns.append({})
        for timestamp, count in self.pattern.items():
            timestamp = int(timestamp)
            if count >= self.node_count:
                pre_number = count//self.node_count
                for node in range(self.node_count):
                    node_patterns[node][timestamp] = pre_number
            nodes = random.sample(range(self.node_count),
                                  count % self.node_count)
            for node in nodes:
                try:
                    node_patterns[node][timestamp] = \
                            node_patterns[node][timestamp] + 1
                except Exception:
                    node_patterns[node][timestamp] = 1
        return node_patterns

    def generate_timestamps(self):
        keys = sorted(self.pattern.keys())
        minimum = keys[0]
        maximum = keys[-1]
        self.timestamps = []
        for index in range(int(minimum), int(maximum)+1):
            try:  # catch division by 0
                # convert pattern to variable interval accuracy
                total = self.pattern[str(index)]
                difference = 60 / total
                for step in range(total):
                    self.timestamps.append(int(60 * index + step * difference))
            except:  # if total == 0, no need to add the timestamp
                pass

    def hub_start(self, patterns, addresses):
        self.blocks = {}
        tmp_patterns = {}
        for node_id in range(len(patterns)):
            self.blocks[node_id] = sorted(patterns[node_id].keys())
            tmp_patterns[node_id] = patterns[node_id]
        current = self.syscoin.get_blockheight()
        delay = 0
        self.start = current + delay
        while self.blocks:
            self.hub_loop(tmp_patterns, addresses)
            time.sleep(1)

    def hub_loop(self, patterns, addresses):
        now = self.syscoin.get_blockheight()
        offset = 0
        source_length = len(self.syscoin.addresses)
        # the list needed to avoid a RuntimeError during deletion
        for node_id, blocks in list(self.blocks.items()):
            if now >= self.start + blocks[0]:
                target_length = len(addresses[node_id])
                num_transactions = patterns[node_id][blocks[0]]
                for index in range(num_transactions):
                    fromAddress = self.syscoin.addresses[
                            (offset + index) % source_length]
                    toAddress = addresses[node_id][index % target_length]
                    self.syscoin.send_sys(
                            self.token_tx_fee, fromAddress, toAddress)
                    txid = self.syscoin.send_tokens(
                        self.value, fromAddress, toAddress)
                    log = ("{:d}: Hub sent {:.2f} "
                           "from {:} to {:} - {:}").format(
                           now, self.value, fromAddress, toAddress, txid)
                    print(log)
                    self.report += "\n" + log
                offset += 2 * num_transactions
                del(self.blocks[node_id][0])
                if not self.blocks[node_id]:
                    del(self.blocks[node_id])

    def minion_start(self, filename):
        transaction_count = self.pattern["1"]
        offset = self.node_id * transaction_count
        with open(filename) as f:
            addresses = json.load(f)
        addresses = addresses[offset:offset+transaction_count]
        for address in addresses:
            self.syscoin.send_tokens(self.value, address, self.hub_address)
    # def minion_start(self):
    #     current = self.syscoin.get_blockheight()
    #     delay = 0
    #     self.start = current + delay
    #     self.blocks = sorted(self.pattern.keys())
    #     while self.blocks:
    #         self.minion_loop()
    #         time.sleep(1)

    def minion_loop(self):
        source_length = len(self.syscoin.addresses)
        now = self.syscoin.get_blockheight()
        if now >= self.start + self.blocks[0]:
            for index in range(self.pattern[self.blocks[0]]):
                fromAddress = self.syscoin.addresses[index % source_length]
                txid = self.syscoin.send_tokens(
                    self.value, fromAddress, self.hub_address)
            del(self.blocks[0])
            log = "{:d}: Node {:d} sent {:.2f} from {:} to {:} - {:}".format(
                    now, self.node_id, self.value,
                    fromAddress, self.hub_address, txid)
            print(log)
            self.report += "\n" + log

    def get_addresses_per_node(self):
        return self.number_of_transactions / self.node_count

    def get_gas_cost(self):
        return self.gas_cost

    def get_required_tokens(self):
        return self.token_amount

    def get_tx_count(self):
        return self.number_of_transactions

    def get_node_count(self):
        return self.node_count

    def get_duration(self):
        return self.duration
