'''
* Copyright 2019-2020 VMware, Inc.
* All Rights Reserved.
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*   http://www.apache.org/licenses/LICENSE-2.0
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
'''

import os
import argparse
import subprocess
import re
import sys 
from shutil import make_archive
import yaml
import time
import warnings
from datetime import datetime
import logging
import traceback
import re
patt = re.compile("[^\t]+")
warnings.filterwarnings("ignore")
encoding = 'utf-8'

class exception(Exception):
    def __init__(self, msg):
        self.msg = msg

def display_colored_text(color, text):
    return "\033[{} {}\033[00m".format(color, text)


def getLogFolderName(helmchart, podType):
    return podType + '-' + helmchart + '-' + str(datetime.now().strftime("%Y-%m-%d-%H%M%S"))

def zipDir(folderName):
    logging.info("Zipping directory %s" %folderName)
    try:
        make_archive(folderName, 'zip', folderName)
        removeDir(folderName)
    except:
        traceback.print_exc(file=sys.stdout)
        removeDir(folderName)
        raise exception("FALURE: : Could not zip the directory")

def makeDir(folderName):
    logging.info("Creating directory %s" %folderName)
    try:
        output = subprocess.check_output("mkdir %s" %folderName, shell=True)
    except subprocess.CalledProcessError:
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED:: : Exception occured when creating the directory %s" %folderName)

def removeDir(folderName):
    rm_dir = "rm -r %s" %folderName
    logging.info("Clean up: %s" %rm_dir)
    try:
        output = subprocess.check_output("%s" %rm_dir, shell=True)
    except subprocess.CalledProcessError:
        print("")
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED:: : Could not delete the directory %s" %folderName)

def copyLogsFromPVC(namespace, podName, pvMount, logFileName, folderName, pvcName, podType):
    kubectl_cp = "kubectl cp %s/%s:%s/%s %s/%s.log" %(namespace,podName,pvMount,logFileName,folderName, podType)
    logging.info("%s" %kubectl_cp)
    try:
        output = subprocess.check_output("%s" %kubectl_cp, shell=True)
        if len(output) > 0:
            logging.error(display_colored_text('31m',"ERROR: ") + "\n" + output.decode(encoding))
            logging.error(display_colored_text('34m',"WARNING: ") + "Because of the above error, skipping the log collection and proceeding with code")
            return
    except:
        print("")
        traceback.print_exc(file=sys.stdout)
        removeDir(folderName)
        raise exception("FAILED: : Could not collect logs from %s/%s of PVC %s " %(pvMount, logFileName, pvcName))

def getGdp(namespace, folderName):
    kubectl_get = "kubectl get gdp -n %s" %namespace
    gdp = subprocess.check_output("%s" %kubectl_get, shell=True)
    gdp = gdp.decode(encoding)
    if len(gdp) == 0:
        logging.error(display_colored_text('34m',"WARNING: ") + "No gdp resource in the given namespace. Skipping this part")
        return
    kubectl_get = "kubectl get gdp -n %s -o yaml > %s/gdp.yaml" %(namespace,folderName)
    logging.info("%s" %kubectl_get)
    try:
        output = subprocess.check_output("%s" %kubectl_get, shell=True)
    except:
        traceback.print_exc(file=sys.stdout)
        removeDir(folderName)
        raise Exception("FAILED : Error get GDP details")

def getGslb(namespace, folderName):
    kubectl_get = "kubectl get gslbconfig -n %s" %namespace
    gslb = subprocess.check_output("%s" %kubectl_get, shell=True)
    gslb = gslb.decode(encoding)
    if len(gslb) == 0:
        logging.error(display_colored_text('34m',"WARNING: ") + "No gslb config resource in the given namespace. Skipping this part")
        return
    kubectl_get = "kubectl get gslbconfig -n %s -o yaml > %s/gslb.yaml" %(namespace,folderName)
    logging.info("%s" %kubectl_get)
    try:
        output = subprocess.check_output("%s" %kubectl_get, shell=True)
    except:
        traceback.print_exc(file=sys.stdout)
        removeDir(folderName)
        raise Exception("FAILED : Error get GSLB details")

def getCRD(namespace, folderName):
    getGdp(namespace, folderName)
    getGslb(namespace, folderName)

