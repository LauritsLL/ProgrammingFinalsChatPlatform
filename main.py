import database_manager as dm
from command import commands as c
import sys

def main():
    dm.manager.setup()
    while True:
        success,encryption_success = c.get_user_obj()
        if success and encryption_success:
            print("You can write 'help' to show all commands")
        while c.user:
            if encryption_success: # Only if user object has been set.
                # Enter 'command mode'.
                command=input("Command: ")
                command = c.command_format(command)
                try:
                    s = c.commands[command]()
                    if not s is None:
                        if s[0] == "logout":
                            success = s[1]
                            encryption_success = s[2]
                except KeyError:
                    try:    
                        s = c.commands[c.user_shortcuts[command]]()
                        if not s is None:
                            if s[0] == "logout":
                                success = s[1]
                                encryption_success = s[2]
                    except KeyError:
                        print("Command not found. Use the command 'help' for more info.")
            else: 
                if success:
                    print("LOGGED IN")
                    print(f"You have now logged in successfully as {c.user.get('username')}. This device has yet to be authenticated by another device where this user is already authenticated. Please log in on your other device to confirm this device's authentication.") 
                    input("Press Enter to shutdown...")
                    sys.exit(0)
        success, encryption_success = c.get_user_obj() 

    
if __name__ == "__main__":
    main()

