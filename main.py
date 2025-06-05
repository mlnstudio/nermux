import os
import getpass
import hashlib
import shutil
from cryptography.fernet import Fernet
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout import Layout
from time import sleep

# Define MLN OS root directory and security files
ROOT_DIR = "mln-sda"
ETC_DIR = os.path.join(ROOT_DIR, "etc")  # System configuration folder
CREDENTIALS_FILE = os.path.join(ETC_DIR, "credentials")
KEY_FILE = os.path.join(ETC_DIR, "keyfile")

os.makedirs(ETC_DIR, exist_ok=True)  # Ensure /etc exists inside mln-sda

def generate_key():
    """Generate and store encryption key securely."""
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

def load_key():
    """Load encryption key or create one if missing."""
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()

fernet = Fernet(load_key())

def create_credentials():
    """Prompt user to set up a username and password for the first time and encrypt them."""
    print("No saved credentials found. Please set up a username and password.")
    
    while True:
        username_inp = input("New Username: ").strip()
        passwd_inp = getpass.getpass("New Password: ")
        confirm_passwd = getpass.getpass("Confirm Password: ")

        if not username_inp:
            print("Username cannot be empty. Try again.")
            continue

        if passwd_inp == confirm_passwd:
            username_hash = hashlib.sha256(username_inp.encode()).hexdigest()
            passwd_hash = hashlib.sha256(passwd_inp.encode()).hexdigest()
            encrypted_credentials = fernet.encrypt(f"{username_hash}:{passwd_hash}".encode())

            with open(CREDENTIALS_FILE, "wb") as f:
                f.write(encrypted_credentials)

            os.chmod(CREDENTIALS_FILE, 0o400)  # Set file permissions to read-only
            print("Username and password successfully created!")
            return username_hash, passwd_hash
        else:
            print("Passwords do not match. Please try again.")

def load_credentials():
    """Load stored encrypted credentials."""
    if not os.path.exists(CREDENTIALS_FILE):
        return create_credentials()

    with open(CREDENTIALS_FILE, "rb") as f:
        encrypted_credentials = f.read()

    decrypted_data = fernet.decrypt(encrypted_credentials).decode()
    username_hash, passwd_hash = decrypted_data.split(":")
    return username_hash, passwd_hash

# Load username and password from storage
stored_username, stored_password = load_credentials()

print("---[MLN OS Login Screen]---\n")

# Login System
access_shell_login = False
while not access_shell_login:
    usr_inp = input("Username: ")
    usr_hash = hashlib.sha256(usr_inp.encode()).hexdigest()

    if usr_hash == stored_username:
        passwd_inp = getpass.getpass("Password: ")
        passwd_hash = hashlib.sha256(passwd_inp.encode()).hexdigest()

        if passwd_hash == stored_password:
            print("Login successful!")
            access_shell_login = True
        else:
            print("Password is incorrect.")
    else:
        print("Username is incorrect.")

# Shell Functions
computer_status_binary = 1
die = lambda: exit()
relive = lambda: exec(open(__file__).read())  # Reboots by re-executing script

current_dir = ROOT_DIR  # Start in mln-sda directory

def load_file(filename):
    """Load existing file content or create a new one."""
    file_path = os.path.join(current_dir, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    return ""

def save_file(filename, text):
    """Save file content inside `mln-sda`."""
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'w') as file:
        file.write(text)
    print(f"\nFile '{filename}' saved in mln-sda! Exiting...")

def nate_text_editor(filename):
    """Interactive CLI-based text editor using prompt_toolkit."""
    text = load_file(filename)
    
    text_area = TextArea(text=text, scrollbar=True)

    bindings = KeyBindings()

    @bindings.add("c-x")  # Ctrl+X to Save & Exit
    def _(event):
        save_file(filename, text_area.text)
        event.app.exit()

    app = Application(
        layout=Layout(container=text_area),
        key_bindings=bindings,
        full_screen=True
    )

    print(f"Editing: {filename} inside MLN OS (Press Ctrl+X to Save & Exit)")
    app.run()

print("\nMLN OS 🄯 2025 GPLV3 Copyleft")
print("OS: MLN OS 1.0v alpha")
print("Kernel: Nerkel 1.0v alpha\n")

# Interactive Shell Loop
while computer_status_binary == 1:
    shell_command = input(f"/{current_dir} >>> ").strip()

    if shell_command == "die":
        print("Shutting Down...")
        sleep(1)
        die()

    elif shell_command == "relive":
        print("Rebooting...")
        sleep(1)
        relive()

    elif shell_command == "clear":
        os.system("clear")

    elif shell_command == "ls":
        print(" ".join(os.listdir(current_dir)))

    elif shell_command.startswith("touch "):
        filename = shell_command[6:].strip()
        if filename:
            with open(os.path.join(current_dir, filename), "w") as f:
                f.write("")
            print(f"File '{filename}' created.")

    elif shell_command.startswith("mkdir "):
        dirname = shell_command[6:].strip()
        if dirname:
            os.makedirs(os.path.join(current_dir, dirname), exist_ok=True)
            print(f"Directory '{dirname}' created.")

    elif shell_command.startswith("cat "):
        filename = shell_command[4:].strip()
        file_path = os.path.join(current_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, "r") as f:
                print(f.read())
        else:
            print(f"No such file '{filename}' in {current_dir}")

    elif shell_command.startswith("rm "):
        args = shell_command[3:].strip().split()

        if len(args) == 1:
            file_path = os.path.join(current_dir, args[0])
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                print(f"File '{args[0]}' removed.")
            else:
                print(f"No such file '{args[0]}'")

        elif len(args) == 2 and args[0] == "-r":
            dir_path = os.path.join(current_dir, args[1])
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
                print(f"Directory '{args[1]}' removed.")
            else:
                print(f"No such directory '{args[1]}'")

    elif shell_command.startswith("nate "):
        filename = shell_command[5:].strip()
        nate_text_editor(filename)

    elif shell_command == "help":
        print("Commands:")
        print("ls      - List files and directories")
        print("cd      - Change directory")
        print("cd ..   - Go back to previous directory")
        print("cat     - Read files")
        print("touch   - Create a file")
        print("mkdir   - Make a directory")
        print("rm      - Delete a file")
        print("rm -r   - Delete a directory recursively")
        print("nate    - Open Nate Text Editor")
        print("clear   - Clear screen")
        print("relive  - Reboot system")
        print("die     - Shutdown system")
        print("help    - Show help message")

    elif shell_command.startswith("cd "):
        dirname = shell_command[3:].strip()

        if dirname == "..":
            # Move up one directory level
            if current_dir != ROOT_DIR:
                current_dir = os.path.dirname(current_dir)
            else:
                print("Already at the root directory.")
        else:
            new_dir = os.path.join(current_dir, dirname)
            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                current_dir = new_dir
            else:
                print(f"No such directory '{dirname}'")

