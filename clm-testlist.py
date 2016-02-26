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
    from ConfigParser import Error as config_error
else:
    from configparser import ConfigParser as config_parser
    from configparser import Error as config_error

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
    """write a template configuration file.

    Each section of the configuration file is a different test suite.

    Each section has a 'type' key that defines how it is processed.

      - base : defineds a base simulation for perturbation suites

      - single parameter perturbation : start with the base simulation
        and perturb it once for each item in each key.

      - one off : a simple list of tests that are included as is

    The keys in each section correspond to the different parts of a
      cime test name:
      {test}.{grid}.{compset}.{machine}_{compiler}.{testmod}

    The keys for "one off" are basically meaningless, and can be used
    for grouping. The values are space delimited lists of fullly
    qualified test names.

    """
    template = config_parser()

    section = 'clm_base'
    template.add_section(section)
    template.set(section, 'type', '"base"')
    template.set(section, 'compset', 'string')
    template.set(section, 'grid', 'string')
    template.set(section, 'test', 'string')
    template.set(section, 'testmods', 'string')
    template.set(section, 'machine', 'string')
    template.set(section, 'compiler', 'string')

    section = 'clm_spp'
    template.add_section(section)
    template.set(section, 'type', '"single param perturbation"')
    template.set(section, 'compset', 'space separated list')
    template.set(section, 'grid', 'space separated list')
    template.set(section, 'test', 'space separated list')
    template.set(section, 'testmods', 'space separated list')
    template.set(section, 'machine', 'string')
    template.set(section, 'compiler', 'string')

    section = 'clm_long'
    template.add_section(section)
    template.set(section, 'type', '"one off"')
    template.set(section, 'tests', 'space separated list')

    with open('template.cfg', 'wb') as configfile:
        template.write(configfile)


# -------------------------------------------------------------------------------
#
# work functions
#
# -------------------------------------------------------------------------------
def process_test_config(config, file_base):
    """
    """
    base_def = None
    # search for a base section
    for s in config.sections():
        config_type = config.get(s, 'type').strip('"')
        if config_type == 'base':
            base_def = setup_base_simulation(config, s)
            removed = config.remove_section(s)

    for s in config.sections():
        testlist = []
        testlist.append(copy.deepcopy(base_def))
        config_type = config.get(s, 'type').strip('"')
        if config_type == 'single parameter perturbation':
            setup_single_parameter_perturbations(config, s, base_def, testlist)
        elif config_type == 'one off':
            setup_one_off(config, s, testlist)
        else:
            msg = "Section {0} has unknown type {1}".format(s, config_type)
            raise RuntimeError(msg)

        filename = '{0}.{1}.testlist.txt'.format(file_base, s)
        write_testlist(filename, testlist)


def setup_base_simulation(config, section):
    """
    """
    config.remove_option(section, 'type')
    test_def = {}
    for option in config.options(section):
        test_def[option] = config.get(section, option)

    base = test_template.safe_substitute(test_def)
    return test_def


def setup_single_parameter_perturbations(config, section, base_def, testlist):
    """
    """
    config.remove_option(section, 'type')
    machine = config.get(section, 'machine')
    config.remove_option(section, 'machine')
    compiler = config.get(section, 'compiler')
    config.remove_option(section, 'compiler')
    for option in config.options(section):
        items = config.get(section, option)
        items = items.split()
        for item in items:
            test_def = copy.deepcopy(base_def)
            test_def[option] = item
            test_def['machine'] = machine
            test_def['compiler'] = compiler
            # print(test_def)
            testlist.append(test_def)


def setup_one_off(config, section, testlist):
    """
    """
    config.remove_option(section, 'type')
    for option in config.options(section):
        items = config.get(section, option)
        items = items.split()
        for item in items:
            test_def = {}
            test_data = item.split('.')
            test_def['test'] = test_data[0]
            test_def['grid'] = test_data[1]
            test_def['compset'] = test_data[2]
            mach_comp = test_data[3].split('_')
            test_def['machine'] = mach_comp[0]
            test_def['compiler'] = mach_comp[1]
            test_def['testmods'] = test_data[4]
            # print(test_def)
            testlist.append(test_def)


def write_testlist(filename, testlist):
    """
    """
    print('Writing test list to: {0}'.format(filename))
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

    for filename in options.test_suite_config:
        try:
            # assume we are running in the same directory, strip off
            # the extension.
            file_base = filename.split('.')[0]
            config = read_config_file(filename)
            process_test_config(config, file_base)
        except config_error as e:
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
