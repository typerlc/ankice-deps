from _winreg import HKEY_LOCAL_MACHINE as HKLM
from _winreg import OpenKey, EnumKey, EnumValue

def keyiterator(key):
    i = 0
    while 1 :
        try :
            yield EnumKey(key, i)
            i += 1
        except: 
            break
            
            
def findpyceinstall():
    
    softkey = OpenKey(HKLM, 'Software')
    pykeys = [OpenKey(softkey, key) 
                for key in keyiterator(softkey) 
                if key.lower().startswith("python")
             ]
    
    return [getpykeyinfo(pykey) for pykey in pykeys]
    
def getpykeyinfo(pykey):
    pycorekey = OpenKey(pykey, 'PythonCore')
    version = EnumKey(pycorekey, 0)
    installpathkey = OpenKey(OpenKey(pycorekey, version), "InstallPath")
    value, path, index = EnumValue(installpathkey, 0)
    return version, path
    
if __name__ == '__main__' :
    print findpyceinstall()
    import dis
    dis.dis(findpyceinstall)