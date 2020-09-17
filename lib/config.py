#!/usr/bin/python3

# This library holds functions that allow scripts to read encrypted configuration
# files. To run unit tests for this library execute this library as main from the
# command line.

import os
import sys
import unittest

# -----------------------------------------------------------------------------
# Some useful variables
VERSION  = "1.0.2"
VERBOSE  = False
DEBUG    = False
FIRST    = 0
LAST     = -1
ME       = os.path.split(sys.argv[FIRST])[LAST]  # Name of this file
MY_PATH  = os.path.dirname(os.path.realpath(__file__))  # Path for this file
PASSED   = "\033[32mPASSED\033[0m"  # \
FAILED   = "\033[31mFAILED\033[0m"  #  > Linux-specific colorization
ERROR    = "\033[31mERROR\033[0m"   # /

def read_config_file(file_name, delimiter=' '):
   """ Reads a config file and returns a dictionary of key/value pairs from
       the configuration file. If anything goes wrong then return an
       empty dictionary. Any errors are sent to standard error """
   configurations = {}
   config_data    = []
   try:
      f = open(file_name, 'r')
      config_data = f.readlines()
      f.close()

      for line in config_data:
         line = line.strip()  # Clean up leading and trailing whitespace
         if len(line) < 1:
            pass  # Skip blank lines
         elif line[FIRST] == '#':
            pass  # Skip comment lines
         elif line.find(delimiter) == -1:
            pass  # Skip mal-formed lines (lines without an equal sign character'=')
         else:
            # Process remaining lines
            line                = line.strip()  # Clean up the whitespace
            key                 = line.split(delimiter, 1)[FIRST].strip()
            value               = line.split(delimiter, 1)[LAST].strip()
            configurations[key] = value
   except Exception as e:
        sys.stderr.write("%s -- Unable to read from configurations file %s\n" % (ERROR, file_name))
        print(str(e))
        configurations = {}  # Trust no one. If there was a problem then flush the data
   finally:
      return configurations


# Unit tests
class UnitTests(unittest.TestCase):
   """ """
   def test_known_good_call(self):
      config_file = "../conf/testmaster.conf"
      configs = read_config_file(config_file)
      self.assertEqual(configs['test1'], "Value 1")
      self.assertEqual(configs['test2'], "Value 2")


   def test_known_bad_call(self):
      config_file = "qwert"
      configs = read_config_file(config_file)
      self.assertEqual(configs, {})


if __name__ == "__main__":
   # If this library is executed as a main program
   # Then execute the unit tests 
   unittest.main()
