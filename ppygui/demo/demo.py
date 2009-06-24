import ppygui.api as gui

class LabelPage(gui.Frame):
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.lb1 = gui.Label(self, "Normal label",
                             font=gui.Font(color=(255,0,0)))
                             
        self.lb2 = gui.Label(self, "Center label", 
                             align="center", 
                             font=gui.Font(size=8,color=(0,255,0)))
        
        self.lb3 = gui.Label(self, "Right label", 
                             align="right",
                             font=gui.Font(color=(0,0,255)))
        
        self.lb4 = gui.Label(self, "A\nMulti-line\nLabel", align="center")
        self.lb4b = gui.Label(self, "A\nMulti-line\nLabel\nwith border", 
                              align="center", border=True)
        self.lb5 = gui.Label(self, "Click me", align="center")
        self.lb5.bind(clicked=self.on_label_clicked)
        
        sizer = gui.VBox((2,2,2,2), spacing=2)
        sizer.add(self.lb1)
        sizer.add(self.lb2)
        sizer.add(self.lb3)
        sizer.add(self.lb4, 1)
        sizer.add(self.lb4b, 1)
        sizer.add(self.lb5, 1)
        self.sizer = sizer
        self.sipp = gui.SIPPref(self)
        
    def on_label_clicked(self, evt):
        self.lb5.text += " again"
        
class ButtonPage(gui.Frame):
    #_w32_window_style_ex = 0x0
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        
        self.b1 = gui.Button(self, "A normal button", 
                             action=self.on_click)
        self.b2 = gui.Button(self, "A colored button", 
                             style="default", 
                             action=self.on_click, 
                             font=gui.Font(color=(255,0,0), bold=True))
        self.b3 = gui.Button(self, "A checkbox (I'm unchecked)", 
                             style="check", 
                             action=self.on_check)
        #self.b3
        self.lb1 = gui.Label(self, "Cheese shop:", 
                             align="center", 
                             font=gui.Font(size=20, bold=True))
        self.radiogroup = gui.RadioGroup()
        self.rb1 = gui.RadioButton(self, 
                                   "Red Leicester", 
                                   group=self.radiogroup, 
                                   value="Sorry we're fresh out of red leicester",
                                   selected=True)
        self.rb2 = gui.RadioButton(self, "Cheddar", group=self.radiogroup, value="Cheddar")
        #self.rb2 = gui.RadioButton(self, "Cheddar", self.radiogroup, "Cheddar")
        self.radiogroup.bind(update=self.on_cheese)
        self.lb2 = gui.Label(self, "")
        sizer = gui.VBox((2,2,2,2), spacing=2)
        sizer.add(self.b1)
        sizer.add(self.b2)
        sizer.add(self.b3)
        sizer.add(self.lb1)#, border=(2,2,2,2))
        sizer.add(self.rb1)
        sizer.add(self.rb2)
        sizer.add(self.lb2)
        self.sizer = sizer
        self.sipp = gui.SIPPref(self)
        
    def on_check(self, event):
        if self.b3.checked:
            self.b3.text = "A checkbox (I'm checked)"
        else:
            self.b3.text = "A checkbox (I'm unchecked)"
    
    def on_click(self, event):
        button = event.window
        button.text += " clicked"
        
    def on_cheese(self, event):
        response = self.radiogroup.value
        self.lb2.text = response
    
class EditPage(gui.Frame):
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.ed1 = gui.Edit(self, "Normal edit")
        self.ed2 = gui.Edit(self, "Read-only edit")
        self.ed2.readonly = True
        self.ed3 = gui.Edit(self, "Numeric edit", style="number")
        self.ed4 = gui.Edit(self, "Password", password=True)
        self.ed5 = gui.Edit(self, "Multiline centered edit", 
                            align="center", multiline=True)
        self.sipp = gui.SIPPref(self)
        
        sizer = gui.VBox(border=(2,2,2,2), spacing=2)
        sizer.add(self.ed1)
        sizer.add(self.ed2)
        sizer.add(self.ed3)
        sizer.add(self.ed4)
        sizer.add(self.ed5, 1)
        
        self.sizer = sizer
        
