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
       
       # Place our controls in a vertical box
       sizer = gui.VBox(border=(2,2,2,2), spacing=2)
       sizer.add(self.text_entry)
       sizer.add(self.button)
       sizer.add(self.label)
       
       # Set the vertical box as our main frame sizer
       self.sizer = sizer
       
       # Set the event handler for the button clicked event
       self.button.bind(clicked=self.on_click)
# Set the event handler for the edit update event
       self.text_entry.bind(update=self.on_text_update)
      
    def on_click(self, event):
        # The code of our event handler
        print "The button %s is clicked" %event.window
           
    def on_text_update(self, event):
        # The code of our event handler
        print "The text of edit control %s was changed" %event.window
           
if __name__ == '__main__':
 app = gui.Application(MainFrame())
 # create an application bound to our main frame instance
 app.run()
 #launch the app !