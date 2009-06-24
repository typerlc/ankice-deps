from math import cos, sin, pi
from time import sleep, time
from datetime import datetime
from threading import Thread
import ppygui as gui
from canvas import Canvas, Pen, CombineDrawOperation, \
    DrawLineOperation

class AnalogClock(Canvas):
    def __init__(self, parent):
        Canvas.__init__(self, parent)
        self.pen_cadre_1 = Pen((0,0,250), 2)
        self.pen_cadre_2 = Pen(width=3)
        self.pen_aiguille_1 = Pen(width=6)
        self.pen_aiguille_2 = Pen(width=5)
        self.pen_aiguille_3 = Pen(width=2, color=(255,0,0))
        
        self.bind(size=self.on_size)
        #self._draw_cadre()
        self.aiguille_draw_op = CombineDrawOperation(self, [])
        self.scheduler = Thread(target=self.schedule)
        self.scheduler.start()
        
    def _get_metrics(self):
        w, h = self.size
        if h>w:
            R = w
        else:
            R = h
        return w, h, R/2 - 5
        
    def _draw_cadre(self):
        w, h, R = self._get_metrics()
        for i in range(60):
            angle = i*2*pi/60
            pt1 = (R-5)*cos(angle)+w/2, (R-5)*sin(angle)+h/2
            pt2 = R*cos(angle)+w/2, R*sin(angle)+h/2
            self.draw_line(pt1, pt2, self.pen_cadre_1)
            
        for i in range(12):
            angle = i*2*pi/12
            pt1 = (R-5)*cos(angle)+w/2, (R-5)*sin(angle)+h/2
            pt2 = R*cos(angle)+w/2, R*sin(angle)+h/2
            self.draw_line(pt1, pt2, self.pen_cadre_2)# color=(12,12,12))
            
    def _draw_aiguille(self):
        #for op in self.aiguille_draw_op :
        #   op.cancel()
        #self.clear()
        #
        try:
            self.aiguille_draw_op.cancel()
        except :
            pass
        del self.aiguille_draw_op[:]
        
        w, h, R = self._get_metrics()
        t = datetime.now()
        hour, minute, second = t.hour, t.minute, t.second
        angle = pi*(hour/6.0 + minute/(6.0*60) - 0.5)
        pt1 = w/2, h/2
        pt2 = (R/2)*cos(angle)+w/2, (R/2)*sin(angle)+h/2
        #self.aiguille_draw_op.append(self.draw_line(pt1, pt2, self.pen_aiguille_1))
        op = DrawLineOperation(self, pt1, pt2, self.pen_aiguille_1)
        self.aiguille_draw_op.append(op)
        
        
        angle = pi*(minute/30.0 +second/(30.0*60) - 0.5)
        pt1 = w/2, h/2
        pt2 = (R*0.70)*cos(angle)+w/2, (R*0.70)*sin(angle)+h/2
        #self.aiguille_draw_op.append(self.draw_line(pt1, pt2, self.pen_aiguille_2))
        op = DrawLineOperation(self, pt1, pt2, self.pen_aiguille_2)
        self.aiguille_draw_op.append(op)
        
        angle = pi*(second/(30.0) - 0.5)
        pt1 = w/2, h/2
        pt2 = (R*0.75)*cos(angle)+w/2, (R*0.75)*sin(angle)+h/2
        op = DrawLineOperation(self, pt1, pt2, self.pen_aiguille_3)
        self.aiguille_draw_op.append(op)
        
        self.operations.append(self.aiguille_draw_op)
        
    def on_size(self, event):
        self.clear()
        self._draw_cadre()
        self._draw_aiguille()
        self.update_draw()
        
    def schedule(self):
        last_t = int(time())
        while 1:
            sleep(0.05)
            t = int(time())
            if t != last_t:
                gui.schedule(self._draw_aiguille)
                gui.schedule(self.update_draw)
            last_t = t
        
class MainFrame(gui.CeFrame):
    def __init__(self):
        gui.CeFrame.__init__(self, title="Alarm")
        self.aclock = AnalogClock(self)
        sizer = gui.VSizer()
        sizer.add(self.aclock)
        self.sizer = sizer
        
if __name__ == '__main__' :
    app = gui.Application(MainFrame())
    app.run()