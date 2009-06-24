import ppygui as gui
# import the gui namespace

class MainFrame(gui.CeFrame):
# subclass to create our own main frame type
    def __init__(self):
         gui.CeFrame.__init__(self, title="Hello World")
         # Create some child control
         self.text_entry = gui.Edit(self)
         self.button = gui.Button(self, "Copy")
         self.label = gui.Label(self)
         
if __name__ == '__main__':
   app = gui.Application(MainFrame())
   # create an application bound to our main frame instance
   app.run()
   #launch the app !

