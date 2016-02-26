#!/usr/bin/env python
"""Tool to automate generation of the clm testlist.

Author: Ben Andre <andre@ucar.edu>

"""

from __future__ import print_function

import sys

if sys.hexversion < 0x02070000:
    print(70 * "*")
    print("ERROR: {0} requires python >= 2.7.x. ".format(sys.argv[0]))
    print("It appears that you are running python {0}".format(
        ".".join(str(x) for x in sys.version_info[0:3])))
    print(70 * "*")
    sys.exit(1)

#
# built-in modules
#
import argparse
import copy
import os
from string import Template
import traceback

if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser as config_parser
else:
    from configparser import ConfigParser as config_parser

#
# installed dependencies
#

#
# other modules in this package
#

#
# templates
#
test_template = Template('${test}.${grid}.${compset}.${machine}_${compiler}.${testmods}')

# -------------------------------------------------------------------------------
#
# User input
#
# -------------------------------------------------------------------------------

def commandline_options():
    """Process the command line arguments.

    """
    parser = argparse.ArgumentParser(
        description='Tool to automate generation of the clm testlist.')

    parser.add_argument('--backtrace', action='store_true',
                        help='show exception backtraces as extra debugging '
                        'output')

    parser.add_argument('--debug', action='store_true',
                        help='extra debugging output')

    parser.add_argument('--test-suite-config', nargs='+',
                        help='name of config file(s) defining a test suite')

    parser.add_argument('--write-template', action='store_true',
                        help='write a template input configuration file')

    options = parser.parse_args()
    return options


def read_config_file(filename):
    """Read the configuration file and process

    """
    print("Reading configuration file : {0}".format(filename))

    cfg_file = os.path.abspath(filename)
    if not os.path.isfile(cfg_file):
        raise RuntimeError("Could not find config file: {0}".format(cfg_file))

    config = config_parser()
    config.read(cfg_file)

    return config


def write_template_config():
    """write a template configuration file
    """
    template = config_parser()

    section = 'base'
    template.add_section(section)
    template.set(section, 'compset', 'string')
    template.set(section, 'grid', 'string')
    template.set(section, 'test', 'string')
    template.set(section, 'testmods', 'string')

    section = 'single_param_perturbation'
    template.add_section(section)
    template.set(section, 'compset', 'space separated list')
    template.set(section, 'grid', 'space separated list')
    template.set(section, 'test', 'space separated list')
    template.set(section, 'testmods', 'space separated list')

    with open('template.cfg', 'wb') as configfile:
        template.write(configfile)

# -------------------------------------------------------------------------------
#
# work functions
#
# -------------------------------------------------------------------------------
def setup_base_simulation(config):
    """
    """
    section = 'base'
    test_def = {}
    test_def['test'] = config.get(section, 'test')
    test_def['grid'] = config.get(section, 'grid')
    test_def['compset'] = config.get(section, 'compset')
    test_def['testmods'] = config.get(section, 'testmods')
    test_def['machine'] = 'any'
    test_def['compiler'] = 'any'

    base = test_template.safe_substitute(test_def)
    print("base test : {0}".format(base))
    return test_def


def setup_single_parameter_perturbations(config, base_def, testlist):
    """
    """
    section = 'single_param_perturbation'
    for option in config.options(section):
        items = config.get(section, option)
        items = items.split()
        for item in items:
            test_def = copy.deepcopy(base_def)
            test_def[option] = item
            #print(test_def)
            testlist.append(test_def)


def write_testlist(filename, testlist):
    """
    """
    with open(filename, 'w') as output:
        for t in testlist:
            output.write("{0}\n".format(test_template.safe_substitute(t)))

            
# -------------------------------------------------------------------------------
#
# main
#
# -------------------------------------------------------------------------------

def main(options):
    if options.write_template:
        write_template_config()
        return 0

    for config_file in options.test_suite_config:
        testlist = []
        config = read_config_file(config_file)
        try:
            base_def = setup_base_simulation(config)
            testlist.append(copy.deepcopy(base_def))
            setup_single_parameter_perturbations(config, base_def, testlist)
            filename = config_file.split('.')[0]
            filename = '{0}.testlist.txt'.format(filename)
            write_testlist(filename, testlist)

        except ConfigParser.Error as e:
            print(e)
            return 1
    return 0


if __name__ == "__main__":
    options = commandline_options()
    try:
        status = main(options)
        sys.exit(status)
    except Exception as error:
        print(str(error))
        if options.backtrace:
            traceback.print_exc()
        sys.exit(1)
