#coding: utf-8
import ppygui.api as gui

CHANGE = [('F', 6.5597), ("DM", 2)]
#help(gui.Combo)

class CurrencyCombo(gui.Combo):
    def __init__(self, parent):
        gui.Combo.__init__(self, parent, style='list')
        for symbol, curr in CHANGE:
            self.append(symbol)
            
        self.selection = 0
        
class MainFrame(gui.CeFrame):
    def __init__(self):
        gui.CeFrame.__init__(self, title="Euro convertissor")
        self.title = gui.Label(self, "Choose a currency and enter an amount to convert", font=gui.Font(color=(0,0,255)))
        self.edit1 = gui.Edit(self)#, style='number')
        self.currency = CurrencyCombo(self)
        self.edit2 = gui.Edit(self)#, style='number')
        
        self.edit1.bind(update=self.onupdate)
        self.edit2.bind(update=self.onupdate)
        self.currency.bind(selchanged=self.onupdate)
        
        sizer = gui.VBox((5,5,5,5), spacing=5)
        sizer.add(self.title) 
        sizer2 = gui.HBox(spacing=5)
        sizer2.add(self.edit1)
        sizer2.addfixed(self.currency, 40)
        
        sizer3 = gui.HBox(spacing=5)
        sizer3.add(self.edit2)
        sizer3.addfixed(gui.Label(self, u'€'), 40)
        
        sizer.addfixed(sizer2, 20)
        sizer.addfixed(sizer3, 20)
        self.sizer = sizer
        
        self.updating = False
        
    def onupdate(self, event):
        if self.updating:
            return
        #print self.currency.selection
        if event.window is self.edit1:
            fromedit = self.edit1
            toedit = self.edit2
            change = 1.0/CHANGE[self.currency.selection][1]
        elif event.window is self.edit2:
            fromedit = self.edit2
            toedit = self.edit1
            change = CHANGE[self.currency.selection][1]
        elif event.window is self.currency:
            self.edit1.text = ''
            self.edit2.text = ''
            return 
        else:
            raise AssertionError
        self.updating = True    
        amount = fromedit.text
        if amount :
            try :
                amount = float(amount)
                amount2 = amount*change
                amount2 = str(amount2)
            except ValueError:
                amount2 = "Err"
            toedit.text = amount2
        else :
            toedit.text = ''
            
        self.updating = False
        
def main():
    app = gui.Application()
    app.mainframe = MainFrame()
    app.run()
    
if __name__ == '__main__' : main()
