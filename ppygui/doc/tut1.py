import ppygui as gui
# import the gui namespace

class MainFrame(gui.CeFrame):
# subclass to create our own main frame type
    def __init__(self):
         gui.CeFrame.__init__(self, title="Hello World")
         
if __name__ == '__main__':
   app = gui.Application(MainFrame())
   # create an application bound to our main frame instance
   app.run()
   #launch the app !