def getConfigmap(namespace, folderName):
    get_congifmap = "kubectl get cm -n %s -o yaml > %s/config-map.yaml" %(namespace,folderName)
    logging.info("%s" %get_congifmap)
    subprocess.check_output("%s" %get_congifmap, shell=True)

def findPodName(namespace, helmchart, podType):
    get_pod = "kubectl get pod -n %s -l app.kubernetes.io/instance=%s" %(namespace, helmchart)
    try:
        logging.info("%s" %get_pod)
        Pods = subprocess.check_output("%s" %get_pod , shell=True)
        Pods = Pods.decode(encoding)
        #In case of an error, an empty output is returned by the kubectl get command
        if len(Pods)==0:
            raise exception("FAILED: : Error in getting the pod name from the helm chart in the given namespace")
        allPods = Pods.splitlines()[1:]
        for podLine in allPods:
            podName = podLine.split(' ')[0]
            if podName.find(podType) == -1:
                continue 
            return podName
        raise exception("FAILED: : No amko pod in the specified helm chart")
    except subprocess.CalledProcessError:
        print("")
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED: : Could not get pod name")

def describePod(namespace,podName):
    describe_pod = "kubectl describe pod %s -n %s" %(podName,namespace) 
    logging.info("%s" %describe_pod)
    try:
        statusOfPod =  subprocess.check_output("%s" %describe_pod , shell=True)
        statusOfPod =  statusOfPod.decode(encoding)
        return statusOfPod
    except subprocess.CalledProcessError:
        #print the exception that occured 
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED: : Exception occured")  

def pvHelper(namespace, helmchart) : 
    # Take details such as PVC and Mount path from the pod helm chart
    helm_get = "helm get all %s -n %s" %(helmchart,namespace)
    try:
        logging.info("%s" %helm_get)
        helmResult = subprocess.check_output("%s" %helm_get , shell=True)
        helmResult = helmResult.decode(encoding)
        return helmResult
    except subprocess.CalledProcessError:
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED: : Exception occured") 
    
def editDeploymentFile(backupPodName, pvcName, pvMount, namespace):
    try:
        deploymentDict = {'apiVersion': 'v1', 'kind':'Pod', 'metadata':{'name': 'custom-backup-pod', 'namespace': '' }, 'spec':{'containers':[{'image': 'avinetworks/server-os', 'name': 'myfrontend', 'volumeMounts':[{'mountPath': '', 'name': 'mypd'}]}], 'volumes':[{'name': 'mypd', 'persistentVolumeClaim':{'claimName': ''}}]}} 
        deploymentDict['metadata']['name'] = backupPodName
        deploymentDict['spec']['containers'][0]['volumeMounts'][0]['mountPath'] = pvMount
        deploymentDict['spec']['volumes'][0]['persistentVolumeClaim']['claimName'] = pvcName
        deploymentDict['metadata']['namespace'] = namespace
        podFile = "pod.yaml"
        pod = open(podFile,'w+')
        yaml.dump(deploymentDict, pod)
        return podFile
    except:
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED: : Exception occured") 

def getLogsFromPod(namespace, since, podType, folderName, podName):
    kubectl_logs = "kubectl logs %s -n %s --since %s > %s/%s.log" %(podName, namespace, since, folderName, podType) 
    logging.info("%s" %kubectl_logs)
    try:
        output = subprocess.check_output("%s" %kubectl_logs , shell=True)
    except subprocess.CalledProcessError:
        traceback.print_exc(file=sys.stdout)
        logging.error(display_colored_text('31m',"ERROR: ") +"No PVC used and hence cannot create backup pod to fetch logs, skipping logs collection and proceeding with code")

def findPVCName(helmResult, namespace, helmchart, since, podType):
    start = helmResult.find("persistentVolumeClaim") + len("persistentVolumeClaim:")
    end = helmResult.find("\n", start)
    if start==-1 or end==-1:
        raise exception("FAILED: : Helm chart details does not contain any field named persistentVolumeClaim to get the PVC name")
    pvcName = helmResult[start:end].strip().strip("\"")
    if len(pvcName) > 0:
        logging.info("PVC name is %s" %pvcName)
        return pvcName
    else:
        logging.info("Persistent Volume for pod is not defined\nReading logs directly from the pod")
        folderName = getLogFolderName(helmchart, podType)
        makeDir(folderName)
        podName = findPodName(namespace, helmchart, podType)
        getLogsFromPod(namespace, since, podType, folderName, podName)
        if podType=="amko":
            getCRD(namespace, folderName)
        elif podType=="ako":
            getConfigmap(namespace, folderName)
        zipDir(folderName)
        print("\nSuccess, Logs zipped into %s.zip\n" %folderName)
        return "done"

