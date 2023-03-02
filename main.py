from random import randint
import hashlib
import Table

import database_manager as dm
from command import commands as c

def main():
    dm.manager.setup()

    running = True
    while running:
        while not c.user:
            #while there are no user loggedin ask if the want to login or register
            l_r=input("login or register: ")
            l_r = c.command_format(l_r)
        
            if l_r == "register" or l_r == "r":
                c.register()
            elif l_r == "login" or l_r == "l":
                c.login()
            elif l_r == "shutdown":
                #if they want to shutdown the program return out of the main function
                return
            else:
                print("try again")
        
        # Enter 'command mode'.
        command=input("command: ")
        command = c.command_format(command)
        try:
            c.commands[command]()
        except KeyError:
            try: 
                c.commands[c.shortcuts[command]]()
            except KeyError:
                print("command not found.", "Use the command help for more info")
                

if __name__ == "__main__":
    main()

