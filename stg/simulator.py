from datetime import datetime
# TODO: research tx size
TX_SIZE = 255 / 1024
SETUP_DURATION = 60


class Simulator(object):

    def __init__(self, syscoin, value, num_nodes, normal_frequency, normal_duration,
                 peak_frequency, peak_duration, fee, assetGuid, hubAddress):
        self.hubAddress = hubAddress
        self.assetGuid = assetGuid
        self.value = value
        self.tx_fee = TX_SIZE * fee
        self.normal_scenario = (normal_frequency, normal_duration)
        self.peak_scenario = (peak_frequency, peak_duration)
        self.number_of_transactions = int(normal_frequency * normal_duration) + int(peak_frequency * peak_duration)
        self.duration = int((normal_duration + peak_duration + SETUP_DURATION) / 60) + 1
        self.node_count = min(num_nodes, self.number_of_transactions)
        self.gas_cost = self.tx_fee * (self.number_of_transactions + 2 * num_nodes)
        self.token_amount = value * self.number_of_transactions
        self.pattern = {}
        self.timestamps = []
        self.report = ""

    def get_node_patterns(self):
        node_patterns = []
        for index in range(self.node_count):
            node_patterns.append({})
        for timestamp, count in self.pattern.items():
            for index in range(count):
                node_patterns[index][timestamp] = min(1, int(count / self.node_count))
            if count >= self.node_count:
                node_patterns[self.node_count-1][timestamp] = int(count / self.node_count) + (count % self.node_count)
        return node_patterns

    def generate_timestamps(self):
        keys = sorted(self.pattern.keys())
        minimum = keys[0]
        maximum = keys[-1]
        self.timestamps = []
        for index in range(minimum, maximum+1):
            try:  # catch division by 0
                # convert pattern to variable interval accuracy
                total = self.pattern[index]
                difference = 60.0 / total
                for step in range(0, total):
                    self.timestamps.append(index+step*difference)
            except:  # if total == 0, no need to add the timestamp
                pass

    def start(self):
        self.generate_timestamps()
        self.start = datetime.now()
        while self.timestamps:
            self.loop()

    def loop(self):
        now = datetime.now()
        if now > self.start + self.timestamps[0]:
            del(self.timestamps[0])
            self.syscoin.send_tokens(self.assetGuid, self.value, self.hubAddress)
            self.report += "\n{:}: Sent {:d}".format(self.value, now)

    def get_addresses_per_node(self):
        return self.number_of_transactions / self.node_count

    def set_patter(self, pattern):
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
