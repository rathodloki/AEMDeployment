import requests,json,re,git,os,pyaem2
from requests.auth import HTTPBasicAuth
from datetime import date,datetime

#Environment
env=["SIT",ipadd]

#Starting Local AEM jar
def aemStart():
    os.chdir("E:/projects/tata-capital-nli/aem-author")
    os.system("jps -mlvv | findstr 4502 > jps.txt")
    if(re.search("AEM_6.4_Quickstart.jar",open("jps.txt").read())):
       print("AEM is already started.")
    else:
        import time,subprocess
        print("AEM is getting Starting Please Wait.....")
        subprocess.Popen(["javaw","-jar","AEM_6.4_Quickstart.jar","-r","author","-p","4502","-gui"])
        print("loading")
        for i in range(40):
            print(".",end='',flush=True)
            time.sleep(0.2)
        time.sleep(50)
        
#Taking git pull
def gitRepo():
    print ("Taking Pull")
    RepoDir = git.Repo( 'https://github.com/repo')
    print(RepoDir.git.checkout( branch ))
    os.chdir("cloned repo directory")
    o = RepoDir.remotes.origin
    o.pull()

#building using maven
def mvnClean():
    print ("Building Project")
    os.chdir('Project dir where the pom.xml present')
    StatusCode=os.system("mvn clean install -PautoInstallPackage > MavenStatus.txt")
    if (StatusCode != 0):
        print("UnSuccessfull Maven!")
        os._exit(1)

#find existing package in aem        
def existingRelease():    
    r=requests.get('http://localhost:4502/crx/packmgr/list.jsp', 
                auth = HTTPBasicAuth('admin', 'admin')) 
    api=json.loads(r.text)
    PkgDetails=[]
    for i in range(len(api['results'])):
        if(re.search("ProjectName-"+env[0]+"-Release*",api['results'][i]['downloadName'])): #Search for package name
            PkgDetails.append(api['results'][i]['name'])
            PkgDetails.append(api['results'][i]['version'])
            PkgDetails.append(api['results'][i]['downloadName'])
            return PkgDetails
            break

#api for update verison and name
def crxApiUpdate(url):
    payload = {}
    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Basic YWRtaW46YWRtaW4='
    }
    response = requests.request("GET", url, headers=headers, data = payload)
    return response.text.encode('utf8')

#update verison and name
def aemUpdate():
    print ("Updating Local Release")
    aem=pyaem2.PyAem2('admin', 'admin', 'localhost', 4502)
    PkgName=existingRelease()[0]
    PkgVersion=float(existingRelease()[1])
    pkgDownloadName=existingRelease()[2]
    if(str('-'.join(re.split('-',PkgName)[:2:-1]))==str(date.today())):
        PkgVersion=round(PkgVersion+0.1,1)
        print (crxApiUpdate("http://localhost:4502/crx/packmgr/update.jsp?groupName=groupName&packageName=ProjectName-"+env[0]+"-Release-"+datetime.today().strftime('%d-%m-%Y')+"&version="+str(PkgVersion)+"&path=/eProjectName/packages/groupName/"+pkgDownloadName))
        aem.build_package('groupName', 'ProjectName-'+env[0]+'-Release-'+datetime.today().strftime('%d-%m-%Y'), str(PkgVersion))
        aem.download_package('groupName', 'ProjectName-'+env[0]+'-Release-'+datetime.today().strftime('%d-%m-%Y'), str(PkgVersion), 'Download dir')
    else:
        print (crxApiUpdate("http://localhost:4502/crx/packmgr/update.jsp?groupName=groupName&packageName=ProjectName-"+env[0]+"-Release-"+datetime.today().strftime('%d-%m-%Y')+"&version=1.0&path=/eProjectName/packages/groupName/"+pkgDownloadName))
        aem.build_package('groupName', 'ProjectName-'+env[0]+'-Release-'+datetime.today().strftime('%d-%m-%Y'), '1.0')
        aem.download_package('groupName', 'ProjectName-'+env[0]+'-Release-'+datetime.today().strftime('%d-%m-%Y'), "1.0", 'Download_Dir')

#Deploy to the environment
def aemDeploy():
    print ("Deploying Release")
    PkgName=existingRelease()[0]
    PkgVersion=float(existingRelease()[1])
    pkgDownloadName=existingRelease()[2]
    aem=pyaem2.PyAem2('admin', 'admin', env[1], 4502)
    #Uploading
    os.system("curl -u admin:admin -F cmd=upload -F force=true -F package=@Download_Dir/"+str(pkgDownloadName)+" http://"+env[1]+":4502/crx/packmgr/service/.json")
    #installing
    os.system("curl -u admin:admin -X POST http://"+env[1]+":4502/crx/packmgr/service/.json/eProjectName/packages/groupName/"+str(pkgDownloadName)+"?cmd=install")

#Replicating to Publishers    
def aemReplicate():
    print("Replicating")
    import win32api,win32con
    PkgName=existingRelease()[0]
    PkgVersion=float(existingRelease()[1])
    pkgDownloadName=existingRelease()[2]
    
    win32api.MessageBeep(win32con.MB_ICONERROR)
    isReplicate=win32api.MessageBox(0, "Replcating to "+env[0]+" pub", "Replication",win32con.MB_ICONQUESTION | win32con.MB_YESNO |win32con.MB_DEFAULT_DESKTOP_ONLY| win32con.MB_TOPMOST)
    if(isReplicate==6):
        print("replicating....")
        replicateStatus=os.system("curl -u admin:admin -X POST http://"+env[1]+":4502/crx/packmgr/service/.json/eProjectName/packages/groupName/"+pkgDownloadName+"?cmd=replicate")
        #checking error in replication
        if(replicateStatus != 0):
            in32api.MessageBeep(win32con.MB_ICONERROR)
            win32api.MessageBox(0, "Replcation Failed on "+env[0]+"", "Replication Failed on "+env[0]+"!!!",win32con.MB_ICONERROR  |win32con.MB_DEFAULT_DESKTOP_ONLY| win32con.MB_TOPMOST)
        else:
            win32api.MessageBeep(win32con.MB_ICONINFORMATION)    
            win32api.MessageBox(0, "Done on "+env[0]+" ALL", "Replication done on "+env[0]+" ALL",win32con.MB_ICONASTERISK | win32con.MB_DEFAULT_DESKTOP_ONLY|win32con.MB_TOPMOST)
    else:
        print("don't replicate")
        win32api.MessageBeep(win32con.MB_ICONINFORMATION)
        win32api.MessageBox(0, "Done on "+env[0]+" Author", "didn't Replicate on "+env[0]+" pub",win32con.MB_DEFAULT_DESKTOP_ONLY|win32con.MB_ICONEXCLAMATION)
        
aemStart()
gitRepo()
mvnClean()
aemUpdate()
aemDeploy()
aemReplicate()
