
import sys
import json
from time import sleep

from stg.simulator import Simulator
from stg.logger import logger
from stg.communication import Communicator
from stg.messages import ADDRESS_REQUEST, ADDRESS_RESPONSE, PATTERN, \
                         SIGNAL_READY, SIGNAL_SUCCESS, SIGNAL_START, REPORT

# account for python2/3 difference
if "raw_input" not in dir():
    raw_input = input


def ask_user(question):
    reply = str(raw_input("{:} (Y/n): ".format(question))).lower().strip()
    try:
        if reply == 'y' or reply == 'yes':
            return True
        if reply == 'n' or reply == 'no':
            return False
        if not reply:
            return True
        else:
            logger.error('Invalid Input')
            return ask_user(question)
    except Exception as error:
        logger.warning("Please enter valid inputs")
        print(error)
        return ask_user(question)


class StateMachine(object):
    def __init__(self, syscoin, args):
        self.syscoin = syscoin
        self.args = args

    def start(self):
        if self.args.sat:
            logger.info("Starting as the Hub node")
            hub = Hub(self.syscoin, self.args)
            hub.start()
        else:
            logger.info("Starting as a satellite node")
            satellite = Satellite(self.syscoin, self.args)
            satellite.start()

    def start_communicator(self, key):
        # check connection to satellite systems
        try:
            self.communicator = Communicator(self.args.sat, self.args.port,
                                             key)
        except Exception as err:
            logger.error(err)
            logger.error(("Could not connect to other sbt processes. "
                          "Make sure they are running and can be reached."))
            sys.exit(3)

    def start_simulator(self):
        try:
            with open(self.args.pattern) as pattern_file:
                self.simulator = Simulator(
                        self.syscoin, json.load(pattern_file),
                        float(self.args.value), len(self.args.sat),
                        float(self.args.fee), int(self.args.token),
                        self.args.addr)
        except Exception as err:
            if isinstance(self, Satellite):
                self.simulator = Simulator(self.syscoin, {}, 0, 0, 0,
                                           int(self.args.token),
                                           self.args.addr)
            else:
                logger.error(err)
                sys.exit(1)


class Hub(StateMachine):
    def start(self):
        self.start_simulator()
        # calculate required sys fees and token balances
        self.check_funds()
        key = self.get_user_consent()
        self.communicator = Communicator(self.args.sat, self.args.port, key)

        # TODO: ask satellite systems for addresses
        logger.info("Calculating funds distribution")
        patterns, totals = self.calculate_fund_distribution()
        logger.info("Collecting target addresses")
        addresses = self.get_addresses(totals)
        logger.info("Starting fund distribution")
        self.simulator.start_distribution(patterns, addresses)
        # for address in addresses:
        #     self.syscoin.send_tokens(self.simulator.value, address,
        #                              self.args.addr)
        #     self.syscoin.sendToAddress(address, self.simulator.tx_fee)
        logger.info("Signalling for fund return")
        self.start_pattern(patterns, self.communicator.connection_list)
        self.wait_for_pattern_end()
        logger.info("Waiting for reports")
        reports = self.wait_for_report()
        self.output_report(reports)
        logger.info("Program ends")
        # TODO: write logfile?

    def calculate_fund_distribution(self):
        node_patterns = self.simulator.get_node_patterns()
        node_transactions = []
        for node_pattern in node_patterns:
            number_of_transactions = 0
            for timestamp, count in node_pattern.items():
                number_of_transactions += count
            node_transactions.append(number_of_transactions)
        return (node_patterns, node_transactions)

    def output_report(self, reports):
        logger.info(self.simulator.report)
        for report in reports:
            logger.info(report)

    def wait_for_report(self):
        reports = []
        messages = self.communicator.receive()
        for message in messages:
            if message["type"] == REPORT:
                reports.append(message["payload"])
            else:
                logger.error(("Received unexpected"
                              "message type: {:}").format(message["type"]))
                sys.exit(6)
        return reports

    def wait_for_pattern_end(self):
        messages = self.communicator.receive()
        for message in messages:
            if not message["type"] == SIGNAL_SUCCESS:
                logger.error(("Received unexpected "
                              "message type: {:}").format(message["type"]))
                sys.exit(6)

    def start_pattern(self, patterns, connections):
        for index in range(len(patterns)):
            message = self.communicator.create_single_message(
                                PATTERN, connections[index],
                                (self.simulator.value, patterns[index]))
            self.communicator.send(message)
        messages = self.communicator.receive()
        for message in messages:
            if not message["type"] == SIGNAL_READY:
                logger.error(("Received unexpected "
                              "message type: {:}").format(message["type"]))
                sys.exit(6)
        message = self.communicator.create_message(SIGNAL_START, None)
        self.communicator.send(message)

    def get_addresses(self, totals):

        if self.simulator.node_count != len(self.communicator.connection_list):
            logger.error("Satellite Connection count mismatch")
            sys.exit(7)
        for index in range(len(totals)):
            message = self.communicator.create_single_message(
                    ADDRESS_REQUEST, self.communicator.connection_list[index],
                    (index, totals[index]))
            self.communicator.send(message)
        messages = self.communicator.receive()
        all_addresses = {}
        for message in messages:
            if message["type"] == ADDRESS_RESPONSE:
                node_id, addresses = message["payload"]
                all_addresses[node_id] = addresses
            else:
                logger.error(("Received unexpected "
                              "message type: {:}").format(message["type"]))
                sys.exit(6)
        return all_addresses

    def check_funds(self):
        # check balance in address against fee and token projection
        sys_have = self.syscoin.get_sys_balance()
        sys_need = self.simulator.get_gas_cost()
        sys_difference = sys_need - sys_have
        if sys_difference > 0:
            logger.error(("Not enough SYS in given address. {:.2f} more SYS "
                          "required.").format(sys_difference))
            sys.exit(4)
        tokens_have = self.syscoin.get_token_balance(self.args.addr)
        tokens_need = self.simulator.get_required_tokens()
        token_difference = tokens_need - tokens_have
        if token_difference > 0:
            logger.error(("Not enough tokens in given address. {:.2f} more "
                          "tokens required.").format(token_difference))
            sys.exit(5)

    def get_user_consent(self):
        # tell the user what's about to happen, how long it will take,
        # how much it will cost and ask for start/cancel confirmation
        reply = ask_user(("\nWe will be sending {:d} transactions, "
                          "using {:d} nodes, for a cost of approximately "
                          "{:f} SYS. This will take about {:d} minutes. "
                          "\nProceed?").format(self.simulator.get_tx_count(),
                                               self.simulator.get_node_count(),
                                               self.simulator.get_gas_cost(),
                                               self.simulator.get_duration()))
        if not reply:
            print("Ok, I'll not be doing anything. Have a nice day :)")
            sys.exit(0)
        else:
            print("Alright :)")
        return str(raw_input(("\nPlease enter a passwort to secure the "
                             "communication channels: ")))


