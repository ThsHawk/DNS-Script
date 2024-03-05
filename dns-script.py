import time
import json
import sys
import subprocess
from Record import Record 
from pathlib import Path

CF_BASE_URL = "https://api.cloudflare.com/client/v4/"
FILE_PATH = Path(__file__).parent

def logger(message):
    log = "[" + time.ctime() + "]" + " " + message
    logFile = open(str(FILE_PATH) + "/dns-script.log", "a")
    logFile.write(log + "\n")
    logFile.close()

def openFile(fileName, op):
    if op == "r" or op == "r+":
        try:
            file = open(fileName, op)
        except FileNotFoundError:
            logger("file: \"" + fileName + "\" not found")
            exit()
        else:
            return file
    else:
        return open(fileName, op)

def getCfIP(domain):
    cfCredentialsFile = openFile(str(FILE_PATH) + "/credentials.json", "r")
    cfCredentials = json.load(cfCredentialsFile)
    cfCredentialsFile.close()
    getRequest = "curl -X GET \"" + CF_BASE_URL + "zones/" + cfCredentials["ZONE_ID"] + "/dns_records/\"" + " -H \"Content-Type: application/json\" -H \"Authorization: Bearer " + cfCredentials["KEY"] + "\" "
    getResponse = subprocess.check_output(getRequest, shell=True, universal_newlines=True)
    getResponse = json.loads(getResponse)
    records = getResponse["result"]
    for i in records:
        recordName = i["name"]
        if recordName == domain:
            record = Record()
            record.setId(i["id"])
            record.setName(i["name"])
            record.setContent(i["content"])
            return record
    return None

def getMachineIP():
    cmmd = "ip a | grep inet6 | grep global"
    machineIP = subprocess.check_output(cmmd, shell=True, universal_newlines=True)
    machineIP = machineIP.split(" ")
    machineIP = machineIP[5].split("/")
    return machineIP[0]

def updateRecord(domainID, newIP):
    cfCredentialsFile = openFile(str(FILE_PATH) + "/credentials.json", "r")
    cfCredentials = json.load(cfCredentialsFile)
    cfCredentialsFile.close()
    patchRequest = "curl -X PATCH \"" + CF_BASE_URL + "zones/" + cfCredentials["ZONE_ID"] + "/dns_records/" + domainID  + "\" -H \"Content-Type: application/json\" -H \"Authorization: Bearer " + cfCredentials["KEY"] + "\" --data \'{\"content\":\"" + newIP  + "\"}\'"
    patchResponse = subprocess.check_output(patchRequest, shell=True, universal_newlines=True)
    patchResponse = json.loads(patchResponse)
    return patchResponse["success"]

def main(domain):
    cfIP = getCfIP(domain)
    if cfIP == None:
        logger("An error occurred during \"" + domain + "\" search on CloudFlare DNS.")
        exit()
    machineIP = getMachineIP()
    if cfIP.getContent() != machineIP:
        status = updateRecord(cfIP.getId(), machineIP)
        if status:
            logger("CloudFlare DNS Records updated successfully.")
        else:
            logger("An error occurred during record update.")
    else:
        logger("CloudFlare DNS Record is up-to-date.")
        exit()

if len(sys.argv) == 2:
    main(sys.argv[1])
