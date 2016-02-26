structured clm testlist generator.

Generate a template configuration file:

    ./clm-testlist.py --write-template

Generate a test list from a configuration file:

    ./clm-testlist.py --test-suite-config clm-50.cfg


# Configuration file format

Each section of the configuration file is a different test suite.

Each section has a 'type' key that defines how it is processed.

- base : defineds a base simulation for perturbation suites

- single parameter perturbation : start with the base simulation and
  perturb it once for each item in each key.

- one off : a simple list of tests that are included as is The keys in
  each section correspond to the different parts of a cime test
  name:

    {test}.{grid}.{compset}.{machine}_{compiler}.{testmod}

The keys for "one off" are basically meaningless, and can be used for
grouping. The values are space delimited lists of fullly qualified
test names.

