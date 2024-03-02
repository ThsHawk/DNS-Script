import time
import json
import sys
import subprocess

CF_BASE_URL = "https://api.cloudflare.com/client/v4/"

def openFile(fileName, op):
    if op == "r" or op == "r+":
        try:
            file = open(fileName, op)
        except FileNotFoundError:
            print("file: \"" + fileName + "\" not found")
            exit()
        else:
            return file
    else:
        return open(fileName, op)

def getCfIP(domain):
    cfCredentialsFile = openFile("credentials.json", "r")
    cfCredentials = json.load(cfCredentialsFile)
    cfCredentialsFile.close()
    getRequest = "curl -X GET \"" + CF_BASE_URL + "zones/" + cfCredentials["ZONE_ID"] + "/dns_records/export\"" + " -H \"Content-Type: application/json\" -H \"Authorization: Bearer " + cfCredentials["KEY"] + "\" " + "| grep AAAA " + "| grep " + domain
    cfIP = subprocess.check_output(getRequest, shell=True, universal_newlines=True)
    cfIP = cfIP.split("\t")
    cfIP = cfIP[4]
    cfIP = cfIP[:len(cfIP)-1]
    return cfIP

def getMachineIP():
    cmmd = "ip a | grep inet6 | grep global"
    machineIP = subprocess.check_output(cmmd, shell=True, universal_newlines=True)
    machineIP = machineIP.split(" ")
    machineIP = machineIP[5].split("/")
    return machineIP[0]

def updateRecord(domainID, newIP):
    cfCredentialsFile = openFile("credentials.json", "r")
    cfCredentials = json.load(cfCredentialsFile)
    cfCredentialsFile.close()
    patchRequest = "curl -X PATCH \"" + CF_BASE_URL + "zones/" + cfCredentials["ZONE_ID"] + "/dns_records/" + domainID  + "\" -H \"Content-Type: application/json\" -H \"Authorization: Bearer " + cfCredentials["KEY"] + "\" --data \'{\"content\":\"" + newIP  + "\"}\'"
    patchResponse = subprocess.check_output(patchRequest, shell=True, universal_newlines=True)
    patchResponse = json.loads(patchResponse)
    return (patchResponse["success"], patchResponse["errors"])

def main(domain, domainID):
    cfIP = getCfIP(domain)
    machineIP = getMachineIP()
    if cfIP != machineIP:
        status = updateRecord(domainID, machineIP)
        if status[0]:
            print("CloudFlare DNS Recors updated successfully!")
        else:
            print("Err: " + status[1][0] + " (" + status[1][1]  +  ")")
    else:
        print("CloudFlare DNS Record is up-to-date!")
        exit()

if len(sys.argv) == 3:
    main(sys.argv[1], sys.argv[2])