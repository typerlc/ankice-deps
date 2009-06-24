import os
import sys

try :
    import ppygui as gui
except ImportError:
    # Reserved for future setups with a pre byte-compiled
    # archive.
    PPYGUIZIPPATH = os.path.join(os.path.abspath(os.getcwd()), "ppygui.zip")
    sys.path.append(PPYGUIZIPPATH)
    import ppygui as gui

from utils.findpy import findpyceinstall
from utils.installpy import installpy

WELCOMETEMPLATE = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
<h1 style="text-align: center;"><img style="height: 20px; width: 20px;" alt="PPyGui" src="file://%s" /> PPyGui Installer</h1>
<h4 style="text-align: center;"><small>Alexandre Delattre &copy; 2007 </small></h4>
<br />
Welcome to the PocketPyGui setup.<br />
This wizard will guide you through the installation process.<br />
</div>
</body>
</html>
'''

WELCOME = '''Please read the license agreement : '''

LICENSE = '''\
PocketPyGui (c) Alexandre Delattre 2007
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE'''.replace('\n', '\r\n')

PAGE2TEXT = '''Please choose a PythonCE installation :'''

ENDTEMPLATE = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
<h1 style="text-align: center;"><img style="height: 20px; width: 20px;" alt="PPyGui" src="file://%s" />PPyGui Installer</h1>
<h4 style="text-align: center;"><small>Alexandre Delattre &copy; 2007 </small></h4>
Congratulations you've just installed PocketPyGui!<br/>
What to do next:<br/>
<ul>
    <li>Try the examples in the demo directory</li>
    <li>Read the generated doc</li>
    <li>Look at this installer source for another sample code</li>
</ul>    
</body>
</html>
'''

class WelcomePage(gui.Frame):
    
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.html = gui.Html(self, zoom_level = 0)
        self.html.value = WELCOMETEMPLATE \
            %os.path.abspath('python.bmp')
        self.bnext = gui.Button(self, "Next")
        
        sizer = gui.VBox(border=(5,5,5,5))
        sizer.add(self.html, 1)
        sizer2 = gui.HBox(spacing=5)
        sizer2.add(gui.Spacer(0, 0), 1)
        sizer2.add(self.bnext, 1)
        sizer.add(sizer2)
        self.sizer = sizer
        
    def setcallback(self, nextcb):
        self.bnext.bind(clicked=nextcb)
        
class EndPage(gui.Frame):
    
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.html = gui.Html(self, zoom_level = 0)
        self.html.value = ENDTEMPLATE \
            %os.path.abspath('python.bmp')
        self.bnext = gui.Button(self, "Close")
        self.bnext.bind(clicked=self.onclose)
        
        sizer = gui.VBox(border=(5,5,5,5))
        sizer.add(self.html, 1)
        sizer2 = gui.HBox(spacing=2)
        sizer2.add(gui.Spacer(0, 0), 1)
        sizer2.add(self.bnext, 1)
        sizer.add(sizer2)
        self.sizer = sizer
    
    def onclose(self, evt):
        self.parent.destroy()
        
class Page1(gui.Frame):
    
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)

        self.label = gui.Label(self, WELCOME)
        self.license = gui.Edit(self, LICENSE, multiline=True)
        self.license.readonly = True
        self.license.font = gui.Font(size=7)
        self.accept = gui.Button(self, "I accept the license agreement", style="check", action=self.onaccept)
        self.accept.font = gui.Font(size=8, bold=True)
        self.bcancel = gui.Button(self, "Cancel")
        self.bnext = gui.Button(self, "Next")
        self.bnext.disable()
        
        
        sizer = gui.VBox((5,5,5,5), spacing=5)
        sizer.add(self.label)
        sizer.add(self.license, 1)
        sizer.add(self.accept)
        sizer2 = gui.HBox(spacing=5)
        sizer2.add(self.bcancel, 1)
        sizer2.add(self.bnext, 1)
        
        sizer.add(sizer2)
        
        self.sizer = sizer
        
    def setcallback(self, cancelcb, nextcb):
        self.bcancel.events['clicked'].bind(cancelcb)
        self.bnext.events['clicked'].bind(nextcb)
        
        
    def onaccept(self, event):
        self.bnext.enable(self.accept.checked)
        
