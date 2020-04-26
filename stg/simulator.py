
# TODO: research tx size
TX_SIZE = 255 / 1024
SETUP_DURATION = 60

class Simulator(object):

    def __init__(self, value, num_nodes, normal_frequency, normal_duration, peak_frequency, peak_duration, fee):
        self.value = value
        self.tx_fee = TX_SIZE * fee
        self.normal_scenario = (normal_frequency, normal_duration)
        self.peak_scenario = (peak_frequency, peak_duration)
        self.number_of_transactions = int(normal_frequency * normal_duration) + int(peak_frequency * peak_duration)
        self.duration = int((normal_duration + peak_duration + SETUP_DURATION) / 60)+1
        self.node_count = min(num_nodes, self.number_of_transactions)
        self.gas_cost = self.tx_fee * (self.number_of_transactions + 2 * num_nodes)
        self.token_amount = value * self.number_of_transactions


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
