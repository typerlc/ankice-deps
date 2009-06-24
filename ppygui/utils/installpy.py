import os
import glob
import shutil

def installpy(installpath, ppyguipath):
    installpath = os.path.join(installpath, "Lib")
    installpath = os.path.join(installpath, "site-packages")
    installpath = os.path.join(installpath, "ppygui")
    
    if not os.path.exists(installpath) :
        os.makedirs(installpath)
    
    for py in glob.glob("%s/*.py" %ppyguipath):
        shutil.copy(py, installpath)
        
#    if pyceguizip.endswith(".zip"):    
#        shutil.copy(pyceguizip, installpath)
#        pthfilepath = os.path.join(installpath, "pycegui.pth")
#        pthfile = open(pthfilepath, "w")
#        pthfile.write("pycegui.zip")
#        pthfile.close()

        
