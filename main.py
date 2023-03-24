import database_manager as dm
from command import commands as c

def main():
    dm.manager.setup()

    status = c.get_user_obj()
    if status == "Success!": # Only if user object has been set.
        # Enter 'command mode'.
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
    
    elif status == "Device not authenticated":
        print("LOGGED IN")
        print(f"You have now logged in successfully as {c.user.get('username')}. This device has yet to be authenticated by another device where this user is already authenticated. Please log in on your other device to confirm this device's authentication.") 
        input("Press Enter to shutdown...")

    
if __name__ == "__main__":
    main()

