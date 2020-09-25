#!/usr/bin/python3

# The Test Master II Program 
# See the README and HELP files 
# -- Madvax, September 2020

# -----------------------------------------------------------------------------
# Standard Library Imports
import os
import sys
import time
from getopt import getopt
import logging
import selectors
import subprocess
import sys

# -----------------------------------------------------------------------------
# Some useful variables
VERSION        = "1.0.0"
APP_NAME       = "Test Master II"
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

# Test case states 
not_ready = "not ready" #  File not found or target not specified 
ready     = "ready"     # File exists and target is specified
running   = "running"   #  Test case is being execuited
passed    = "passed"    # Test case has finished without error or failed step
failed    = "failed"    # Test case failed one or more steps 
error     = "error"     # Test case encountered an error during execution  
test_case_states = [not_ready, ready, running, passed, failed, error]

# Initialize the logger
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()
logger.info("%s Started =======================================================" % ME)

# Set the python_interpreter value 
PYTHON_INTERPRETER = sys.executable
message = "Using Python interpreter %s" %PYTHON_INTERPRETER 
logger.info(message)

# Try to import PyQt5 
try:
   from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QFrame, QAction, qApp)
   from PyQt5.QtWidgets import (QGridLayout, QVBoxLayout, QHBoxLayout, QBoxLayout, QSplashScreen)
   from PyQt5.QtWidgets import (QLabel, QComboBox, QTabWidget, QTextEdit, QLineEdit, QDialogButtonBox)
   from PyQt5.QtWidgets import (QSlider, QDial, QScrollBar, QListWidget, QListWidgetItem)
   from PyQt5.QtWidgets import (QInputDialog, QLineEdit, QFileDialog, QDialog, QMessageBox)
   from PyQt5.QtGui import (QPixmap, QFont, QIcon, QStatusTipEvent, QColor,  QPalette, QTextCursor)
   from PyQt5.QtCore import (Qt, pyqtSignal, QSize, QUrl, QEvent)

except ModuleNotFoundError:
   sys.stderr.write("ERROR -- Unable to import the 'PyQt5' library\n")
   sys.stderr.write("         try: pip3 install pyqt5 --user\n")
   sys.stderr.flush()
   sys.exit(99)

# Import custom libraries 
sys.path.append(LIBRARY_PATH)
from config import read_config_file
from console import Console

# ============================================================================= Clickable Image 
# Create an object of type Image that is clickable. To do this we have to 
# create a generic QWidget and inherit from Qimage then add the click() method
# to that object.
class ClickableQLabel(QLabel):
   """ Extends the QLable object to make it clickable """

   def __init(self, parent):
      super().__init__(parent)
      clicked = pyqtSignal()
      rightClicked = pyqtSignal()

   def mousePressEvent(self, event):
      if event.button() == Qt.RightButton:
         self.rightClicked.emit()
      else:
         self.clicked.emit()

# ============================================================================= Clickable Icon
# Create an object of type Icon that is clickable. To do this we have to 
# create a generic QWidget and inherit from Qicon then add the click() method
# to that object.
class ClickableQIcon(QIcon):
   """ Extends the QIcon object to make it clickable """

   def __init(self, parent):
      super().__init__(parent)
      clicked = pyqtSignal()
      rightClicked = pyqtSignal()

   def mousePressEvent(self, event):
      if event.button() == Qt.RightButton:
         self.rightClicked.emit()
      else:
         self.clicked.emit()

