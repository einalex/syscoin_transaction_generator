#! /usr/bin/env python3

import sys
import argparse
from stg.state_machine import StateMachine
from stg.syscoin import Syscoin
from stg.logger import logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='sbt', usage='%(prog)s [options]',
                                     description=('A utility to create'
                                                  'rudimentary transaction'
                                                  'patterns on the Syscoin'
                                                  'network.'))
    parser.add_argument(
        '--addr', default="sys1qhxfg49a08pw3nth8558vz7vuq64trzuntw6fqj",
        help='Funding address')
    parser.add_argument('--pattern', default="pattern.json",
                        help='path to JSON file containing traffic pattern')
    parser.add_argument('--token', default="1533716253", help='Token ID')
    parser.add_argument('--value', default=1,
                        help='Average transaction value')
    parser.add_argument('--sat', default=[],
                        help='List of satellite system IPs')
    parser.add_argument('--port', default=9999, help='The port to use')
    parser.add_argument('--fee', default=0.0001,
                        help='Transaction fee per kilobyte')
    parser.add_argument('--prefund', default=False, action="store_true",
                        help='Distribute coins')
    parser.add_argument('--addrfile', default="main-addr.json",
                        help='File containing addresses')

    args = parser.parse_args()
    # account for argparse inability to create a list of strings
    args.sat = args.sat if isinstance(args.sat, list) else args.sat.split(",")

    try:
        syscoin = Syscoin(args.token)
    except Exception as err:
        logger.error(err)
        logger.error(("Could not connect to syscoind. "
                      "Make sure syscoin is running and "
                      "this user has access to the rpc port."))
        sys.exit(2)
    state_machine = StateMachine(syscoin, args)
    state_machine.start()
