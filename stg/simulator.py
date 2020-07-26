import time
import random

# TODO: research tx size
TX_SIZE = 260 / 1024
SETUP_DURATION = 60


class Simulator(object):

    def __init__(self, syscoin, pattern, value, num_nodes, fee, assetGuid,
                 hubAddress):
        self.hubAddress = hubAddress
        self.syscoin = syscoin
        self.assetGuid = assetGuid
        self.value = value
        self.tx_fee = 0.001
        self.pattern = pattern
        self.seconds = {int(key) for key in pattern.keys()}
        try:
            self.number_of_transactions = sum(pattern.values())
            self.duration = max(self.seconds) - min(self.seconds)
            self.node_count = min(num_nodes, self.number_of_transactions)
            self.gas_cost = self.tx_fee * (self.number_of_transactions
                                           + 2 * num_nodes)
            self.token_amount = value * self.number_of_transactions
        except Exception:
            pass
        self.timestamps = []
        self.report = ""

    def get_node_patterns(self):
        node_patterns = []
        for index in range(self.node_count):
            node_patterns.append({})
        for timestamp, count in self.pattern.items():
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
                difference = 60.0 / total
                for step in range(0, total):
                    self.timestamps.append(index+step*difference)
            except:  # if total == 0, no need to add the timestamp
                pass

    def start(self):
        self.generate_timestamps()
        self.start = int(time.time())
        while self.timestamps:
            self.loop()

    def loop(self):
        now = int(time.time())
        if now > self.start + self.timestamps[0]:
            del(self.timestamps[0])
            self.syscoin.send_tokens_final(self.value, self.hubAddress)
            self.report += "\n{:d}: Sent {:f}".format(now, self.value)
        time.sleep(1)

    def get_addresses_per_node(self):
        return self.number_of_transactions / self.node_count

    def set_pattern(self, pattern):
        self.pattern = pattern

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