# ============================================================================= Main Window
# Create the main window and inherit from the base class Qwidget
class MainWindow(QMainWindow):
   
   # -------------------------------------------------------------------------- __init__()
   def __init__(self, parent=None):
      """ Main Window Constructor 
          This is a special case constructor as we need an object of type 
          QMainWindow to supprt a menu bar at the top of the window and a 
          status bar at the bottom of the window. However this QMAinWindow 
          widget has issues with adding additoonal widgets to it. We need 
          to create a main_widget within this QMainWindow object that can 
          easily have its own layout and have its own widgets assigend to 
          it. This main_widget will inherit from the generic QWidget.      """  
      
      super(MainWindow, self).__init__(parent)

      # Create and assign a main_widget and main_layout for the main window 
      self.main_widget = QWidget(self)
      self.main_layout = QGridLayout(self.main_widget)
      self.setCentralWidget(self.main_widget)

      # Define the test targets available. Test targets are folders in the 
      # test cases folder that hold individula test cases. 
      self.update_list_of_test_targets()  
      self.loaded_test_suite  = ""
      # self.loaded_test_target = ""
      self.loaded_target = ""
      self.test_case_full_pathname_list = []
      self.test_case_results = []

      self.pass_color    = QColor(100, 255, 100) # light green 
      self.fail_color    = QColor(255, 100, 100) # light red 
      self.running_color = QColor(255, 255, 100) # light yellow

      self.ready_icon     = ClickableQIcon( os.path.join(RESOURCE_PATH, "ready.png"   ) )
      self.running_icon   = ClickableQIcon( os.path.join(RESOURCE_PATH, "running.jpg" ) )
      self.passed_icon    = ClickableQIcon( os.path.join(RESOURCE_PATH, "passed.png"  ) )
      self.failed_icon    = ClickableQIcon( os.path.join(RESOURCE_PATH, "failed.jpg"  ) )
      self.not_ready_icon = ClickableQIcon( os.path.join(RESOURCE_PATH, "no.png"      ) )
      self.running_icon   = ClickableQIcon( os.path.join(RESOURCE_PATH, "running.jpg" ) )
      self.open_icon      = ClickableQIcon( os.path.join(RESOURCE_PATH, "open.png"    ) )
      self.exit_icon      = ClickableQIcon( os.path.join(RESOURCE_PATH, "exit.png"    ) )
      self.about_icon     = ClickableQIcon( os.path.join(RESOURCE_PATH, "about.png"   ) )
      self.help_icon      = ClickableQIcon( os.path.join(RESOURCE_PATH, "help.png"    ) )
      self.target_icon    = ClickableQIcon( os.path.join(RESOURCE_PATH, "target.png"  ) )

      # Each test suite result will be stored in a data time stamped folder 
      # so we are going to need a string to hold that value. Each time the 
      # run_test_suite() method is called we will get an updated value for 
      # this date_time_string
      self.date_time_string = time.strftime("%Y%m%d%H%M%S", time.localtime())

      # --- Define the frames for the main window / central widget in the main window. 
      #     The frames are the large division of the windows in which widgets are placed. 
      #     Here is the intended frame layout for the MainWindow: 
      #    +-----------------------------------------+
      #    |         Status and Summary Frame        |
      #    |-----------------------------------------|
      #    |         Test        |                   | 
      #    |     Suite Frame     |       Test        |
      #    |---------------------+       Case        |
      #    |       Console       |       Frame       |
      #    |        Frame        |                   |
      #    |                     |                   |
      #    +-----------------------------------------+
      self.status_frame  = QFrame()   # status and summary frame 
      self.suite_frame   = QFrame()   # test suite frame 
      self.case_frame    = QFrame()   # test case frame
      self.console_frame = QFrame()   # console frame  
      self.status_frame.setFrameStyle(  QFrame.Panel | QFrame.Raised ) # \
      self.suite_frame.setFrameStyle(   QFrame.Panel | QFrame.Raised ) #  \__ set initial frame styles
      self.case_frame.setFrameStyle(    QFrame.Panel | QFrame.Raised ) #  / 
      self.console_frame.setFrameStyle( QFrame.Panel | QFrame.Raised ) # / 
      # --- Add the frames to the grid layout of the main window
      #     to the main window
      #                         (     Frame,          Row, Col, RSpan, CSpan, Allignment )  
      self.main_layout.addWidget(self.status_frame,     0,   0,     5,    12) #, Qt.AlignLeft    | Qt.AlignTop)
      self.main_layout.addWidget(self.suite_frame,     13,   0,     8,     6) #, Qt.AlignHCenter | Qt.AlignTop)
      self.main_layout.addWidget(self.case_frame,       6,   6,    15,     6)
      self.main_layout.addWidget(self.console_frame,    6,   0,     7,     6)
      
      # Set the main_layout as the main_wigit
      self.main_widget.setLayout(self.main_layout)

      # --- Define and set the status bar that appears at the bottom of the wondow
      # TODO: make this font a little smaller 
      self.status_bar = self.statusBar()                  # Status Bar appears on the bottom  
      self.status_bar.showMessage('No Test Suite Loaded') # of the main window

      # --- Menu Bar for the top of the main window
      print("call create_menu_bar()")
      self.create_menu_bar()

      # --- Main Window Geometry 
      self.setGeometry(100, 100, 1200, 800)

      # --- Create the About Dialog 
      self.about_dialog = QDialog()
      self.about_dialog.setWindowTitle("About Test Master II")
      about_layout = QGridLayout()
      title        = QLabel("Test Mster II")
      author       = QLabel("Madvax")
      email        = QLabel("madvax@madvax.com")
      about_layout.addWidget(QLabel("---------------") , 1, 1 , Qt.AlignCenter)
      about_layout.addWidget(title                     , 2, 1 , Qt.AlignCenter)
      about_layout.addWidget(author                    , 3, 1 , Qt.AlignCenter)
      about_layout.addWidget(email                     , 4, 1 , Qt.AlignCenter)
      about_layout.addWidget(QLabel("---------------") , 5, 1 , Qt.AlignCenter)
      self.about_dialog.setLayout(about_layout)

      # --- Create the Help Dialog
      #     The help text in this dialog is taken from the HELP file
      #     in the root folder for this repository
      self.help_dialog = QDialog()
      self.help_dialog.setWindowTitle("Help With Test Master II")
      help_layout = QGridLayout()
      help_text = QTextEdit()
      try:
         f = open(os.path.join(MY_PATH, "../HELP")   , 'r')
         text = f.read()
         f.close()
         help_text.setText(text)
      except:
         help_text.setText("Sorry, Unlable to locate help file")   
      help_text.setReadOnly(True)
      font = help_text.font()
      font.setFamily("Currier")
      font.setPointSize(10)
      help_layout.addWidget(help_text, 0,0)
      self.help_dialog.setLayout(help_layout)
      self.help_dialog.setGeometry(150,150, 500,500)

      # ----------------------------------------------------------------------- Status Frame Widgets 
      # --- Create and populate the product pull down with products  
      #     taken from the test cases folder
           
      # --- Logo Image that loads the About Window
      self.logo = QPixmap(  os.path.join(RESOURCE_PATH, "splash.jpg")   )
      self.logo.scaled(10, 10, Qt.KeepAspectRatio)
      self.logo_image = ClickableQLabel()
      self.logo_image.setScaledContents(True)
      self.logo_image.setPixmap(self.logo)
      self.logo_image.setMaximumWidth(80)
      self.logo_image.setMaximumHeight(100)

      # --- Suite and Target labels
      self.test_suite_label  = QLabel("Test Suite: None")
      self.test_target_label = QLabel("Test Target: None")

      # --- Generic spacer to help with alignemtns 
      self.spacer = QLabel("   ")
      # --- Status Frame Layout and widget placement 
      status_frame_layout = QGridLayout()
      status_frame_layout.addWidget(self.logo_image        , 0, 0, 3, 1, Qt.AlignLeft | Qt.AlignTop     )
      status_frame_layout.addWidget(self.test_suite_label  , 1, 1, 1, 1, Qt.AlignLeft | Qt.AlignVCenter )
      status_frame_layout.addWidget(self.test_target_label , 0, 1, 1, 1, Qt.AlignLeft | Qt.AlignVCenter )
      status_frame_layout.addWidget(self.spacer            , 0, 4, 1, 1, Qt.AlignLeft | Qt.AlignTop     ) 
      status_frame_layout.addWidget(self.spacer            , 0, 5, 1, 3, Qt.AlignLeft | Qt.AlignTop     ) 
      self.status_frame.setLayout(status_frame_layout) 

      # ----------------------------------------------------------------------- SUITE FRAME WIDGETS
      palette = QPalette()
      palette.setColor(  QPalette.Text,  QColor(  0, 75,   0)   ) # Very Dark  green text on a 
      palette.setColor(  QPalette.Base,  QColor(200, 255, 200)   ) # very light green background
      text_area_font = QFont("Courier", 15, QFont.Bold)
      self.suite_text_area = QTextEdit()
      self.suite_text_area.setPalette(palette)
      self.suite_text_area.setFont(text_area_font)
      suite_layout = QVBoxLayout()
      suite_layout.addWidget(self.suite_text_area)
      self.suite_frame.setLayout(suite_layout)
      self.suite_text_area.setText("No Test Suite Loaded")

      # ----------------------------------------------------------------------- CONSOLE FRAME WIDGETS
      palette = QPalette()
      palette.setColor(QPalette.Text, Qt.white) # White text on a 
      palette.setColor(QPalette.Base, Qt.black) # black background
      text_area_font = QFont("Courier", 15, QFont.Bold)
      self.console_text_area = QTextEdit()
      self.console_text_area.setPalette(palette)
      self.console_text_area.setFont(text_area_font)
      console_layout = QVBoxLayout()
      console_layout.addWidget(self.console_text_area)
      self.console_frame.setLayout(console_layout)
      self.console_text_area.setText("Console Area")

      # ----------------------------------------------------------------------- TEST CASE FRAME WIDGETS 
      self.testcase_list_widget = QListWidget()
      self.testcase_list_widget.setLineWidth(3)
      testcase_layout = QVBoxLayout()
      testcase_layout.addWidget(self.testcase_list_widget)
      self.case_frame.setLayout(testcase_layout)   

   # -------------------------------------------------------------------------- create_menu_bar()
   def create_menu_bar(self):
      """ """
      # --- Create the menu bar object
      print("Crate Menu Bar") 
      menu_bar = self.menuBar()

      # --- Define some actions for the menu bar 
      open_action = QAction(QIcon(os.path.join(MY_PATH, '../res/open.png')), '&Open Test Suite', self)
      open_action.setShortcut('Ctrl+O')
      open_action.setStatusTip('Open a Test Suite')
      open_action.triggered.connect( self.open_test_suite)
      # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
      exit_action = QAction(QIcon(os.path.join(MY_PATH, '../res/exit.png')), '&Exit', self)
      exit_action.setShortcut('Ctrl+Q')
      exit_action.setStatusTip('Exit application')
      exit_action.triggered.connect( qApp.quit)
      # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
      # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
      select_target_action = QAction(QIcon(os.path.join(MY_PATH, '../res/target.png')), '&Target', self)
      select_target_action.setShortcut('Ctrl+T')
      select_target_action.setStatusTip('Select test taget')
      select_target_action.triggered.connect( self.select_target)
      # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
      run_tests_action = QAction(QIcon(os.path.join(MY_PATH, '../res/run.png')), '&Run Test', self)
      run_tests_action.setShortcut('Ctrl+R')
      run_tests_action.setStatusTip('Run tests agains the target')
      run_tests_action.triggered.connect( self.run_test_suite)
      # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
      stop_tests_action = QAction(QIcon(os.path.join(MY_PATH, '../res/stop.png')), '&Stop Test', self)
      stop_tests_action.setShortcut('Ctrl+S')
      stop_tests_action.setStatusTip('Stops running tests')
      stop_tests_action.triggered.connect( self.open_test_suite)
      # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
      help_action = QAction(QIcon(os.path.join(MY_PATH, '../res/help.png')), '&Help', self)
      help_action.setShortcut('Ctrl+H')
      help_action.setStatusTip('Help')
      help_action.triggered.connect( self.open_help)
      # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
      about_action = QAction(QIcon(os.path.join(MY_PATH, '../res/about.png')), '&About', self)
      about_action.setShortcut('Ctrl+A')
      about_action.setStatusTip('About Test MAster II')
      about_action.triggered.connect( self.open_about)

      # Add actions to the menu bar 
      fileMenu = menu_bar.addMenu('&File')
      testMenu = menu_bar.addMenu('&Test')
      helpMenu = menu_bar.addMenu('&Help')
      # - - - - - - - - - - - - - - - - - - -
      fileMenu.addAction(open_action)    
      fileMenu.addAction(exit_action)
      # - - - - - - - - - - - - - - - - - - -
      testMenu.addAction(select_target_action)
      testMenu.addAction(run_tests_action)
      testMenu.addAction(stop_tests_action)
      # - - - - - - - - - - - - - - - - - - -
      helpMenu.addAction(help_action)
      helpMenu.addAction(about_action)

   # -------------------------------------------------------------------------- open_test_suite() 
   def open_test_suite(self):
      """ Open a test suite file and loads the test cases from the suite into the tool.
          There is a chained process flow when you open a test suite:
             open_test_suite() calls select_target() 
             select_target then calls load_test_cases() 
          Once a test suite is opened, the user may later choose a new target for the same 
          test suite as teh select_target() method call load_test_cases().      """ 
      
      self.test_case_data_list = []
      url = QUrl()                                    # This File Dialog should start in  
      url.setScheme("file")                           # the test suites folder by default. 
      url.setPath(   "%s/../testsuites" %MY_PATH   )  # TODO: os.path.join()
      options = QFileDialog.Options()
      options |= QFileDialog.DontUseNativeDialog
      file_dialog = QFileDialog()
      file_dialog.setDirectoryUrl(url)
      self.testsuite_file, _ = file_dialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*)", options=options)
      if self.testsuite_file:
         self.test_suite_label.setText("Test Suite: %s" %self.testsuite_file.split('/')[LAST])
         message = "Loaded Test Suite:  %s" %self.testsuite_file 
         logger.info(message)
         # Crate a list of test cases from the test suite file. However, these 
         # test cases are only file names with not path. We'll have to add the path 
         # based on the target selected.   
         try:
            f = open(self.testsuite_file, 'r')
            lines = f.readlines()
            f.close()
            self.suite_text_area.clear()
            for line in lines:
               line = line.strip()
               self.suite_text_area.append(line)
         except:
            message = "Unalbe to read test cases from test suite %s" %self.testsuite_file
            logger.error(message)
            self.suite_text_area.setText(message) 
            lines = []

         self.test_case_file_list = [] # a list of test case file names with no paths
         for line in lines:
            line = line.strip()
            if len(line) < 1:
               pass
            elif line.startswith('#'):
               pass
            else:
               self.test_case_file_list.append(line)     

         self.test_case_count = len(self.test_case_file_list)
         message = "Found %d test cases in %s" %(self.test_case_count, self.testsuite_file.split('/')[LAST])
         logger.info(message)
         self.status_bar.showMessage(message)  

         # open the select a test target for this suite
         self.select_target()  

         # load the test cases 
         # logger.info("Back from select_target() ... calling load_test_cases()")
         # self.load_test_cases()

   # -------------------------------------------------------------------------- load_test_cases()
   def load_test_cases(self):
      """ When we load the test cases from the test suite file we populate the 
          test case frame a.k.a. cases frame with the test cases. However, 
          before we put up the green run icon we have to ensure that a target 
          as been selected and using that target, verify that the test cases 
          requested in the test suite are available in the target folder.    """
      self.test_cases = []                # Start with an empty list of test cases 
      self.testcase_list_widget.clear()   # Clear any test cases from the test case frame 
      self.testcase_list_widget_items_list = []
      
      if len(self.test_case_file_list) > 0:
         
         counter = 0 
 
         for t in self.test_case_file_list:
 
            counter += 1
            logger.info("Loading test case %d of %d %s" %(counter, len(self.test_case_file_list), t) )

            # In this loop the variable t is the file name of a candidate test case 
            # without the path of the file. We will need to use the target to 
            # generate a ful path file name for the test case in this loop.
            # 
            # Create a list of test case data where each item in the list is a 
            # dictionary with two key-valie pairs: name an state. The name is 
            # the file name of the script as read from the test suite file and 
            # the state is one of: 
            #       "not ready" - File not found or target not specified 
            #       "ready"     - File exists and target is specified
            #       "running"   - Test case is being execuited
            #       "passed"    - Test case has finished without error or failed step
            #       "failed"    - Test case failed one or more steps 
            #       "error"     - Test case finished with and error, not the same as a failure 

            # Definethe full path of the candidate test case 
            test_case_path_filename = ""
            test_case_path_filename =  os.path.join(  os.path.join(TESTCASE_PATH, self.loaded_target), t  )
            message = "Test case full path %s" %(test_case_path_filename) 
            logger.info(message)

            test_case_record = {} # used to hold the data for a test case 

            # if the full path test case file exists then we mark it a ready
            # otherwise we mark it a not ready  
            if os.path.isfile( test_case_path_filename  ):
               test_case_record = {"name": t, "state":ready, "file": test_case_path_filename}   
               #                                                                 # \  ***    This is the list of    ***
               self.test_case_full_pathname_list.append(test_case_path_filename) #  > ***   executable test cases   ***
               #                                                                 # /  *** used for "run test suite" *** 
            else: 
               test_case_record = {"name": t, "state":not_ready, "file": None}   
             
            # define the icon for the test case based on the state of the test case 
            if test_case_record["state"] == ready:  
               test_case_icon = ClickableQIcon(  os.path.join(RESOURCE_PATH, "run.png")  )
            else:   
               test_case_icon = ClickableQIcon(  os.path.join(RESOURCE_PATH, "no.png")  )
            test_case_record["icon"] = test_case_icon

            # At this point the test case reacod is a dictionary with the key-value
            # paris listed below:
            # {"same": string, "state", string, "file": full_path_filename, "icon": ClickableIcon}
            # uisng this date we can create a QListItem and add it to the testcase_list_widget. 
            message = "Adding test case %s to the test case list widget" %test_case_record["name"]
            logger.info(message)
            list_item = QListWidgetItem()
            list_item.setText("Name: %s\nFile:%s\nState:%s" %(test_case_record["name"], test_case_record["file"], test_case_record["state"]))
            list_item.setIcon(test_case_record["icon"])
            self.testcase_list_widget.addItem(list_item)
            self.testcase_list_widget_items_list.append(list_item)
      else:
         message = "Failed to load any test cases from %s" %self.testsuite_file.split('/')[LAST] 
         logger.warning(message) 
         self.status_bar.showMessage(message)   
  
   # -------------------------------------------------------------------------- update_list_of_test_targets()
   def update_list_of_test_targets(self):
      """ update the list of test targets from the contents of the testcases folder """
      target_candidates = os.listdir(TESTCASE_PATH)
      self.target_list = [{"name":"Not selected",  "folder":"Not selected" }]
      for item in target_candidates:
         if os.path.isdir(  os.path.join(TESTCASE_PATH, item)   ):
            target = {}
            target["name"] = item
            target["folder"] = os.path.join(TESTCASE_PATH, item)
            self.target_list.append(target)
            logger.info("Added target %s to the list of targets" %item)  

   # -------------------------------------------------------------------------- select_target()
   def select_target(self):
      """ Select a target from teh list of available test targets """ 
      self.update_list_of_test_targets()
      targets = []
      for target in self.target_list[1:]:
         targets.append(target["name"])
      item, okPressed = QInputDialog.getItem(self, "Select Test Target","Target:", targets, 0, False)
      if okPressed and item:
         self.test_target_label.setText("Test Target: %s" %item)
         self.loaded_target = item
         logger.info("Loaded Test Target: %s" %item)   
         
         # load the test cases 
         logger.info("Back from select_target() ... calling load_test_cases()")
         self.load_test_cases()

   # -------------------------------------------------------------------------- run_test_suite()
   def run_test_suite(self):
      """ Execute all of the tests in a test suite. The list of executables is 
          stored in self.test_case_full_pathname_list. """ 
          
      if len(self.test_case_full_pathname_list) > 0:

         self.suite_results_folder = os.path.join(RESULTS_HOME, time.strftime("%Y%m%d%H%M%S", time.localtime())   )
         os.mkdir(self.suite_results_folder)
         message = "Created suite results folder %s" %self.suite_results_folder
         logger.info(message)

         # intiialize a list of dictionaries to store the results of this test suite run
         self.test_suite_results = []  

         # This is the main loop for executing test cases.
         # In this loop we create folders for the results 
         # of each test case and call/run each test cases
         # and provide the test cases results folder name 
         # as the last argument to the test case invocation
         # command. We also keep track of the test case 
         # results and store them in the test case list: 
         #  self.test_case_results   
         counter = 0
         for test_case in self.test_case_full_pathname_list:
         
            test_case_results = {}
            self.active_test_case = test_case
            self.active_test_case_results_folder = ""

            counter += 1  

            # Make the test case results folder
            test_case_short_name = test_case.split('/')[LAST]   
            if '.' in test_case_short_name:
               test_case_short_name = test_case_short_name.split('.')[FIRST]
            test_case_results_folder = os.path.join(self.suite_results_folder, test_case_short_name)
            os.mkdir(test_case_results_folder)
            self.active_test_case_results_folder = test_case_results_folder
            message = "Created test case resulst folder %s" %test_case_results_folder
            logger.info(message)

            # Identify and use the test case list widget item for this test case 
            list_item  = self.testcase_list_widget_items_list[counter - 1]
            bg_color   = self.running_color
            icon       = self.running_icon
            text       = "Test: %s\nFile: %s\nState: Running" %(test_case.split('/')[LAST], test_case, )
            self.set_test_case_list_wdiget_item(list_item, icon, bg_color, text )
            message = "Running Test case %d of %d: %s " %(counter, len(self.test_case_full_pathname_list), test_case)
            logger.info(message)
            self.status_bar.showMessage(message)

            self.repaint() # heavy sigh ...

            # *************************
            # *** RUN THE TEST CASE ***
            # *************************
            results = self.execute_test_case()
            if results["return_code"] == 0:
               list_item  = self.testcase_list_widget_items_list[counter - 1]
               bg_color   = self.pass_color
               icon       = self.passed_icon
               text       = "Test: %s\nFile: %s\nState: PASSED" %(test_case.split('/')[LAST], test_case, )
               self.set_test_case_list_wdiget_item(list_item, icon, bg_color, text )
               test_case_results = {"testcase"       : test_case_short_name, 
                                    "file"           : test_case, 
                                    "result"         : "passed", 
                                    "results_folder" : test_case_results_folder }
            else:
               list_item  = self.testcase_list_widget_items_list[counter - 1]
               bg_color   = self.fail_color
               icon       = self.failed_icon
               text       = "Test: %s\nFile: %s\nState: FAIILED" %(test_case.split('/')[LAST], test_case, )
               self.set_test_case_list_wdiget_item(list_item, icon, bg_color, text )
               test_case_results = {"testcase"       : test_case_short_name, 
                                    "file"           : test_case, 
                                    "result"         : "failed", 
                                    "results_folder" : test_case_results_folder }
            self.repaint()

            # Write the output and errors files to the test case results folder 
            # output  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            tc_output = results["output"]
            tc_output = tc_output.strip()
            if len(tc_output) < 1:
               pass
            else:
               output_file = os.path.join(test_case_results_folder, TC_OUTPUT_FILE) 
               try:
                  f = open(output_file, 'w')
                  f.write(tc_output)
                  f.close()
               except Exception as e:
                  message = "Ubnable to write to test case output file %s" %output_file
                  logger.error(message)
            # errors  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            tc_errors = results["error"]
            tc_errors = tc_errors.strip()
            if len(tc_errors) < 1:
               pass
            else:
               errors_file = os.path.join(test_case_results_folder, TC_ERRORS_FILE) 
               try:
                  f = open(errors_file, 'w')
                  f.write(tc_errors)
                  f.close()
               except Exception as e:
                  message = "Ubnable to write to test case errors file %s" %errors_file
                  logger.error(message)

            # Test Suite results can be used later in summary reports or general reporting   
            self.test_suite_results.append(test_case_results)

            message = "test case %d of %d complete" %(counter, len(self.test_case_full_pathname_list))
            self.status_bar.showMessage(message)
            logger.info(message)
            # Need a method for updateing all of the attributes of a list item 
         
         # Log the results
         logger.info("Test suite results:")
         logger.info(str(self.test_suite_results)) 

      else:
         message = "No test cases loaded. Nothing to do"
         logger.warning(message)
         mBox = QMessageBox()
         mBox.setText(message)
         mBox.setWindowTitle("Warning -- No test cases")
         mBox.setIcon(QMessageBox.Warning)
         mBox.setStandardButtons(QMessageBox.Ok)
         mBox.exec_()

   # -------------------------------------------------------------------------- set_test_case_list_wdiget_item()
   def set_test_case_list_wdiget_item(self, list_widget_item, icon , background_color, text ):
      """ sets the properties of a test cacse list widget item
             list_widget_item : test case list widget item 
             icon             : QIcon or ClickableIcon 
             background_color : Qt.QColor 
             text             : test for the list idget item  
          """
      list_widget_item.setText(text)
      list_widget_item.setBackground(background_color)
      list_widget_item.setIcon(icon)


   # -------------------------------------------------------------------------- open_about() 
   def open_about(self):
      """ """
      self.about_dialog.exec()

   # -------------------------------------------------------------------------- open_help() 
   def open_help(self):
      """ """
      self.help_dialog.exec()

   # -------------------------------------------------------------------------- execute_test_case()
   def execute_test_case(self):
      """ """

      # If the active test case is a python script then be sure to run it 
      # UNBUFFERED mode otehrwise just execute the active test case 
      if self.active_test_case.endswith('.py') or self.active_test_case.endswith('.Py') or self.active_test_case.endswith('.PY') :
         command_list = [PYTHON_INTERPRETER, "-u", self.active_test_case]
      else:
         command_list = [self.active_test_case]
      message = "RUNING:\n%s\n\nRESULTS IN:\n%s\n\n" %(self.active_test_case, self.active_test_case_results_folder)
      logger.info(message)   

      p = subprocess.Popen(command_list           , 
                           stdout=subprocess.PIPE ,
                           stderr=subprocess.PIPE )

      output_buffer  = ""
      error_buffer   = ""
      return_code    = 127

      sel = selectors.DefaultSelector()
      sel.register(p.stdout, selectors.EVENT_READ)
      sel.register(p.stderr, selectors.EVENT_READ)
      
      while p.poll() == None:
         for key, _ in sel.select():
            
            data = key.fileobj.read1().decode()
            if not data:
               break
            if key.fileobj is p.stdout:
               output_buffer += data             
            else:
               error_buffer += data   

            data = "%s" %str(data).strip()
            # text_buffer += data
            self.console_text_area.append(data)
            self.console_text_area.moveCursor(QTextCursor.End)
            self.repaint()   
   
      return {"return_code": p.poll()      ,
              "output"     : output_buffer ,
              "error"      : error_buffer  }   

   # -------------------------------------------------------------------------- event()
   def event(self, e):
      """ Manages the default text of the status bar """
      default_text = "By your command"
      if e.type() == QEvent.StatusTip:
         if e.tip() == '':
            e = QStatusTipEvent(default_text)  
      return super().event(e)

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