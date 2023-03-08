from random import randint
import hashlib
import Table

import database_manager as dm
from command import commands as c

def main():
    dm.manager.setup()

    success = c.get_user_obj()
    if success: # Only if user object has been set.
        # Enter 'command mode'.
        try:
            with open(f'{c.user.get("id")}_private_key.pem', "rb") as key_file:
                pass
        except FileNotFoundError:
            #TODO the user does not have a private_key on this device add it
            privatekey = c.create_privatekey()
            c.send_publickey_to_database(privatekey.public_key())
            pass

        while c.user:
            command=input("Command: ")
            command = c.command_format(command)
            try:
                c.commands[command]()
            except KeyError:
                try:    
                    c.commands[c.user_shortcuts[command]]()
                except KeyError:
                    print("command not found.", "Use the command help for more info")

if __name__ == "__main__":
    main()

