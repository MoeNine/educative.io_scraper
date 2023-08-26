import json
import os

import requests
import websockets
from selenium import webdriver

from src.Common.Constants import constants
from src.Logging.Logger import Logger


class BrowserUtility:
    def __init__(self, configJson):
        self.devToolJsonUrl = None
        self.browser = None
        self.configJson = configJson
        self.devToolUrl = None
        self.logger = Logger(configJson, "BrowserUtility").logger


    def loadBrowser(self):
        userDataDir = os.path.join(
            constants.OS_ROOT, self.configJson["userDataDir"])
        options = webdriver.ChromeOptions()
        if self.configJson["headless"]:
            options.add_argument('headless')
        options.add_argument(f'user-data-dir={userDataDir}')
        options.add_argument('--profile-directory=Default')
        options.add_argument("--start-maximized")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-web-security")
        options.add_argument('--allow-running-insecure-content')
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument('--log-level=3')
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.56 Safari/537.36"
        options.add_argument(f'user-agent={userAgent}')
        options.binary_location = constants.chromeBinaryPath
        self.browser = webdriver.Remote(
            command_executor='http://127.0.0.1:9515', options=options)
        self.browser.set_window_size(1920, 1080)
        self.browser.command_executor._commands["send_command"] = (
            "POST", '/session/$sessionId/chromium/send_command')
        self.logger.debug("Browser Initiated")
        return self.browser


    def getDevToolsUrl(self):
        devToolsFilePath = os.path.join(constants.OS_ROOT, self.configJson["userDataDir"], "DevToolsActivePort")
        with open(devToolsFilePath) as f:
            devToolsFile = f.readlines()
            devToolsPort = devToolsFile[0].split("\n")[0]
            devToolsId = devToolsFile[1].split("\n")[0]
        self.devToolUrl = f"ws://127.0.0.1:{devToolsPort}{devToolsId}"
        self.devToolJsonUrl = f"http://127.0.0.1:{devToolsPort}/json/list"


    async def shutdownChromeViaWebsocket(self):
        try:
            self.getDevToolsUrl()
            async with websockets.connect(self.devToolUrl) as websocket:
                message = {
                    "id": 1,
                    "method": "Browser.close"
                }
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                self.logger.debug(f"shutdownChromeViaWebsocket Response: {response}")
        except Exception as e:
            self.logger.error("No Browser was open to close via websocket")


    async def getCurrentUrlViaWebsocket(self):
        try:
            self.getDevToolsUrl()
            response = requests.get(self.devToolJsonUrl)
            currentUrl = json.loads(response.content)[0]['url']
            self.logger.info(currentUrl)
        except Exception as e:
            self.logger.error("Error occurred while getting current URL via websocket")