def findPVMount(helmResult):
    start = helmResult.find("mountPath") + len("mountPath:")
    end = helmResult.find("\n", start)
    if start==-1 or end==-1:
        raise exception("FAILED: : Helm chart details does not contain any field named mountPath to get the pvc mount path details")
    pvcMount = helmResult[start:end].strip().strip("\"")
    if len(pvcMount) > 0 :
        logging.info("PVC mount point found - %s" %pvcMount)
        return pvcMount[1:]
    else:
        logging.error(display_colored_text('34m',"WARNING: ") + "PV mount path is has no value. Taking /log as the default mount path\n")
        return "/log"

    try: 
        pvMount = helmResult['containers'][0]['volumeMounts'][0]['mountPath']
        return pvMount
    except KeyError:
        raise exception("FAILED : The results of helm get all aren't as expected")

def findLogFileName(helmResult):
    start = helmResult.find("logFile") + len("logFile:")
    end = helmResult.find("\n", start)
    if start==-1 or end==-1:
        raise exception("FAILED: : Helm chart details does not contain any field named logFile to get the amko log file name")
    logFileName = helmResult[start:end].strip().strip("\"")
    if len(logFileName) > 0 :
        logging.info("Log file name is %s" %logFileName)
        return logFileName
    else:
        logging.info("No log file name found in helm results.\nTaking default as amko.log")
        return "amko.log"

def createBackupPod():
    create_backup_pod = "kubectl apply -f pod.yaml"
    logging.info("%s" %create_backup_pod)
    try:
        output = subprocess.check_output("%s" %create_backup_pod, shell=True)
    except subprocess.CalledProcessError:
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED: : Exception occured while creating backup pod custom-backup-pod")

def deletePodFile(podFile):
    rm_file = "rm %s" %podFile
    logging.info("Clean up: %s" %rm_file)
    try:
        output = subprocess.check_output("%s" %rm_file, shell=True)
    except subprocess.CalledProcessError:
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED at clean up stage  : Exception occured while deleting pod.yaml file")

def deleteBackupPod(podName, namespace, podFile):
    delete_pod = "kubectl delete pod custom-backup-pod -n %s" %namespace
    logging.info("Clean up: %s" %delete_pod)
    try:
        output = subprocess.check_output("%s" %delete_pod , shell=True)
    except subprocess.CalledProcessError:
        deletePodFile(podFile)
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED at clean up stage : Exception occured while deleting backup pod custom-backup-pod")

def cleanBackupPod(namespace, podName, podFile):
    time.sleep(25)
    deleteBackupPod(podName, namespace, podFile)
    deletePodFile(podFile)

