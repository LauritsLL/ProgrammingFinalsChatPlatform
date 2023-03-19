import os
import datetime as dt
#import inspect # For getting code info from calling script
import sys # Works better
import ast

from rich import print

LOG_FILENAME = "DB_MANAGER_LOG.log"
RECURSION_STOPS = []
EXCLUSIONS = ["__init__", "execute_query", "execute_read_query"]

# Get all function names from command for stopping backwards frame recursion.
filename = "command.py"
with open(filename) as file:
    node = ast.parse(file.read())
classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
for class_ in classes:
    RECURSION_STOPS.extend([n.name for n in class_.body if isinstance(n, ast.FunctionDef)])
    RECURSION_STOPS = [item for item in RECURSION_STOPS if item not in EXCLUSIONS]

filename = "database_manager.py"
with open(filename) as file:
    node = ast.parse(file.read())
classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
for class_ in classes:
    RECURSION_STOPS.extend([n.name for n in class_.body if isinstance(n, ast.FunctionDef)])
    RECURSION_STOPS = [item for item in RECURSION_STOPS if item not in EXCLUSIONS]

class DbLog():
    """Log to log_file."""
    def __init__(self) -> None:
        self.log_file_path = os.path.join(os.getcwd(), LOG_FILENAME)
        self.debug_print = False
        self.write_to_file = True

    def log(self, *data, err=False, reason=None):
        """Log any data"""
        data = [str(d) for d in data]
        if self.debug_print:
            print(' '.join(data))
        if self.write_to_file:
            with open(self.log_file_path, 'a') as log:
                log.write(f"\nDB_MANAGER_LOG ({dt.datetime.now().strftime('%H:%M:%S %m/%d/%Y')}): "
                    + ("ERROR" if err else "") + "*" + ' '.join(data) + "* ")
                if reason:
                    # Get filename together with function name of calling script while recursively going through until recursion stop is hit.
                    frame = sys._getframe()
                    last_frame = frame
                    while not frame.f_code.co_name in RECURSION_STOPS and frame:
                        last_frame = frame
                        frame = frame.f_back
                    if not frame:
                        frame = last_frame
                    log.write(f"--> REASON '{reason}' | From file '{os.path.basename(frame.f_code.co_filename)}' in func '{frame.f_code.co_name}'")
