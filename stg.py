#! /bin/env python

import argparse
import sys

from stg.communication import Communicator
from stg.syscoin import Syscoin
from stg.simulator import Simulator
from stg.logger import logger



# account for python2/3 difference
if not "raw_input" in dir():
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='sbt', usage='%(prog)s [options]', description='A utility to create rudimentary transaction patterns on the Syscoin network.')
    parser.add_argument('--addr', default = "baddecaf", help='Funding address')
    parser.add_argument('--token', default = "deadbeef", help='Token ID')
    parser.add_argument('--value', default = 42, help='Average transaction value')
    parser.add_argument('--nf', default = 0.03, help='Normal frequency [1/s]')
    parser.add_argument('--pf', default = 0.03, help='Peak frequency [1/s]')
    parser.add_argument('--pd', default = 2, help='Normal duration [min]')
    parser.add_argument('--nd', default = 2, help='Peak duration [min]')
    parser.add_argument('--sat', default = [], help='List of satellite system IPs')
    parser.add_argument('--port', default = 9999, help='The port to use')
    parser.add_argument('--fee', default = 0.0001, help='Transaction fee per kilobyte')

    args = parser.parse_args()
    # account for argparse inability to create a list of strings
    args.sat = args.sat if isinstance(args.sat, list) else [args.sat]

    if args.sat:
        logger.info("Starting as the Hub node")
    else:
        logger.info("Starting as a satellite node")


    # calculate required sys fees and token balances
    if args.sat:
        try:
            simulator = Simulator(args.value, len(args.sat), args.nf, args.nd*60, args.pf, args.pd*60, args.fee)
        except Exception as err:
            logger.error(err)
            sys.exit(1)

        # tell the user what's about to happen, how long it will take, how much it will cost and ask for start/cancel confirmation
        reply = ask_user("\nWe will be sending {:d} transactions, using {:d} nodes, for a cost of approximately {:f} SYS. This will take about {:d} minutes.\nProceed?".format(simulator.get_tx_count(), simulator.get_node_count(), simulator.get_gas_cost(), simulator.get_duration()))
        if not reply:
            print("Ok, I'll not be doing anything. Have a nice day :)")
            sys.exit(0)
        else:
            print("Alright :)")

    key = str(raw_input("\nPlease enter a passwort to secure the communication channels: "))
    # --- on central system:
    # TODO: connect to local syscoind
    try:
        syscoin = Syscoin()
    except Exception as err:
        logger.error(err)
        logger.error("Could not connect to syscoind. Make sure syscoin is running and this user has access to the rpc port.")
        sys.exit(2)
    # TODO: check connection to satellite systems

    # try:
    communicator = Communicator(args.sat, args.port, key)
    # except Exception as err:
    #     logger.error(err)
    #     logger.error("Could not connect to other sbt processes. Make sure they are running and can be reached.")
    #     sys.exit(3)


    # TODO: check balance in address against fee and token projection
    if args.addr:
        sys_have = syscoin.get_sys_balance(args.addr)
        sys_need = simulator.get_gas_cost()
        sys_difference = sys_need - sys_have
        if sys_difference > 0:
            logger.error("Not enough SYS in given address. {:.2f} more SYS required.".format(sys_difference))
            sys.exit(4)
        tokens_have = syscoin.get_token_balance(args.addr, args.token)
        tokens_need = simulator.get_required_tokens()
        token_difference = tokens_need - tokens_have
        if token_difference > 0:
            logger.error("Not enough tokens in given address. {:.2f} more tokens required.".format(token_difference))
            sys.exit(5)





    # TODO: ask satellite systems for addresses
    if args.sat:
        simulator.
        communicator.get_addresses()

    # --- on satellite system:
    # TODO: connect to local syscoind
    # TODO: create required addresses

    # --- on central system:
    # TODO: send tokens and fees to satellite system addresses
    # TODO: calculate normal and peak usage patterns
    # TODO: tell satellite systems about patterns

    # --- on satellite system:
    # TODO: check requirements of patterns,
    # TODO: create new addresses according to pattern requirements
    # TODO: distribute tokens among generated addresses
    # TODO: wait for confirmation
    # TODO: report ready state to central system

    # --- on central system:
    # TODO: wait for satellite systems' ready state
    # TODO: give start signal for first phase to satellite systems

    # --- on satellite system:
    # TODO: execute first normal pattern
    # TODO: report success to central system

    # --- on central system:
    # TODO: wait for satellite systems' success messages
    # TODO: give start signal for next phase to satellite systems

    # --- on satellite system:
    # TODO: execute peak pattern
    # TODO: report success to central system

    # --- on central system:
    # TODO: wait for satellite systems' success messages
    # TODO: give start signal for next phase to satellite systems

    # --- on satellite system:
    # TODO: execute second normal pattern
    # TODO: report success to central system
    # TODO: send tokens and sys back to central system
    # TODO: send action report to central system
    # TODO: exit program

    # --- on central system:
    # TODO: wait for satellite systems' success messages
    # TODO: wait for tokens and coins to return
    # TODO: report finished test to user
    # TODO: write logfile
    # TODO: exit program

    # parse parameter:
    # initial address
    # token uid - default:
    # avg tx token value - default:
    # tx bandwidth normal - default:
    # tx bandwidth peak - default:
    # duration of peak - default:
    # duration of experiment - default:

    #---------------------