def zipLogFile(helmchart, namespace, since, podType):
    podName = findPodName(namespace, helmchart, podType)
    statusOfPod = describePod(namespace, podName)
    helmResult = pvHelper(namespace, helmchart)
    pvcName = findPVCName(helmResult, namespace, helmchart, since, podType)
    if pvcName=="done":
        return
    pvMount = findPVMount(helmResult)
    logFileName = findLogFileName(helmResult)
    folderName = getLogFolderName(helmchart, podType)

    #Check if the pod is up and running
    if (re.findall("Status: *Running", statusOfPod) and (re.findall("Restart Count: *0", statusOfPod))):
        makeDir(folderName) 
        copyLogsFromPVC(namespace, podName, pvMount, logFileName, folderName, pvcName, podType)
        getLogsFromPod(namespace, since, "LogsFromConsole", folderName, podName)
        if podType=="amko":
            getCRD(namespace, folderName)
        elif podType=="ako":
            getConfigmap(namespace, folderName)
        zipDir(folderName)
        print("\nSuccess, Logs zipped into %s.zip\n" %folderName)
        return
    else:
        #If pod isnt running, then create backup pod 
        logging.info("Creating backup pod as pod isn't running")
        backupPodName = "custom-backup-pod"
        podFile = editDeploymentFile(backupPodName, pvcName, pvMount, namespace)
        createBackupPod()
        timeout = time.time() + 30
        #Waiting for the Custom backup pod to start running
        while(1):
            statusOfBackupPod = describePod(namespace, backupPodName)
            if (re.findall("Status: *Running", statusOfBackupPod) and (re.findall("Restart Count: *0", statusOfBackupPod))):
                #Once backup pod is running, copy the log file to zip it
                logging.info("Backup pod \'%s\' started" %backupPodName)
                makeDir(folderName)
                copyLogsFromPVC(namespace, backupPodName, pvMount, logFileName, folderName, pvcName, podType)
                if podType=="amko":
                    getCRD(namespace, folderName)
                elif podType=="ako":
                    getConfigmap(namespace, folderName)
                zipDir(folderName)
                cleanBackupPod(namespace, backupPodName, podFile)
                print("\nSuccess, Logs zipped into %s.zip\n" %folderName)
                return
            time.sleep(2)  
            if time.time()>timeout:
                logging.error(display_colored_text('31m',"ERROR: ") + "Timed out when creating backup pod")
                raise exception("FAILED : Timed out") 

def findHelmchartName(namespace, podType):
    get_helm = "helm list -n %s" %namespace
    try:
        logging.info("For %s : %s" %(podType.upper(), get_helm))
        helm = subprocess.check_output("%s" %get_helm, shell=True)
        helm = helm.decode(encoding)
        #print("\n%s\n" %helm)
        allHelm = helm.splitlines()[1:]
        for helmEntry in allHelm:
            helm = helmEntry.split(' ')[0]
            #print("\n%s\n" %patt.findall(helmEntry)[0])
            if patt.findall(helmEntry)[0].find(podType) == -1:
                continue
            return patt.findall(helmEntry)[0].strip(' ')
        logging.error(display_colored_text('31m',"ERROR: No helm chart for %s in %s namespace" %(podType, namespace)))
        raise exception("FAILED : Could not get logs for AKO pod")
    except subprocess.CalledProcessError:
        traceback.print_exc(file=sys.stdout)
        raise exception("FAILED : Could not get helm chart name")

if __name__ == "__main__":
    #Parsing cli arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="General description :\nThe script can fetch logs for both AKO and AMKO pod\nIf AKO pod logs are wanted, \'akoNamespace\' is mandatory, \'since\' arguments is optional.\nIf AMKO pod logs are wanted, \'amkoNamespace\' is mandatory, \'since\' argument is optional.\nEither of akoNamespace or amkoNamespace is mandatory\n")
    parser.add_argument('-ako', '--akoNamespace', help='Namespace in which the AKO pod is present' )
    parser.add_argument('-amko', '--amkoNamespace', help='Namespace in which the AMKO pod is present' )
    parser.add_argument('-s', '--since',default='24h', help='(Optional) For pod not having persistent volume storage the logs since a given time duration can be fetched.\nMention the time as 2s(for 2 seconds) or 4m(for 4 mins) or 24h(for 24 hours)\nExample: if 24h is mentioned, the logs from the last 24 hours are fetched.\nDefault is taken to be 24h' )
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    if (not args.akoNamespace and not args.amkoNamespace):
        print("Either of AKO namespace or AMKO namespace is mandatory\nTry \'python3 get_logs.py --help\' for more info\n\n")
    
    if(args.amkoNamespace):
        try:
            print()
            logging.info("*"*20 + " AMKO " + "*"*20)
            helmchart = findHelmchartName(args.amkoNamespace, "amko")
            zipLogFile(helmchart, args.amkoNamespace, args.since, "amko")
        except exception as e:
            print("\n" + e.msg + "\n")

    if (args.akoNamespace):
        try:
            print()
            logging.info("*"*20 + " AKO " + "*"*20)
            helmchart = findHelmchartName(args.akoNamespace, "ako")
            zipLogFile(helmchart, args.akoNamespace, args.since, "ako")
        except exception as e:
            if args.amkoNamespace:
                print("\n" + e.msg + "\n")