class ListPage(gui.Frame):
    CHOICES = ['a', 'b', 'c'] *15
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.list = gui.List(self, choices=self.CHOICES)
        self.list.bind(selchanged=self.on_list_choice)
        self.label_1 = gui.Label(self)
        self.combo = gui.Combo(self, style='list', choices=self.CHOICES)
        self.combo.bind(selchanged=self.on_combo_choice)
        self.label_1 = gui.Label(self)
        sizer = gui.VBox((2,2,2,2))
        sizer.add(self.list)
        sizer.add(self.label_1)
        sizer.add(self.combo)
        
        self.sizer = sizer
        
    def on_list_choice(self, evt):
        self.label_1.text = "Your selection: %s" \
            %self.CHOICES[self.list.selection]
            
    def on_combo_choice(self, evt):
        self.label_1.text = "Your selection: %s" \
            %self.CHOICES[self.combo.selection]

class TablePage(gui.Frame):
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.table = gui.Table(self, multiple=True, autoadjust=False)
        self.table.columns.append("x")
        self.table.redraw = False
        for i in range(2, 5):
            self.table.columns.append("x**%i" %i)
        
        for i in range(250):
            self.table.rows.append([str(i**n) for n in xrange(1, 5)])
        
        sizer = gui.VSizer()
        sizer.add(self.table)
        self.sizer = sizer
        self.table.redraw = True
        self.table.adjust_all()
        
class CommonDialogPage(gui.Frame):
    def __init__(self, parent):
        gui.Frame.__init__(self, parent)
        self.button_1 = gui.Button(self, "Open a file", action=self.on_open)
        self.button_2 = gui.Button(self, "Save a file", action=self.on_save)
        label_1 = gui.Label(self, "Message type: ")
        self.combo_1 = gui.Combo(self, choices=['ok', 'okcancel', 'yesno', 'yesnocancel' ], style="list")
        self.combo_1.selection = 0
        
        label_2 = gui.Label(self, "Message icon: ")
        self.combo_2 = gui.Combo(self, choices=['info', 'warning', 'error', 'question' ], style="list")
        self.combo_2.selection = 0
        
        self.button_3 = gui.Button(self, "Message Dialog", action=self.on_msg)
        self.label_ret_value = gui.Label(self)
        sizer = gui.VBox((2,2,2,2), spacing=2)
        sizer.add(self.button_1)
        sizer.add(self.button_2)
        
        table = gui.TBox(2,2, spacing_x=2, spacing_y=2)
        table.add(label_1)
        table.add(self.combo_1)
        table.add(label_2)
        table.add(self.combo_2)
        
        sizer.add(table)
        sizer.add(self.button_3)
        sizer.add(self.label_ret_value)
        self.sizer = sizer
        
    def on_open(self, ev):
        ret = gui.FileDialog.open()
        self.label_ret_value.text = "Return value: %s" %ret
        
    def on_save(self, ev):
        ret = gui.FileDialog.save()
        self.label_ret_value.text = "Return value: %s" %ret
        
    def on_msg(self, ev):
        msg_type = self.combo_1.selection
        if msg_type == 0:
            msg_func = gui.Message.ok
        elif msg_type == 1:
            msg_func = gui.Message.okcancel
        elif msg_type == 2:
            msg_func = gui.Message.yesno
        elif msg_type == 3:
            msg_func = gui.Message.yesnocancel
        icon = self.combo_2[self.combo_2.selection]
        ret = msg_func('Title', 'Message', icon=icon, parent=self.parent)
        
        self.label_ret_value.text = "Return value: %s" %ret

class TreePage(gui.Frame):
    pass
    
class HtmlPage(gui.Frame):
    pass
    
class OtherPage(gui.Frame):
    pass
    
class DemoBook(gui.NoteBook):
    PAGES = [('Labels', LabelPage),
             ('Buttons', ButtonPage),
             ('Edits', EditPage),
             ('Lists', ListPage),
             ('Tables', TablePage),
             ('Common dialogs', CommonDialogPage),
            ]
    
    def __init__(self, parent):
        gui.NoteBook.__init__(self, parent)
        for title, klass in self.PAGES:
            self.append(title, klass(self))
        self.selection = 0
        
class MainFrame(gui.CeFrame):
    def __init__(self):
        gui.CeFrame.__init__(self, 
            title="PPyGui Demo",
            action=("About", self.on_about),
            menu="Demo")
            
        for i, (page, klass) in enumerate(DemoBook.PAGES):
            self.cb_menu.append(page, callback=self._menu_cb(i))
        self.nb = DemoBook(self)
        self.sipp = gui.SIPPref(self)
        
        sizer = gui.VSizer()
        sizer.add(self.nb)
        self.sizer = sizer
    
    def _menu_cb(self, i):
        def cb(event):
            self.nb.selection = i
        return cb
        
    def on_about(self, ev):
        gui.Message.ok("About", "Ppygui demo", "info", self)
        
if __name__ == '__main__' :
    app = gui.Application(MainFrame())
    app.run()