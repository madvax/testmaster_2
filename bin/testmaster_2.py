#!/usr/bin/python3

import logging
# -----------------------------------------------------------------------------
# Standard Library Imports
import os
import sys
import time
from getopt import getopt
import logging

# -----------------------------------------------------------------------------
# Some useful variables
VERSION        = "1.0.0"
VERBOSE        = True
DEBUG          = False
FIRST          = 0
LAST           = -1
ME             = os.path.split(sys.argv[FIRST])[LAST]  # Name of this file
MY_PATH        = os.path.dirname(os.path.realpath(__file__))  # Path for this file
LIBRARY_PATH   = os.path.join(MY_PATH, "../lib")
LOG_PATH       = os.path.join(MY_PATH, "../log")
LOG_FILE       = os.path.join(LOG_PATH, "%s.log" % ME.split('.')[FIRST])  # testmaster.log
LOG_FORMAT     = "%(asctime)s, %(levelname)s, %(message)s"
TESTSUITE_PATH = os.path.join(MY_PATH, "../testsuites")
TESTCASE_PATH  = os.path.join(MY_PATH, "../testcases")
RESULTS_HOME   = os.path.join(MY_PATH, "../testresults")
CONFIG_PATH    = os.path.join(MY_PATH, "../conf")
CONFIG_FILE    = os.path.join(CONFIG_PATH,  "%s.conf" % ME.split('.')[FIRST]) # testmaster.cong
RESOURCE_PATH  = os.path.join(MY_PATH, "../res")
TC_OUTPUT_FILE = "output.txt"
TC_ERRORS_FILE = "errors.txt"
PASSED         = "\033[32mPASSED\033[0m"  # \
WARNING        = "\033[33mWARNING\033[0m" #  \___ Linux-specific colorization
FAILED         = "\033[31mFAILED\033[0m"  #  /
ERROR          = "\033[31mERROR\033[0m"   # /

# Initialize the logger
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()
logger.info("%s Started =======================================================" % ME)



# Try to import PyQt5 
try:
   from PyQt5.QtWidgets import (QApplication, QWidget)
   from PyQt5.QtWidgets import (QGridLayout, QVBoxLayout, QHBoxLayout, QBoxLayout, QSplashScreen)
   from PyQt5.QtWidgets import (QLabel, QComboBox, QTabWidget, QTextEdit, QLineEdit)
   from PyQt5.QtWidgets import (QSlider, QDial, QScrollBar, QListWidget, QListWidgetItem)
   from PyQt5.QtGui import (QPixmap, QFont, QIcon)
   from PyQt5.QtCore import (Qt, pyqtSignal, QSize)

except ModuleNotFoundError:
   sys.stderr.write("ERROR -- Unable to import the 'PyQt5' library\n")
   sys.stderr.write("         try: pip3 install pyqt5 --user\n")
   sys.stderr.flush()
   sys.exit(99)

# Import custom libraries 
sys.path.append(LIBRARY_PATH)
from config import read_config_file



# Create the main window and inherit from the base class Qwidget
class MainWindow(QWidget):
   
   def __init__(self):
      """ Main Window Constructor """  
      super().__init__()







# === MAIN ====================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Splash screen 
    pixmap = QPixmap(os.path.join(RESOURCE_PATH,  "splash.jpg"))
    splash = QSplashScreen(pixmap)
    splash.show()
    splash.showMessage("Loading configs  ... ")
    # Import custom libraries 
    sys.path.append(LIBRARY_PATH)
    from config import read_config_file
    from console import Console
    c = Console()
    configs = read_config_file(CONFIG_FILE)
    if len(configs) > 0:
       logger.info("Read %d configs from %s" %(len(configs), CONFIG_FILE )) 
    else: 
       message = "No configs read from %s" %CONFIG_FILE
       c.write_warning(message)
       logger.warning(message)
    # app.processEvents() 


    # Show the main window and close the splash screen 
    windowMain = MainWindow()
    splash.finish(windowMain)
    windowMain.show()

    # Application executions and clean exit 
    sys.exit(app.exec_())