from ppygui.core import *
from ppygui.w32comctl import *

class ImageList(GuiObject):
    def __init__(self, cx, cy, flags=1):
        self._hImageList = ImageList_Create(cx, cy, flags, 0, 1)
            
    def add_from_resource(self, resource_dll, icons, cx, cy, flags=0):
        LoadLibrary(unicode(resource_dll))
        hdll = GetModuleHandle(unicode(resource_dll))
        for i in icons:
            hIcon = LoadImage(hdll, i, IMAGE_ICON, cx, cy, flags)
            ImageList_AddIcon(self._hImageList, hIcon)
            
            
    def __del__(self):
        ImageList_Destroy(self._hImageList)
    
import ppygui as gui
class MainFrame(gui.CeFrame):
    def __init__(self):
        gui.CeFrame.__init__(self, title="Test")
        il = ImageList(32, 32)
        #il.add_from_resource(u"\\windows\\browsres.dll", [0, 160, 161, 162], 32, 32)
        il.add_from_resource(u"\\outlinerres.dll", [101, 102, 103], 24, 24)
        self.tree = gui.Tree(self)
        root = self.tree.add_root("Hello", image=0, image_selected=1)
        for i in range(10):
            root.append("Hey", image=i, image_selected=i+1)
        
        self.tree.image_list = il
        sizer = gui.VSizer()
        sizer.add(self.tree)
        self.sizer = sizer
        
        self.il = il
        

##    il = ImageList(32, 32)
#    print LoadLibrary(u"\\windows\\browsres.dll")
#    LoadLibrary(u"\\pyceres.dll")
##    il.add_from_resource(r"\PYCERES.DLL", 32, 32)
#    app = gui.Application(MainFrame())
#    app.run()
def list_icons(dll):
    LoadLibrary(unicode(dll))
    hdll = GetModuleHandle(unicode(dll))
    for i in range(500):
        try:
            hIcon = LoadImage(hdll, i, IMAGE_ICON, 32, 32, 0)
            print i
        except:
            pass
            
if __name__ == '__main__' :
#    print LoadLibrary(u"\\windows\\browsres.dll")
    LoadLibrary(u"\\outlinerres.dll")
##    il.add_from_resource(r"\PYCERES.DLL", 32, 32)
    app = gui.Application(MainFrame())
    app.run()
#    #list_icons("\\windows\\browsres.dll")
    #list_icons("\\outlinerres.dll")