class Satellite(StateMachine):
    def start(self):
        self.start_simulator()
        key = str(raw_input(("\nPlease enter a passwort to secure "
                             "the communication channels: ")))
        self.start_communicator(key)
        # wait for hub to ask for addresses
        self.get_addresses()
        self.get_pattern()
        self.wait_for_blocks(2)
        # self.check_funds() # TODO: check requirements of patterns, wait for confirmations
        self.report_ready()
        self.wait_for_start()
        self.start_pattern()
        self.send_success()
        self.send_report()
        self.syscoin.cleanup(self.simulator.hubAddress)

    def wait_for_blocks(self, count):
        blockheight = self.syscoin.get_blockheight() + count
        while (self.syscoin.get_blockheight() < blockheight):
            sleep(60)

    def get_pattern(self):
        message = self.communicator.receive()[0]
        if message["type"] == PATTERN:
            value, pattern = message["payload"]
            self.simulator.value = value
            self.simulator.set_pattern(pattern)
        else:
            logger.error(("Received unexpected "
                          "message type: {:}").format(message["type"]))
            sys.exit(6)

    def report_ready(self):
        message = self.communicator.create_message(SIGNAL_READY,
                                                   None)
        self.communicator.send(message)

    def wait_for_start(self):
        message = self.communicator.receive()[0]
        if not message["type"] == SIGNAL_START:
            logger.error(("Received unexpected "
                          "message type: {:}").format(message["type"]))
            sys.exit(6)

    def start_pattern(self):
        self.simulator.start()

    def send_success(self):
        message = self.communicator.create_message(SIGNAL_SUCCESS,
                                                   None)
        self.communicator.send(message)

    def send_report(self):
        message = self.communicator.create_message(REPORT,
                                                   self.simulator.report)
        self.communicator.send(message)

    def get_addresses(self):
        message = self.communicator.receive()[0]
        if message["type"] == ADDRESS_REQUEST:
            node_id, address_count = message["payload"]
            self.simulator.node_id = node_id
            addresses = self.syscoin.generate_addresses(address_count)
            message = self.communicator.create_message(ADDRESS_RESPONSE,
                                                       (node_id, addresses))
            self.communicator.send(message)
            return addresses
        else:
            logger.error(("Received unexpected "
                          "message type: {:}").format(message["type"]))
            sys.exit(6)
