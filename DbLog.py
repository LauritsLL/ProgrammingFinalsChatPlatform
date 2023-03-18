import os
import datetime as dt
import inspect # For getting filename from calling script
import sys

from rich import print

LOG_FILENAME = "DB_MANAGER_LOG.log"

class DbLog():
    """Log to log_file."""
    def __init__(self) -> None:
        self.log_file_path = os.path.join(os.getcwd(), LOG_FILENAME)
        self.debug_print = False
        self.write_to_file = True

    def log(self, *data, err=False, reason="UNSPECIFIED"):
        """Log any data"""
        data = [str(d) for d in data]
        if self.debug_print:
            print(' '.join(data))
        if self.write_to_file:
            with open(self.log_file_path, 'a') as log:
                log.write(f"\nDB_MANAGER_LOG ({dt.datetime.now().strftime('%H:%M:%S %m/%d/%Y')}): "
                    + ("ERROR" if err else "") + ' '.join(data))
                log.write(f"\n--> REASON '{reason}' | From file '{os.path.basename(sys._getframe().f_back.f_back.f_code.co_filename)}' in func '{sys._getframe().f_back.f_back.f_code.co_name}'")
