import os
import time
import json
import asyncio
import zipfile
import importlib.util
import sys  # Added for restart functionality
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# Configuration
SESSION_NAME = "userbot_session"

# File to store session data
SESSION_FILE = "session_data.json"

# File to store loaded modules
MODULES_FILE = "loaded_modules.json"

# Folder to store modules
MODULES_FOLDER = "modules"

# Track bot start time for uptime calculation
start_time = time.time()

# Whitelist for authorized users
whitelist = set()

# Ensure the modules folder exists
if not os.path.exists(MODULES_FOLDER):
    os.makedirs(MODULES_FOLDER)

# Load session data if it exists
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return None

# Save session data
def save_session(phone_number, api_id, api_hash):
    with open(SESSION_FILE, "w") as f:
        json.dump({"phone_number": phone_number, "api_id": api_id, "api_hash": api_hash}, f)

# Load the list of loaded modules
def load_loaded_modules():
    if os.path.exists(MODULES_FILE):
        with open(MODULES_FILE, "r") as f:
            return json.load(f)
    return []

# Save the list of loaded modules
def save_loaded_modules(modules):
    with open(MODULES_FILE, "w") as f:
        json.dump(modules, f)

# Initialize the Telegram client
client = None

# Function to load a module from a .zip file
async def load_module_from_zip(zip_path, event):
    try:
        # Extract the .zip file to the modules folder
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(MODULES_FOLDER)

        # Get the module name from the .zip file name
        module_name = os.path.basename(zip_path).replace(".zip", "")
        module_path = os.path.join(MODULES_FOLDER, f"{module_name}.py")
        changelog_path = os.path.join(MODULES_FOLDER, "changelog.tlog")

        # Check if the required files exist
        if not os.path.exists(module_path):
            await event.reply(f"❌ Error: {module_name}.py not found in the .zip file.")
            return
        if not os.path.exists(changelog_path):
            await event.reply(f"❌ Error: changelog.tlog not found in the .zip file.")
            return

        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check if the module has a register function
        if hasattr(module, "register"):
            await module.register(client)
            await event.reply(f"✅ Module {module_name} loaded successfully!")
        else:
            await event.reply(f"❌ Error: Module {module_name} does not have a register function.")

        # Read and display the changelog
        with open(changelog_path, "r") as f:
            changelog = f.read()
        await event.reply(f"📝 Changelog for {module_name}:\n{changelog}")

        # Add the module to the list of loaded modules
        loaded_modules = load_loaded_modules()
        if module_name not in loaded_modules:
            loaded_modules.append(module_name)
            save_loaded_modules(loaded_modules)

    except Exception as e:
        await event.reply(f"❌ Error loading module: {str(e)}")

# Main function to start the bot
async def main():
    global client

    # Prompt user for API ID, API Hash, and phone number
    api_id = input("Enter your API ID: ")
    api_hash = input("Enter your API Hash: ")
    phone_number = input("Enter your phone number (with country code, e.g., +1234567890): ")

    # Initialize the Telegram client
    client = TelegramClient(SESSION_NAME, api_id, api_hash)

    # Start the client
    await client.start()
    print("Userbot started!")

    # Check if the user is authorized
    if not await client.is_user_authorized():
        # Send a code request
        await client.send_code_request(phone_number)
        code = input("Enter the code you received: ")
        try:
            await client.sign_in(phone_number, code)
        except SessionPasswordNeededError:
            password = input("Your account is protected by 2FA. Enter your password: ")
            await client.sign_in(password=password)

    # Save session data
    save_session(phone_number, api_id, api_hash)

    # Load previously loaded modules
    loaded_modules = load_loaded_modules()
    for module_name in loaded_modules:
        module_path = os.path.join(MODULES_FOLDER, f"{module_name}.py")
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                await module.register(client)
                print(f"✅ Reloaded module: {module_name}")

    # Keep the bot running
    print("Userbot is running...")
    await client.run_until_disconnected()

# Event handler for new messages
@client.on(events.NewMessage)
async def handler(event):
    if event.raw_text.startswith("."):
        command = event.raw_text[1:].lower()

        # Ping command
        if command == "ping":
            # Calculate uptime
            uptime_seconds = int(time.time() - start_time)
            uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

            # Calculate ping
            start_ping = time.time()
            await event.edit("Pinging...")
            end_ping = time.time()
            ping_ms = round((end_ping - start_ping) * 1000, 2)

            # Send the result
            await event.edit(f"☕ Uptime: {uptime_str}\n✈️ Ping: {ping_ms}ms")

        # Whitelist commands
        elif command.startswith("addwhitelist"):
            user_id = command.split(" ")[1] if len(command.split(" ")) > 1 else None
            if user_id:
                whitelist.add(user_id)
                await event.reply(f"User {user_id} added to whitelist.")
            else:
                await event.reply("Please provide a user ID to add.")

        elif command.startswith("whitelistremove"):
            user_id = command.split(" ")[1] if len(command.split(" ")) > 1 else None
            if user_id in whitelist:
                whitelist.remove(user_id)
                await event.reply(f"User {user_id} removed from whitelist.")
            else:
                await event.reply(f"User {user_id} is not in the whitelist.")

        elif command == "whitelist":
            if whitelist:
                await event.reply("Current whitelist: " + ", ".join(whitelist))
            else:
                await event.reply("The whitelist is empty.")

        # Load command
        elif command.startswith("load"):
            if event.is_reply:
                reply_message = await event.get_reply_message()
                if reply_message.document:
                    # Download the .zip file
                    zip_path = await reply_message.download_media()
                    if zip_path.endswith(".zip"):
                        await event.reply("Loading module from .zip file...")
                        await load_module_from_zip(zip_path, event)
                    else:
                        await event.reply("❌ Error: The file must be a .zip file.")
                else:
                    await event.reply("❌ Error: Please reply to a .zip file.")
            else:
                await event.reply("❌ Error: Please reply to a .zip file to load a module.")

        # Restart command
        elif command == "restart":
            await event.reply("🔄 Restarting the userbot...")
            # Restart the bot
            os.execv(sys.executable, [sys.executable] + sys.argv)

        # Help command
        elif command == "help":
            help_message = """
            **Available Commands:**
            - `.ping`: Check bot uptime and ping.
            - `.addwhitelist <user_id>`: Add a user to the whitelist.
            - `.whitelistremove <user_id>`: Remove a user from the whitelist.
            - `.whitelist`: List all users in the whitelist.
            - `.load`: Load a module from a .zip file (reply to a .zip file).
            - `.restart`: Restart the userbot.
            - `.help`: Show this help message.
            """
            await event.reply(help_message)

# Start the bot
if __name__ == "__main__":
    asyncio.run(main())
