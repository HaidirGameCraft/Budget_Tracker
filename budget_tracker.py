import hashlib
import sys 
import pathlib
from datetime import datetime
import json
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

UserName = ""
Password = None
hashFileName = None
act_user_data = None
data_folder = pathlib.Path("data/")

# Encrypt/Descript File
fernet = None

def main():

    # Creating data folder if not exists
    if not data_folder.exists():
        data_folder.mkdir()


    print("======== Budget Tracker ========")
    print(f"{UserName}> ", end="", flush=True)
    for lines in sys.stdin:
        line = lines.split()
        if len(line) > 0 and ( line[0].lower() == 'quit' or line[0].lower() == 'exit' ):
            log_out()
            print("======== Thank You for using this Apps ========")
            break
        analyze_and_run_command( lines.split() )
        print(f"{UserName}> ", end="", flush=True)


def analyze_and_run_command( lines ):
    global hashFileName
    global Password
    global fernet
    global UserName
    global act_user_data
    
    if len(lines) == 0:
        return
    first_command = lines[0]
    if first_command.lower() == "login":
        # Login an account
        if len(lines) == 2 and lines[1] == 'create':
            # Create an account
            user_name = input("User Name: ")
            password = input("Password: ")
            confirmPass = input("Confirmation Password: ")
            if password != confirmPass:
                print("Password is not same as Confirmation Password")
                return
            else:
                # Create account file
                file_name = f"{user_name}_{password}"
                hashfileName = f"{data_folder.name}/{hashlib.sha256( file_name.encode("utf-8") ).hexdigest()}"
                create_user_data = {
                    "last-login": "",
                    "value": 0,
                    "value_tracker": 0,
                    # Transaction: { Date, Title, Money, income/pay }
                    "transaction": []
                }
                fernet = Fernet( generate_key( password ) )
                with open(hashfileName, "wb") as file:
                    file.write( fernet.encrypt(json.dumps(create_user_data).encode('utf-8')) )
        else:
            user_name = input("User Name: ")
            password = input("Password: ")
            file_name = f"{user_name}_{password}"
            hashFileName = f"{data_folder.name}/{hashlib.sha256( file_name.encode("utf-8") ).hexdigest()}"
            accountPath = pathlib.Path(hashFileName)
            if not accountPath.exists():
                print("Account Files is not exists")
                hashFileName = None
            else:
                UserName = user_name
                Password = password
                fernet = Fernet( generate_key( password ) )
                with open(hashFileName, "rb") as file:
                    text_data = file.read()
                data = fernet.decrypt( text_data )
                act_user_data = json.loads( data.decode() )
    elif first_command.lower() == "last_login":
        # Showing the latest login
        if act_user_data == None or UserName == "":
            print("You need to login")
            return
        print( act_user_data["last-login"] )
    elif first_command.lower() == "balance":
        # Showing the balance following the limit spend, highest, lowest and total spending in this month
        if act_user_data == None or UserName == "":
            print("You need to login")
            return
        print( f"Your Balance: RM {act_user_data["value"]}" )
        print( f"Your Limit Spend: RM {act_user_data["value_tracker"]}")
        cdate = ""
        cmin_date = ""
        cmax_date = ""
        total = 0
        total_spend = 0
        min_balance = 0
        max_balance = 0
        length = len(act_user_data["transaction"])

        for i in range(0, length):
            transaction = act_user_data["transaction"][i]
            if cdate != transaction[0] or i == length - 1:
                cdate = transaction[0]
                if max_balance < total:
                    max_balance = total
                    cmax_date = cdate
                if min_balance > total:
                    min_balance = total
                    cmin_date = cdate
                total = 0
            if transaction[2] == False:
                total += abs( transaction[3] )
                total_spend += abs( transaction[3] )

        print(f"The Highest Spend {cmax_date}: RM {max_balance} ")
        print(f"The Lowest Spend {cmin_date}: RM {min_balance} ")
        print(f"The Total Spend in this Month: RM {total_spend}")
    elif first_command.lower() == "list-transaction" or first_command.lower() == "list":
        # Showing the list of Transaction
        if act_user_data == None or UserName == "":
            print("You need to login")
            return
        cdate = ""
        total = 0
        length = len(act_user_data["transaction"])
        for i in range(0, length):
            transaction = act_user_data["transaction"][i]
            if cdate != transaction[0] or i == length - 1:
                print("Change")
                cdate = transaction[0]
                if total > act_user_data["value_tracker"]:
                    print(f"{transaction[0]}: RM { total } ( Out of Spending )")
                else:
                    print(f"{transaction[0]}: RM { total } ")
                total = 0
            if transaction[2] == False:
                total += abs( transaction[3] )

        print("\n======== List of Transaction ========")
        for i in range(0, len(act_user_data["transaction"])):
            transaction = act_user_data["transaction"][i]
            print(f"{i}| {transaction[0]}, {transaction[1]} {transaction[3]}")
    elif first_command.lower() == "logout":
        # Log out current account
        if act_user_data == None or UserName == "":
            print("You need to login")
            return
        log_out()
    elif first_command.lower() == "delete_account":
        # Delete current account
        if act_user_data == None or UserName == "":
            print("You need to login")
            return
        delete_user()
    elif first_command == "transaction" or first_command == "ts":
        # Add or Delete transaction
        if act_user_data == None or UserName == "":
            print("You need to login")
            return

        if len(lines) == 2 and lines[1] == "add":
            # Add the transaction
            date = datetime.now().strftime("%d/%m/%Y")
            trans_title = input("Title of Transaction: ")
            income_or_pay = input("True: income, False: pay?: ").lower() == "true"
            value = float(input("Value: RM "))

            if income_or_pay:
                act_user_data["value"] += value
            else:
                act_user_data["value"] -= value
                value = -value
            act_user_data["transaction"].append([date, trans_title, income_or_pay, value])
        elif len(lines) == 2 and lines[1] == "delete":
            index_delete = input("Enter the Index of Transaction: ")
            act_user_data["value"] -= act_user_data["transaction"][3]
            act_user_data["transaction"].remove( index_delete )
        else:
            print("Invalid Arguments")
    elif first_command == "budget":
        if act_user_data == None and UserName == "":
            print("You need to login")

        if len( lines ) > 0:
            if lines[1] == "set":
                act_user_data["value_tracker"] = int(input("Enter the maximum value to spend per day: RM "))
        
    elif first_command == "help":
        help_print()
    else:
        print(f"INVALID COMMAND OF: {first_command}")

