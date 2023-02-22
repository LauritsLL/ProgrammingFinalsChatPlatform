from random import randint
import hashlib
import Table

import database_manager as dm
from command import commands as c


#dict with the command the user can write as the key and the function it calls as the value

def main():
    dm.manager.setup()

    running = True
    while running:
        while not c.user:
            #while there are no user loggedin ask if the want to login or register
            l_r=input("login or register: ")
            l_r.replace(" ","").lower()
        
            if l_r == "register" or l_r == "r":
                #if they want to register get the
                #username
                username=input("username: ")
                #firstname
                firstname=input("firstname: ")
                #lastname
                lastname=input("lastname: ")
                #password
                password=input("password: ")
                # and confirm the password
                confirmpassword=input("confirmpassword: ")
                #check if its the same
                if confirmpassword==password:
                    #create a salt (a 10 digte number )
                    salt=str(randint(0,9999999999))
                    #add zeros at the begining 
                    salt="0"*(10-len(salt)) + salt
                    hashed=hashlib.sha256((password + salt).encode()).hexdigest()
                    #useses the create user function from the database manager 
                    c.user=dm.manager.registeruser(username,salt,hashed,firstname,lastname)
                    if not c.user:
                        print("Username already taken")
                

            elif l_r == "login" or l_r == "l":
                #if they want to login get
                username=input("username: ")
                password=input("password: ")
                salt=dm.manager.getsalt(username)
                if not salt:
                    print("Username or password is incorrect")
                    continue
                #calls the authenticate function in the database manager
                hashed=hashlib.sha256((password + salt).encode()).hexdigest()
                c.user=dm.manager.authenticate(username,hashed)
                if not c.user:
                    print("Username or password incorrect")
    
            elif l_r == "shutdown":
                #if they want to shutdown the program return out of the main function
                return
            else:
                print("try again")
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

