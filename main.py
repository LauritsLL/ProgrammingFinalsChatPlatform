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
        print(f"You are now loggedin as {c.user.get('username')} but this device is not authenticated for that user,before you can use this device you need to login on a already authenticated device and authenticated it")
        
        input("press enter to shutdown")

    
if __name__ == "__main__":
    main()

