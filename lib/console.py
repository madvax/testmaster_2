#!/usr/bin/python3

# Console Library 

import sys
import subprocess
import unittest

class Console():
   """ Console class """

   def __init__(self):
      """ Constructor for an object of type consol """
      self.PASSED  = "\033[32mPASSED\033[0m"  # \
      self.WARNING = "\033[33mWARNING\033[0m" #  \___ Linux-specific colorization
      self.FAILED  = "\033[31mFAILED\033[0m"  #  /
      self.ERROR   = "\033[31mERROR\033[0m"   # /

      self.command     = ""                      # The command to execute
      self._stdout     = subprocess.PIPE         # Standard Output PIPE
      self._stderr     = subprocess.PIPE         # Standard Error PIPE
      self.output      = "Command not executed"  # Output from command execution
      self.error       = "Command not executed"  # Error from command execution
      self.return_code = 127                     # Return code from command, default=127

   def write_message(self, message=""):
      """ Writes a message to standard out and flushes I/O the buffer. """
      sys.stdout.write("%s\n" %str(message))
      sys.stdout.flush()
      return None

   def write_warning(self, message=""):
      """ Writes a warning message to standard error and flushes I/O the buffer. """
      sys.stderr.write("%s -- %s\n" %(self.WARNING, str(message)))
      sys.stderr.flush()
      return None

   def write_error(self, message=""):
      """ Writes an error  message to standard error and flushes I/O the buffer. """
      sys.stdout.write("%s -- %s\n" %(self.ERROR, str(message)))
      sys.stderr.flush()
      return None

   def run(self, cmd=""):
      """ Executes a console command . """
      try:
         self.command = cmd
         results = subprocess.Popen(self.command            ,
                                    stdout   = self._stdout ,
                                    stderr   = self._stderr ,
                                    shell    = True         ,
                                    encoding = 'utf-8'      )
         self.output, self.error = results.communicate()  # Get output and error
         self.return_code = results.returncode            # Get Return Code
         self.output = self.output.strip() # \__ Clean up the output and error
         self.error  = self.error.strip()  # /
      except Exception as e:
         message = "Unable to execute: \"%s\"" % self.command
         self.write_error(message)
         # self.return_code = 127
      finally:
         return self.return_code   

   def write_results(self):
      """ Prints original command and resutls to stdout. """
      self.write_message("COMMAND     : \"%s\"" % self.command)
      self.write_message("OUTPUT      : \"%s\"" % self.output)
      self.write_message("ERROR       : \"%s\"" % self.error)
      self.write_message("RETURN CODE : %d"     % self.return_code)
      return None

   def return_results(self):
      """ Prints original command and resutls to stdout. """
      results = {"command"     : self.command     ,
                 "output"      : self.output      , 
                 "error"       : self.error       ,
                 "return_code" : self.return_code }
      return results


# Unit tests 
class UnitTests(unittest.TestCase):
   """ """
   def test_write_messages(self):
      """ """    
      test_string = "Test String"
      self.target = Console()    
      self.assertEqual(self.target.write_message(test_string), None)
      self.assertEqual(self.target.write_warning(test_string), None)
      self.assertEqual(self.target.write_error(test_string),   None)
      self.assertEqual(self.target.write_message([]), None)
      self.assertEqual(self.target.write_warning([]), None)
      self.assertEqual(self.target.write_error([]),   None)
      self.assertEqual(self.target.write_message({}), None)
      self.assertEqual(self.target.write_warning({}), None)
      self.assertEqual(self.target.write_error({}),   None)
      self.assertEqual(self.target.write_message(123), None)
      self.assertEqual(self.target.write_warning(123), None)
      self.assertEqual(self.target.write_error(123),   None)
      self.assertEqual(self.target.write_message(123.456), None)
      self.assertEqual(self.target.write_warning(123.456), None)
      self.assertEqual(self.target.write_error(123.456),   None)

   def test_good_command(self):
      """ """    
      self.target = Console()    
      command = "uname -a"
      self.assertEqual(self.target.run(command),                          0        )
      self.assertEqual(self.target.write_results(),                       None     )
      self.assertEqual(self.target.return_results()["command"],           command  )    
      self.assertEqual(type(self.target.return_results()),                type({}) )
      self.assertEqual(type(self.target.return_results()["command"]),     type("") )
      self.assertEqual(type(self.target.return_results()["output"]),      type("") )
      self.assertEqual(type(self.target.return_results()["error"]),       type("") )
      self.assertEqual(type(self.target.return_results()["return_code"]), type(0)  )
      
   def test_bad_command(self):
      """ """    
      self.target = Console()    
      command = "qwert"
      self.assertEqual(self.target.run(command),                          127      )
      self.assertEqual(self.target.write_results(),                       None     )
      self.assertEqual(self.target.return_results()["command"],           command  )  
      self.assertEqual(type(self.target.return_results()),                type({}) )
      self.assertEqual(type(self.target.return_results()["command"]),     type("") )
      self.assertEqual(type(self.target.return_results()["output"]),      type("") )
      self.assertGreater(len(self.target.return_results()["error"]),      0        )
      self.assertEqual(type(self.target.return_results()["return_code"]), type(0)  )
      
   def test_nonzero_command(self):
      """ """    
      self.target = Console()    
      command = "mv qwert qwerty"
      self.assertEqual(self.target.run(command),                          1        )
      self.assertEqual(self.target.write_results(),                       None     )
      self.assertEqual(self.target.return_results()["command"],           command  )     
      self.assertEqual(type(self.target.return_results()),                type({}) )
      self.assertEqual(type(self.target.return_results()["command"]),     type("") )
      self.assertEqual(type(self.target.return_results()["output"]),      type("") )
      self.assertGreater(len(self.target.return_results()["error"]),      0        )
      self.assertEqual(type(self.target.return_results()["return_code"]), type(0)  )


if __name__ == "__main__":
   # If this library is executed as a main program
   # Then execute the unit tests 
   unittest.main()