def generate_key( keys ):
    keys_bytes = keys.encode()
    salt = b'\x12\x8f\x92\x04\xae\x88\xbe\x1c'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000
    )
    
    return base64.urlsafe_b64encode( kdf.derive( keys_bytes ) )

# Save automatically user data to file
def log_out():
    global UserName
    global hashFileName

    if hashFileName == None or UserName == "":
        return # No need to save
    UserName = ""
    print("Automatically save your data")
    act_user_data["last-login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(hashFileName, "wb") as file:
        file.write( fernet.encrypt(json.dumps(act_user_data).encode('utf-8')) )

def delete_user():
    global UserName
    global Password
    global hashFileName
    global fernet
    global act_user_data
    # Deleting Account User
    print("Delete an account will delete entire your transaction")
    confirmPassword = input("Enter your Password to confirm about deletion of account: ")
    if confirmPassword != Password:
        print("Invalid Confirmation Password")
        return
    os.remove( hashFileName )
    print("Your account has been deleted...")
    UserName = ""
    Password = None
    fernet = None
    hashFileName = None
    act_user_data = None
    return

def help_print():
    print("login - login to your account")
    print("login create - create new account")
    print("last_login - show the lastest login datetime")
    print("list-transaction/list - show the list of transaction")
    print("transaction/ts add - add new transaction")
    print("transaction/ts delete - delete the specific transaction")
    print("balance - show your balance")
    print("logout - log out the account")
    print("delete_account - deleting account")
    print("budget set - set your limit spending")

if __name__ == "__main__":
    main()
    