class Page2(gui.Frame):
    
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.pyinstalls = findpyceinstall()
        choices = ["Python %s (found in registry)" %(version) for version, path in self.pyinstalls]
        
        self.title = gui.Label(self, PAGE2TEXT)
        self.pychoice = gui.List(self, choices=choices, sort=False)
        self.pychoice.bind(selchanged=self.onchoicechanged)
        self.bcancel = gui.Button(self, "Cancel")
        self.bnext = gui.Button(self, "Next")
        self.bnext.disable()
        
        
        sizer = gui.VBox((5,5,5,5), spacing=5)
        sizer.add(self.title)
        sizer.add(self.pychoice, 1)
        sizer2 = gui.HBox(spacing=5)
        sizer2.add(self.bcancel, 1)
        sizer2.add(self.bnext, 1)
        sizer.add(sizer2)
        self.sizer = sizer
    
    def onchoicechanged(self, event):
        self.bnext.enable()
        
    def setcallback(self, cancelcb, nextcb):
        self.bcancel.bind(clicked=cancelcb)
        self.bnext.bind(clicked=nextcb)
        self.pychoice.bind(itemactivated=nextcb)
        
    def getinstallpath(self):
        if self.pychoice.selection is not None:
            return self.pyinstalls[self.pychoice.selection][1]
        
class MainFrame(gui.CeFrame):
    
    def __init__(self):
        gui.CeFrame.__init__(self, title="PPyGui installer")
        self.finished = False
        self.events['close'].bind(self.onclose)
        
        self.page0 = WelcomePage(self)
        self.page0.setcallback(self.onnext0)
        sizer0 = gui.VSizer()
        sizer0.add(self.page0)
        self.set_sizer(sizer0)
        
    def oncancel(self, event):
        self.close()
    
    def onclose(self, event):
        if self.finished :
            event.skip()
        else :
            if gui.Message.yesno("Abort", "Abort setup ?", 'question', self) == 'yes':
                event.skip()
            else :
                pass
    
    def onnext0(self, event):
        self.page1 = Page1(self)
        self.page1.setcallback(self.oncancel, self.onnext1)
        sizer1 = gui.VSizer()
        sizer1.add(self.page1)
        self.sizer = sizer1
        self.page1.focus()
        self.page0.hide()
        self.page0.destroy()
        del self.page0
        
           
    def onnext1(self, event):
        self.page1.destroy()
        del self.page1
        
        self.page2 = Page2(self)
        self.page2.setcallback(self.oncancel, self.onnext2)
        sizer2 = gui.Sizer('vertical')
        sizer2.add(self.page2)
        self.sizer = sizer2
        self.page2.focus()
        
    def onnext2(self, event):
        installpath = self.page2.getinstallpath()
        if installpath:
            if gui.Message.yesno("Confirmation", "Install ppygui to %s ?" %installpath, 'question', self) == 'yes':
                cur = gui.BusyCursor()
                try :
                    #installpy(installpath, PYCEGUIZIPPATH)
                    installpy(installpath, os.path.abspath('ppygui')) 
                except Exception, e :
                    msg = "There was an error during the installation : %s" %e
                    msg = msg.decode('iso-8859-1')
                    raise e
                    gui.Message.ok("Error", msg, "error", self) 
                else :
                    gui.Message.ok("Success", "Ppygui has been installed on your handheld", parent=self)
                    self.endframe = EndPage(self)
                    self.page2.destroy()
                    sizer3 = gui.VSizer()
                    sizer3.add(self.endframe)
                    self.sizer = sizer3 
                    self.endframe.focus()
                #self.destroy()
            
       
class SetupApp(gui.Application):
    def __init__(self):
        gui.Application.__init__(self)
        self.mainframe = MainFrame()

def main():
    app = SetupApp()
    app.run()
    
if __name__ == '__main__' : main()