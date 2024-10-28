from flask import Flask, request, Response, redirect, g
from lupa import LuaRuntime
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import mimetypes
import os
import http.client
import json
import hashlib
import re
import base64
import uuid
import urllib.parse
import sqlite3
from datetime import datetime
import random
import socket
import psutil
import dns.resolver
import urllib.parse

app = Flask(__name__)
app.config["ROUTES_FOLDER"] = "routes"
app.config["MODULES_FOLDER"] = "modules"
app.config["ERRORS_FOLDER"] = os.path.join(app.config["ROUTES_FOLDER"], "errors")
lua = LuaRuntime(unpack_returned_tuples=True)
executor = ThreadPoolExecutor()

showLuaErrors = False


DATABASE = "shared_lists.db"

# Initialize the database connection as a global variable
db = sqlite3.connect(DATABASE, check_same_thread=False)


# Database Initialization to run on app start
def initDb():
    cursor = db.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS SharedList (
                        id TEXT PRIMARY KEY,
                        data TEXT NOT NULL
                    )"""
    )
    db.commit()
    print("Database initialized.")

try:
    os.remove(DATABASE)
except Exception:
    pass

# Ensure initDb runs when the script starts
initDb()


# Shared List Operations
def getList(listId):
    cursor = db.cursor()
    cursor.execute("SELECT data FROM SharedList WHERE id = ?", (listId,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])  # Deserialize JSON data
    else:
        # Insert a new empty list if not found
        cursor.execute(
            "INSERT INTO SharedList (id, data) VALUES (?, ?)", (listId, json.dumps([]))
        )
        db.commit()
        return []


def updateList(listId, data):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE SharedList SET data = ? WHERE id = ?", (json.dumps(data), listId)
    )
    db.commit()


class HtmlBuilder:
    def __init__(self):
        self.html_content = []
        self.tag_stack = []

    def _format_attributes(self, attributes):
        if not attributes:
            return ""
        return " " + " ".join(f'{k}="{v}"' for k, v in attributes.items())

    def doctype(self):
        self.html_content.append("<!DOCTYPE html>")
        return self

    def standalone(self, tag, attributes=None):
        formatted_attributes = self._format_attributes(attributes)
        self.html_content.append(f"<{tag}{formatted_attributes}>")
        return self

    def open(self, tag, attributes=None):
        formatted_attributes = self._format_attributes(attributes)
        self.html_content.append(f"<{tag}{formatted_attributes}>")
        self.tag_stack.append(tag)
        return self

    def selfClosing(self, tag, attributes=None):
        formatted_attributes = self._format_attributes(attributes)
        self.html_content.append(f"<{tag}{formatted_attributes} />")
        return self

    def empty(self, tag, attributes=None):
        formatted_attributes = self._format_attributes(attributes)
        self.html_content.append(f"<{tag}{formatted_attributes}></{tag}>")
        return self

    def plain(self, text):
        self.html_content.append(text)
        return self

    def title(self, text):
        self.html_content.append(f"<title>{text}</title>")
        return self

    def br(self):
        self.html_content.append("<br>")
        return self

    def head(self):
        return self.open("head")

    def body(self):
        return self.open("body")

    def meta(self, attributes=None):
        return self.selfClosing("meta", attributes)

    def link(self, attributes=None):
        return self.selfClosing("link", attributes)

    def script(self, src, attributes=None):
        if attributes is None:
            attributes = {}
        attributes["src"] = src
        return self.standalone("script", attributes)

    def close(self, times=1):
        for _ in range(times):
            if self.tag_stack:
                tag = self.tag_stack.pop()
                self.html_content.append(f"</{tag}>")
        return self

    def finish(self):
        while self.tag_stack:
            self.close()
        return "".join(self.html_content)

    # New Methods for Additional HTML Elements
    def div(self, attributes=None):
        return self.open("div", attributes)

    def span(self, attributes=None):
        return self.open("span", attributes)

    def p(self, attributes=None):
        return self.open("p", attributes)

    def a(self, href, attributes=None):
        if attributes is None:
            attributes = {}
        attributes["href"] = href
        return self.open("a", attributes)

    def img(self, src, attributes=None):
        if attributes is None:
            attributes = {}
        attributes["src"] = src
        return self.selfClosing("img", attributes)

    def ul(self, attributes=None):
        return self.open("ul", attributes)

    def ol(self, attributes=None):
        return self.open("ol", attributes)

    def li(self, attributes=None):
        return self.open("li", attributes)

    def h1(self, text, attributes=None):
        return self.open("h1", attributes).plain(text).close()

    def h2(self, text, attributes=None):
        return self.open("h2", attributes).plain(text).close()

    def h3(self, text, attributes=None):
        return self.open("h3", attributes).plain(text).close()

    def h4(self, text, attributes=None):
        return self.open("h4", attributes).plain(text).close()

    def h5(self, text, attributes=None):
        return self.open("h5", attributes).plain(text).close()

    def h6(self, text, attributes=None):
        return self.open("h6", attributes).plain(text).close()

    def form(self, attributes=None):
        return self.open("form", attributes)

    def input(self, attributes=None):
        return self.selfClosing("input", attributes)

    def button(self, text, attributes=None):
        return self.open("button", attributes).plain(text).close()

    def textarea(self, attributes=None):
        return self.open("textarea", attributes).close()

    def select(self, attributes=None):
        return self.open("select", attributes)

    def option(self, value, text, attributes=None):
        if attributes is None:
            attributes = {}
        attributes["value"] = value
        return self.open("option", attributes).plain(text).close()

    def footer(self, attributes=None):
        return self.open("footer", attributes)

    def header(self, attributes=None):
        return self.open("header", attributes)

    def section(self, attributes=None):
        return self.open("section", attributes)

    def article(self, attributes=None):
        return self.open("article", attributes)

    def aside(self, attributes=None):
        return self.open("aside", attributes)

    def main(self, attributes=None):
        return self.open("main", attributes)

    def nav(self, attributes=None):
        return self.open("nav", attributes)

    def scriptInline(self, code):
        self.html_content.append(f"<script>{code}</script>")
        return self

    def style(self, css):
        self.html_content.append(f"<style>{css}</style>")
        return self

class OsApi:
    @staticmethod
    def listDir(path):
        return lua.table_from(os.listdir(path))

    @staticmethod
    def remove(path):
        return os.remove(path)

    @staticmethod
    def rename(src, dst):
        return os.rename(src, dst)

    @staticmethod
    def pathExists(path):
        return os.path.exists(path)

    @staticmethod
    def isDir(path):
        return os.path.isdir(path)

    @staticmethod
    def isFile(path):
        return os.path.isfile(path)

    @staticmethod
    def makeDirs(path):
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def removeDir(path):
        return os.rmdir(path)

    @staticmethod
    def pathJoin(*paths):
        return os.path.join(*paths)

    @staticmethod
    def pathSplit(path):
        return os.path.split(path)

    @staticmethod
    def pathBasename(path):
        return os.path.basename(path)

    @staticmethod
    def pathDirname(path):
        return os.path.dirname(path)

    @staticmethod
    def pathAbsolute(path):
        return os.path.abspath(path)

    @staticmethod
    def pathGetSize(path):
        return os.path.getsize(path)

    @staticmethod
    def pathIsLink(path):
        return os.path.islink(path)


class HttpApi:
    @staticmethod
    def get(host, path, headers):
        conn = http.client.HTTPConnection(host)
        if headers is None:
            headers = {}
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return lua.table_from({"status": response.status, "data": data.decode("utf-8")})

    @staticmethod
    def post(host, path, body, headers):
        conn = http.client.HTTPConnection(host)
        if headers is None:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
        conn.request("POST", path, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return lua.table_from({"status": response.status, "data": data.decode("utf-8")})


class HtmlApi:
    @staticmethod
    def serveHtml(html):
        return {"response": html, "type": "text/html", "code": 200}

    @staticmethod
    def serveError(code):
        try:
            # Try serving the requested error code file
            with open(
                os.path.join(app.config["ERRORS_FOLDER"], f"{code}.html"), "r"
            ) as file:
                error = file.read()
                return {"response": error, "type": "text/html", "code": code}
        except FileNotFoundError:
            try:
                # Fallback to 500.html if the specific error file doesn't exist
                with open(
                    os.path.join(app.config["ERRORS_FOLDER"], "500.html"), "r"
                ) as file:
                    error = file.read()
                    return {"response": error, "type": "text/html", "code": 500}
            except FileNotFoundError:
                # Final fallback to plain text response
                return {
                    "response": "Hi, the person who made this website is a terrible person, and didn't even bother to make an error page.\nThis is the default error message on the server software made by a good person.\nLike they literally asked the software to return an error, but they didn't even make the page for that error, or the default error page.\nThe code was: 500",
                    "type": "text/plain",
                    "code": 500,
                }

    @staticmethod
    def builder():
        return HtmlBuilder()  # Assumes HtmlBuilder class is already defined


class UtilityApi:
    @staticmethod  # Sleep for a specified amount of time in seconds
    def sleep(seconds):
        time.sleep(seconds)

    @staticmethod
    def serveRedirect(link):
        """Return a dictionary for a redirect response."""
        return lua.table_from({"_redirect": link})

    @staticmethod
    def hashData(data, algorithm="sha256"):
        try:
            hashFunc = hashlib.new(algorithm)
            hashFunc.update(data.encode("utf-8"))
            return hashFunc.hexdigest()
        except ValueError:
            return f"Unsupported hash algorithm: {algorithm}"

    @staticmethod
    def validateEmail(email):
        emailPattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(emailPattern, email))

    @staticmethod
    def base64Encode(data):
        encodedBytes = base64.b64encode(data.encode("utf-8"))
        return encodedBytes.decode("utf-8")

    @staticmethod
    def base64Decode(data):
        try:
            decodedBytes = base64.b64decode(data.encode("utf-8"))
            return decodedBytes.decode("utf-8")
        except base64.binascii.Error:
            return "Invalid Base64 data"

    @staticmethod
    def timestamp():
        return datetime.utcnow().isoformat()

    @staticmethod
    def uuid():
        return str(uuid.uuid4())

    @staticmethod
    def urlEncode(data):
        return urllib.parse.quote(data)

    @staticmethod
    def urlDecode(data):
        return urllib.parse.unquote(data)

    @staticmethod
    def generateRandomString(length):
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def getIPAddress():
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    @staticmethod
    def dnsLookup(domain):
        try:
            answers = dns.resolver.resolve(domain, "A")
            return [answer.to_text() for answer in answers]
        except Exception as e:
            return str(e)

    @staticmethod
    def generateSlug(text):
        slug = text.lower()
        slug = slug.replace(" ", "-")
        return urllib.parse.quote(slug)

    @staticmethod
    def getCpuUsage():
        return psutil.cpu_percent(interval=1)

    @staticmethod
    def getMemoryUsage():
        memoryInfo = psutil.virtual_memory()
        return memoryInfo.used // 1024  # Return in kilobytes

class SharedListApi:
    @staticmethod
    def appendToList(listId, item):
        dataList = getList(listId)
        dataList.append(str(item))  # Append to the list (starting at index 1 in Lua)
        updateList(listId, dataList)
        return f"Item added to list {listId}"

    @staticmethod
    def removeFromList(listId, item):
        dataList = getList(listId)
        try:
            dataList.remove(int(item))
            updateList(listId, dataList)
            return f"Item removed from list {listId}"
        except ValueError:
            return f"Item not found in list {listId}"

    @staticmethod
    def getListData(listId):
        return lua.table_from(getList(listId))

    @staticmethod
    def getItem(listId, index):
        dataList = getList(listId)
        # Adjust index to be 1-based (Lua convention)
        if 0 < index <= len(dataList):
            return dataList[index - 1]
        return None

    @staticmethod
    def deleteList(listId):
        cursor = db.cursor()
        cursor.execute("DELETE FROM SharedList WHERE id = ?", (listId,))
        db.commit()
        return f"List {listId} deleted"

    @staticmethod
    def listExists(listId):
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(1) FROM SharedList WHERE id = ?", (listId,))
        exists = cursor.fetchone()[0] > 0
        return exists


luaGlobals = lua.globals()
with open("json.lua", "r") as file:
    luaGlobals.json = lua.execute(file.read())

class Api:
    http = HttpApi
    json = luaGlobals.json
    os = OsApi
    html = HtmlApi
    util = UtilityApi
    list = SharedListApi

luaGlobals.api = Api


# Load Modules Dynamically
def loadModules():
    modules = {}
    moduleFolder = app.config["MODULES_FOLDER"]
    if os.path.isdir(moduleFolder):
        for moduleFile in os.listdir(moduleFolder):
            if moduleFile.endswith(".lua"):
                moduleName = os.path.splitext(moduleFile)[0]
                with open(os.path.join(moduleFolder, moduleFile), "r") as file:
                    luaScript = file.read()
                    luaFunction = lua.execute(f"return function() {luaScript} end")
                    modules[moduleName] = luaFunction

    return modules


loadedModules = loadModules()


# Automatically call module named "_"
if "_" in loadedModules:
    loadedModules["_"]()


# Modify require behavior to load from modules if available
def customRequire(moduleName):
    if moduleName in loadedModules:
        return loadedModules[moduleName]()
    else:
        return "Module not found."


luaGlobals.require = customRequire

def getRequestData():
    """Retrieve request data for Lua scripts."""
    return lua.table_from(
        {
            "urlArguments": lua.table_from(dict(request.args)),
            "headers": lua.table_from(dict(request.headers)),
            "method": request.method,
        }
    )


def getLuaErrorMessage(e):
    if showLuaErrors:
        return f"Error: {str(e)}"
    return "Error"


def processCustomLuaTags(htmlContent):
    def executeLuaCode(match):
        # Capture Lua code and strip tags and extra whitespace
        code = match.group(1).strip()
        output = ""
        try:
            # Execute only the Lua code, without tags
            result = lua.execute(code)
            output = str(result) if result is not None else ""
        except Exception as e:
            # Insert error message if there's an execution error
            output = f'<div class="_error">{getLuaErrorMessage(e)}</div>'
        return output

    # Regex to capture content within <$lua ... $> or <$lua>...</$>
    processedContent = re.sub(
        r"<\$lua\s*>(.*?)<\$>", executeLuaCode, htmlContent, flags=re.DOTALL
    )
    return processedContent


def serveErrorPage(errorCode):
    """Serve a custom error page manually, or a plain text response if unavailable."""
    errorPath = os.path.join(app.config["ERRORS_FOLDER"], f"{errorCode}.html")
    if os.path.isfile(errorPath):
        with open(errorPath, "r") as file:
            return Response(
                file.read(), status=int(errorCode), content_type="text/html"
            )
    return Response(
        f"Hi, the person who made this website forgot to make one specific error page, meaning this message is being shown.\nThis is the default error message on the server software made by a good person.\nThe code was: {errorCode}",
        status=int(errorCode),
        content_type="text/plain",
    )


def handleLuaError(e):
    """Attempt to serve luaError.html, then 500.html, with a final fallback to a plain text message."""
    luaErrorPath = os.path.join(app.config["ERRORS_FOLDER"], "luaError.html")
    if os.path.isfile(luaErrorPath):
        with open(luaErrorPath, "r") as file:
            return Response(
                file.read().replace("<$error$>", getLuaErrorMessage(e)),
                status=500,
                content_type="text/html",
            )

    return Response(
        "Well, the person who made this website decided to not make an error page.\nThere was an error with their code.\n "
        + getLuaErrorMessage(e),
        status=500,
        content_type="text/plain",
    )


def handleLuaFile(path, requestData):
    """Execute a Lua file and handle any errors during execution."""
    try:
        with app.app_context():  # Ensure Flask app context
            with open(path, "r") as file:
                luaScript = file.read()

            # Execute Lua script with request data
            luaFunction = lua.execute(luaScript)
            result = dict(luaFunction(requestData))

            if result is not None:
                if "response" in result:
                    return Response(
                        result["response"],
                        status=result.get("code", 200),
                        content_type=result.get("type", "text/plain"),
                        headers=result.get("headers", {}),
                    )
                elif "_redirect" in result:
                    return redirect(result["_redirect"])
            else:
                print("Error: Invalid response from Lua function.")
                return serveErrorPage("500")

    except Exception as e:
        print("Lua Error:", e)
        return handleLuaError(str(e))


@app.route("/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "DELETE"])
def routeHandler(subpath):
    """Handle routes by serving Lua scripts or other files in the routes folder."""
    if subpath == "":
        luaPath = os.path.join(app.config["ROUTES_FOLDER"], "_.lua")
    else:
        luaPath = os.path.join(app.config["ROUTES_FOLDER"], subpath, "_.lua")

    # If default route file doesn’t exist, check for specific file
    if not os.path.isfile(luaPath):
        luaPath = os.path.join(app.config["ROUTES_FOLDER"], f"{subpath}.lua")

    if os.path.isfile(luaPath):
        requestData = getRequestData()
        return executor.submit(handleLuaFile, luaPath, requestData).result()

    # If the route is a .shtml file, process embedded Lua tags
    if subpath.endswith(".shtml"):
        shtmlPath = os.path.join(app.config["ROUTES_FOLDER"], subpath)
        if os.path.isfile(shtmlPath):
            with open(shtmlPath, "r") as file:
                htmlContent = file.read()

            # Process embedded Lua tags in .shtml file
            processedContent = processCustomLuaTags(htmlContent)

            return Response(processedContent, content_type="text/html")

    # Serve non-Lua files directly if available
    otherFilePath = os.path.join(app.config["ROUTES_FOLDER"], subpath)
    if os.path.isfile(otherFilePath):
        with open(otherFilePath, "rb") as file:
            # Guess the content type based on file extension
            mimeType, _ = mimetypes.guess_type(otherFilePath)
            contentType = mimeType if mimeType else "application/octet-stream"

            return Response(file.read(), content_type=contentType)

    # Fallback to 404 if file not found
    return serveErrorPage("404")


# Set a generic error handler that captures all HTTP errors
@app.errorhandler(Exception)
def handleAnyHttpError(e):
    """Catch all HTTP errors and serve corresponding error pages."""
    # Retrieve HTTP status code, default to 500 if not available
    statusCode = e.code if hasattr(e, "code") else 500
    return serveErrorPage(str(statusCode))

if __name__ == "__main__":
    showLuaErrors = True
    app.run(host="0.0.0.0", port=80, debug=True)
