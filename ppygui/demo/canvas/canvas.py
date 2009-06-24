from ppygui.core import *


def rgb(r, g, b):
    return r+(g<<8)+(b<<16)
    
class DrawObject(GuiObject):
    def __init__(self, handle):
        self._handle = handle
        
    def __del__(self):
        DeleteObject(self._handle)
        
class Pen(DrawObject):
    def __init__(self, color=(0,0,0), width=1):
        handle = CreatePen(0, width, rgb(*color))
        DrawObject.__init__(self, handle)
        
default_pen = Pen()

class Bitmap(DrawObject):
    pass
    
class Brush(DrawObject):
    pass

class DrawOperation(GuiObject):
    '''
    DrawOperation instances are returned by the various draw_X
    Canvas method and represents a graphical operation. 
    One can cancel 
    '''
    def __init__(self, canvas=None):
        self.canvas = canvas
    
    def cancel(self):
        if self.canvas is not None:
            self.canvas._operations.remove(self)
        #self.canvas._update_draw()
        
class CombineDrawOperation(list, DrawOperation):
    '''
    A DrawOperation that acts as a container for
    DrawOperation instances.
    '''
    def __init__(self, canvas, operations):
        list.__init__(self, operations)
        DrawOperation.__init__(self, canvas)
        
    def _draw(self, dc):
        for op in self:
            op._draw(dc)
        
class DrawLineOperation(DrawOperation): 
    def __init__(self, canvas, point1, point2, pen):
        DrawOperation.__init__(self, canvas)
#        self._point1 = point1
#        self._point2 = point2
        self._pen = pen
        
        x1, y1 = point1
        x2, y2 = point2
        line = (POINT*2)()
        line[0].x = int(x1)
        line[0].y = int(y1)
        line[1].x = int(x2)
        line[1].y = int(y2)
        
        self._line = line
        
    def _draw(self, dc):
        self.canvas._set_pen(dc, self._pen)
        Polyline(dc, self._line, 2)
        
    #def set_point1(self, value):
    #    pass
        
class DrawLinesOperation(DrawOperation):
    def __init__(self, canvas, points, pen):
        DrawOperation.__init__(self, canvas)
        self._points = points
        self._pen = pen
        
    def _draw(self, dc):
        self.canvas._set_pen(dc, self._pen)
        n = len(self._points)
        pts = (POINT*n)()
        for i in xrange(n):
            x, y = self._points[i]
            pts[i].x = int(x)
            pts[i].y = int(y)
        Polyline(dc, pts, n)

class DrawTextOperation(DrawOperation):
    def __init__(self, canvas, text, pos, font, color):
        DrawOperation.__init__(self, canvas)
        self._text = text
        self._pos = pos
        self._font = font
        self._color = color
        
    def _draw(self, dc):
        x, y = self._pos
        msg = unicode(self._text)
        lmsg = len(msg)
        rc = RECT(x, y, 0, 0)
        self.canvas._set_font(dc, self._font)
        DrawText(dc, msg, lmsg, byref(rc), 0x400)
        DrawText(dc, msg, lmsg, byref(rc), 0x100)
        

class Canvas(Window):
    
    def __init__(self, parent, bkcolor=(255,255,255), scrolled=False, **kw):
        
        Window.__init__(self, parent, **kw)
        self._operations = []
        self.bind(paint=self.on_paint,)
                
        self._hbrbk = CreateSolidBrush(rgb(*bkcolor))
        #self._hpen = None
        self._mdc = None
        self._hbmp = None
        self._hfont = None
        self._need_update = False


    def _set_pen(self, dc, pen):
        SelectObject(dc, pen._handle)
        
    def _set_font(self, dc, font):
#        if self._hfont:
#            DeleteObject(self._hfont)
        SelectObject(dc, font._hFont)
        
    def set_bkcolor(self, color):
        r,g,b = color
        if self._hbrbk:
            DeleteObject(self._hbrbk)
        self._hbrbk = CreateSolidBrush(rgb(r,g,b))
        self.update_draw()
        
    doc_bkcolor = 'The background color as a tuple of ints (red, green, blue)'
    
    def _draw_operations(self, dc, size):
        for op in self._operations:
            op._draw(dc)
        
    def update_draw(self, rect=None):
        if self._need_update :
            return
        self._need_update = True
        InvalidateRect(self._w32_hWnd, byref(self.client_rect), 0)

            
    def on_paint(self, event):
        ps = PAINTSTRUCT()
        hdc = BeginPaint(self._w32_hWnd, byref(ps))
        rc = self.client_rect
        r, b =  rc.right, rc.bottom
        #SetBkColor(hdc, 0xff0000)
        if not self._mdc :
            mdc = CreateCompatibleDC(hdc)
            hbmp = CreateCompatibleBitmap(hdc, r, b)
            SelectObject(mdc, hbmp)
            FillRect(mdc, byref(rc), self._hbrbk)
            size = r, b
            self._draw_operations(mdc, size)
            self._mdc = mdc
            self._hbmp = hbmp
            self._canvassize = size
            self._need_update = False
            
        size = r, b
        #print self._canvassize, size 
        if self._canvassize[0] < r or self._canvassize[1] < b :
            #print 'need update'
            DeleteDC(self._mdc)
            DeleteObject(self._hbmp)
            mdc = CreateCompatibleDC(hdc)
            hbmp = CreateCompatibleBitmap(hdc, r, b)
      
            SelectObject(mdc, hbmp)
            self._mdc = mdc
            self._hbmp = hbmp
            self._need_update = True
            
        if self._need_update:
            FillRect(self._mdc, byref(rc), self._hbrbk)
            self._draw_operations(self._mdc, size)
            
        
        BitBlt(hdc, 0, 0, r, b, self._mdc, 0, 0, SRCCOPY)
        EndPaint(self._w32_hWnd, byref(ps))
        self._need_update = False
        self._canvassize = size
        
    def get_operations(self):
        return self._operations
        
    doc_operations = '''
    The list of current drawing operations of the canvas.
    This list is populated by DrawOperation instances.
    One can affect the rendering of the canvas by inserting,
    appending, removing DrawOperation instances.
    '''
    
    def clear(self):
        '''
        Cancel all drawing operations
        '''
        self._operations = []
        #self._update_draw()
        
    def draw_line(self, point1, point2, pen=default_pen):
        '''
        Draw a line between point1 and point2 with the 
        Pen instance pen. point1 and point2 must be tuples
        of int (x, y). 
        Return a new DrawLineOperation corresponding to
        this operation
        '''
        #self._operations.append(['line', width, color, point1, point2])
        #self._update_draw(RECT(point1[0], point1[1], point2[0], point2[1]))
        op = DrawLineOperation(self, point1, point2, pen)
        self._operations.append(op)
        #self._update_draw()
        return op
        
    def draw_lines(self, points, pen=default_pen):
        #self._operations.append(['lines', width, color]+list(points))
        op = DrawLinesOperation(self, points, color, width)
        self._operations.append(op)
        #self._update_draw()
        return op

    def draw_text(self, text, pos, font=DefaultFont, color=(0,0,0)):
        op = DrawTextOperation(self, text, pos, font, color)
        #self._operations.append(['text', text, pos, font, color])
        self._operations.append(op)
        #self._update_draw()
        return op
        
    def draw_image(self, image, pos):
        pass
        
    def __del__(self):
        if self._mdc :
            DeleteDC(self._mdc)
        if self._hbmp:
            DeleteObject(self._hbmp)
#        if self._hpen:
#            DeleteObject(self._hpen)
        DeleteObject(self._hbrbk)