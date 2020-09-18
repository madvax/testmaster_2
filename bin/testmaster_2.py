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

# Initialize the logger
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()
logger.info("%s Started =======================================================" % ME)

# Try to import PyQt5 
try:
   from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QFrame, QAction, qApp)
   from PyQt5.QtWidgets import (QGridLayout, QVBoxLayout, QHBoxLayout, QBoxLayout, QSplashScreen)
   from PyQt5.QtWidgets import (QLabel, QComboBox, QTabWidget, QTextEdit, QLineEdit, QDialogButtonBox)
   from PyQt5.QtWidgets import (QSlider, QDial, QScrollBar, QListWidget, QListWidgetItem)
   from PyQt5.QtWidgets import (QInputDialog, QLineEdit, QFileDialog, QDialog)
   from PyQt5.QtGui import (QPixmap, QFont, QIcon, QStatusTipEvent)
   from PyQt5.QtCore import (Qt, pyqtSignal, QSize, QUrl, QEvent)

except ModuleNotFoundError:
   sys.stderr.write("ERROR -- Unable to import the 'PyQt5' library\n")
   sys.stderr.write("         try: pip3 install pyqt5 --user\n")
   sys.stderr.flush()
   sys.exit(99)

# Import custom libraries 
sys.path.append(LIBRARY_PATH)
from config import read_config_file



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

      # Create and assign a main_widget and main layout
      self.main_widget = QWidget(self)
      self.main_layout = QGridLayout(self.main_widget)
      self.setCentralWidget(self.main_widget)

      # Define the test targets available. Test targets are folders in the 
      # test cases folder that hold individula test cases. 
      self.update_list_of_test_targets()  
      self.loaded_test_suite  = ""
      self.loaded_test_target = ""





      # --- Define the frames for the main/central widget in the main window. The 
      #     frames are the large division of the windows in which widgets are placed. 
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
      self.main_layout.addWidget(self.suite_frame,      6,   0,     7,     6) #, Qt.AlignHCenter | Qt.AlignTop)
      self.main_layout.addWidget(self.case_frame,       6,   6,    15,     6)
      self.main_layout.addWidget(self.console_frame,   13,   0,     8,     6)
      
      # Set the main_layout as the main_wigit
      self.main_widget.setLayout(self.main_layout)

      # --- Define and set the status bar that appears at the bottom of the wondow
      # TODO: make this font a little smaller 
      self.status_bar = self.statusBar()                  # Status Bar appears on the bottom  
      self.status_bar.showMessage('No Test Suite Loaded') # of the main window

      # --- Menu Bar for the top of the main window
      print("call create_menu_bar()")
      self.create_menu_bar()

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
      self.test_suite_label = QLabel("Test Suite: None")
      self.test_target_label = QLabel("Test Target: None")

      # --- Generic spacer to help with alignemtns 
      self.spacer = QLabel("   ")
      # --- Status Frame Layout and widget placement 
      status_frame_layout = QGridLayout()
      status_frame_layout.addWidget(self.logo_image        , 0, 0, 3, 1, Qt.AlignLeft | Qt.AlignTop     )
      status_frame_layout.addWidget(self.test_suite_label  , 0, 1, 1, 1, Qt.AlignLeft | Qt.AlignVCenter )
      status_frame_layout.addWidget(self.test_target_label , 1, 1, 1, 1, Qt.AlignLeft | Qt.AlignVCenter )
      status_frame_layout.addWidget(self.spacer            , 0, 4, 1, 1, Qt.AlignLeft | Qt.AlignTop     ) 
      status_frame_layout.addWidget(self.spacer            , 0, 5, 1, 3, Qt.AlignLeft | Qt.AlignTop     ) 


      self.status_frame.setLayout(status_frame_layout) 


      # --- Main Window Geometry 
      self.setGeometry(100, 100, 1200, 800)

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
      run_tests_action.triggered.connect( self.open_test_suite)
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
      """ Open a test suite file and load the test cases from the suite into the tool. """ 
      
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
         self.load_test_cases()

   # -------------------------------------------------------------------------- load_test_cases()
   def load_test_cases(self):
      """ """
      self.test_cases = []
      f = open(self.testsuite_file, 'r')
      lines = f.readlines()
      f.close()
      for line in lines:                  # Build the list of test cases to execute. 
         line = line.strip()              # Skip any lines in the test suite that 
         if line == '':                   # are either blank lines or comment lines
            pass                          # that start with a pound sign '#'.   
         elif line.startswith('#'):       #
            pass                          #
         else:                            #
            self.test_cases.append(line)  #             
      if len(self.test_cases) > 0:
         self.test_case_count = len(self.test_cases)
         message = "Loaded %d test cases from %s" %(self.test_case_count, self.testsuite_file.split('/')[LAST])
         self.status_bar.showMessage(message)  
         print(self.test_cases)  
      else:
         message = "Failed to load any test cases from %s" %self.testsuite_file.split('/')[LAST]  
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

   # -------------------------------------------------------------------------- open_about() 
   def open_about(self):
      """ """
      self.about_dialog.exec()

   # -------------------------------------------------------------------------- open_help() 
   def open_help(self):
      """ """
      self.help_dialog.exec()



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