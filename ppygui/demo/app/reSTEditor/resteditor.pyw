import os
import sys
import ppygui as gui

def dummy_exit(code=0):
    print code
sys.exit = dummy_exit    
#sys.stdout = None

from docutils.core import publish_string, publish_cmdline

try:
    from pygmentize import register_directive
    register_directive()
except ImportError:
    print "resteditor.py: pygments support disabled"
    print "please install pygments for code highlightning"
    
def render_preview(source):
    source = unicode(source)
    return publish_string(source, writer_name="html", settings_overrides={'output_encoding': 'unicode', 'input_encoding': 'unicode'})

def _prepare_argv(*args, **options):
    argv = [sys.argv[0]]
    argv += args[:]
    for option in options.items():
        argv.append("--%s=%s" %option)
    return argv
    
def render_html(f_in, f_out):
    sys.argv = _prepare_argv(f_in, f_out)
    publish_cmdline(writer_name='html', settings_overrides={'output_encoding': 'utf-8', 'input_encoding': 'utf-8', 'stylesheet_path': 'parente.css'})
    del sys.argv[1:]
    
def render_s5(f_in, f_out):
    sys.argv = _prepare_argv(f_in, f_out)
    publish_cmdline(writer_name='s5', settings_overrides={'output_encoding': 'utf-8', 'input_encoding': 'utf-8'})
    del sys.argv[1:]
    
def render_latex(f_in, f_out):
    sys.argv = _prepare_argv(f_in, f_out)
    publish_cmdline(writer_name='latex', settings_overrides={'output_encoding': 'utf-8', 'input_encoding': 'utf-8'})
    del sys.argv[1:]
    
def render_pseudoxml(f_in, f_out):
    pass
    
class Editor(gui.Edit):
    def __init__(self, parent):
        gui.Edit.__init__(self, parent, multiline=True)
        self.font = gui.Font(name="Andale Mono", size=5)
        self.bind(chardown=self.on_char_down)
        
    def on_char_down(self, ev):
        key = ev.key
        if key == '\t':
            self.selected_text = ' '*4
            return
        elif key == '\r':
            start, stop = self.selection
            line = self.line_from_char(start)
            line_start = self.line_index(line)
            line_end = line_start + self.line_length(line_start)
            line_content = self.text[line_start : line_end+1]
            indent = 0
            for char in line_content:
                #print char
                if char == ' ':
                    indent += 1
                elif char == '\t':
                    indent += 8
                else:
                    break
            indent = " "*indent
            
            self.selected_text = "\r\n%s" % indent
        else:
            ev.skip()
        
class AboutDialog(gui.Dialog):
    ABOUT = '''
    <html>
        <body>
        <div style="text-align: center;">
            <h1>reSTEditor</h1>
            <h2>A pocket reStructuredText editor</h2>
            <h3>by Alexandre Delattre</h3>
            <h4>(c) 2007 GNU GPL v2</h4>
        </div>
        <body>
    </html>
    '''
    def __init__(self):
        gui.Dialog.__init__(self, "About", has_sip=False)
        self.html = gui.Html(self)
        self.html.zoom_level = 0
        self.html.value = self.ABOUT
        sizer = gui.VBox()
        sizer.add(self.html)
        self.sizer = sizer
        
class PreviewDialog(gui.Dialog):
    def __init__(self):
        gui.Dialog.__init__(self, "Preview", has_sip=False)
        self.html = gui.Html(self)
        self.html.zoom_level = 0
        sizer = gui.VBox()
        sizer.add(self.html, 1)
        self.sizer = sizer
        
    def set_value(self, value):
        self.html.value = value
            
class ExportDialog(gui.Dialog):
    EXPORT_TYPES = [("(X)Html", "html", "*.html"),
                    ("S5 presentation", "s5", "*.html"),
                    ("LaTeX", "latex", "*.tex"),
                    ("Pseudo-xml", "pseudoxml", "*.xml")]
                    
    def __init__(self, filename):
        gui.Dialog.__init__(self, "Export dialog", action=("Export", self.on_export), has_ok=False)
        self.lb_title = gui.Label(self, "Export your document", font=gui.Font(color=(0,0,255)))
        self.lb1 = gui.Label(self, "Output to:")
        self.ed1 = gui.Edit(self)
        self.ed1.bind(update=self.on_update)
        self.bt1 = gui.Button(self, "Browse", action=self.on_browse)
        self.lb2 = gui.Label(self, "Export as:")
        self.cb1 = gui.Combo(self, 
                             choices=[label for label, writer, wildcard in self.EXPORT_TYPES],
                             style="list",)
        
        self.cb1.selection = 0    
        self.cb_action.disable()
        
        sizer = gui.VBox(spacing=4)
        sizer.add(gui.DialogHeader(self, "Export dialog"))
        #sizer.add(self.lb_title)
        tbox = gui.TBox(2, 3, 
                        border=(2,2,2,2),
                        spacing_x=2, 
                        spacing_y=2)
        tbox.add(self.lb1)
        tbox.add(self.ed1)
        tbox.add(self.bt1)
        tbox.add(self.lb2)
        tbox.add(self.cb1)
        sizer.add(tbox, 1)
        self.sizer = sizer
        self.sippref = gui.SIPPref(self)
        self.filename = filename
        
    def on_update(self, ev):
        self.cb_action.enable(self.ed1.text)

    def on_browse(self, ev=None):
        sel = self.cb1.selection
        name, ext, wcard = self.EXPORT_TYPES[sel]
        
        fname = os.path.basename(self.filename)
        fname, ext = os.path.splitext(fname)
        fname += wcard[1:] 
        
        wildcards = {"All (*.*)":"(*.*)", 
                     "%s (%s)" %(name, wcard):wcard}
        filename = gui.FileDialog.save(
                            parent=self,
                            filename=fname,
                            wildcards=wildcards,
                            title="Export",
                            )
        if filename is not None:
            self.ed1.text = filename
        
    def on_export(self, ev=None):
        if not self.ed1.text:
            gui.Message.ok(
                "Warning",
                "Please choose a filename for output",
                'warning',
                self
            )
            return
        sel = self.cb1.selection
        typ = self.EXPORT_TYPES[sel][1]
        renderer = globals()['render_%s' %typ]
        c = gui.BusyCursor()
        output = self.ed1.text
        try:
            renderer(self.filename, output)
        except Exception, e:
            gui.Message.ok("Export failed",
                           "Error: %s" %e,
                           "error",
                           self)
        else:
            if gui.Message.yesno("Export sucessful",
                                 "Open the file exported ?",
                                 "question",
                                 self) == 'yes':
                os.startfile(output)
        
class MainFrame(gui.CeFrame):
    def __init__(self):
        gui.CeFrame.__init__(self, 
                             title="reSTEditor",
                             action=("Preview", self.on_preview),
                             menu="Menu",
                             tab_traversal=False,
                             has_toolbar=True)
        self.toolbar.add_standard_bitmaps()
#        for i in range(20):
#            self.toolbar.add_button(i)
        self.toolbar.add_button(6, action=self.on_new)
        self.toolbar.add_button(7, action=self.on_open)
        self.toolbar.add_button(8, action=self.on_save)
        self.toolbar.add_button(style='separator')
        self.toolbar.add_button(0, action=self.on_cut)
        self.toolbar.add_button(1, action=self.on_copy)
        self.toolbar.add_button(2, action=self.on_paste)
        self.toolbar.add_button(3, action=self.on_undo)
        
        self._make_menu()
        self.editor = Editor(self)
        self.sippref = gui.SIPPref(self)
        self.bind(close=self.on_close)
        self.editor.bind(update=self.on_editor_update,
                         lbdown=self.on_bdown)
        sizer = gui.VSizer()
        sizer.add(self.editor)
        self.sizer = sizer
        
        self.filename = None
        
        self.cb_action.disable()
        
    def _markup_wrapper(self, ch):
        return lambda ev : self.markup(ch)
        
    def _underline_wrapper(self, ch):
        return lambda ev : self.underline(ch)
    
    def _make_menu(self):
        help_menu = gui.PopupMenu()
        help_menu.append('About', 
                         callback=self.on_about)
        help_menu.append('Contents', 
                         callback=self.on_help_contents)
        
        rest_menu = gui.PopupMenu()
        rest_markup_menu = gui.PopupMenu()
        
        for label, ch in [('bold', '**'), 
                          ('italic', '*')]:
            rest_markup_menu.append(
                label,
                callback=self._markup_wrapper(ch))
        rest_menu.append_menu('Markup', rest_markup_menu)
        
        rest_under_menu = gui.PopupMenu()
        for ch in "= - ` : . ' \" ~ ^ _ * + #".split():
            rest_under_menu.append(
                ch,
                callback=self._underline_wrapper(ch))
        
        rest_menu.append_menu('Underline', rest_under_menu)
        
        file_menu = gui.PopupMenu()
        file_menu.append("New", callback=self.on_new)
        file_menu.append("Open", callback=self.on_open)
        file_menu.append_separator()
        file_menu.append("Save", callback=self.on_save)
        file_menu.append("Save as", callback=self.on_save_as)
        file_menu.append_separator()
        export_item = file_menu.append("Export", callback=self.on_export, enabled=False)
        
        self.export_item = export_item
        
        edit_menu = gui.PopupMenu()
        edit_menu.append("Undo", callback=self.on_undo, enabled=False)
        edit_menu.append_separator()
        edit_menu.append("Cut", callback=self.on_cut)
        edit_menu.append("Copy", callback=self.on_cut)
        edit_menu.append("Paste", callback=self.on_paste)
        edit_menu.append_separator()
        edit_menu.append("Select all", callback=self.on_select_all)
        
        self.cb_menu.append_menu("Help", help_menu)
        self.cb_menu.append_menu("reST", rest_menu)
        self.cb_menu.append_menu("Edit", edit_menu)
        self.cb_menu.append_menu("File", file_menu)
        
        self.edit_menu = edit_menu
    
    
    def set_filename(self, filename):
        if filename is None:
            self.export_item.disable()
        else:
            self.export_item.enable()
            
        self._filename = filename
        
    def get_filename(self):
        return self._filename
        
    def on_close(self, ev=None):
        if self.prevent_lost():
            ev.skip()
            
    def prevent_lost(self):
        if self.editor.modified:
            if self.filename is not None:
                message = "Save modifications to file %s ?" %self.filename
            else:
                message = "Save modifications to new file ?"
                
            res = gui.Message.yesnocancel(
                "Save changes", 
                message, 
                "question", 
                self
            ) 
            if res == 'yes':
                self.on_save()
                return True
            elif res == 'no':
                return True
            else:
                return False
        return True
            
    def on_new(self, ev):
        if self.prevent_lost():
            self.filename = None
            self.editor.text = ''
            self.editor.modified = False
            self.cb_action.disable()
            
        
    def on_open(self, ev):
        if self.prevent_lost():
            filename = gui.FileDialog.open(
            parent=self, 
            wildcards={"Text files (*.txt)":"*.txt", 
                      "All (*.*)":"*.*"}
            )
            if not filename:
                return
            if not os.path.exists(filename):
                gui.Message.ok("Error", 
                               "The file %s does not exists" %filename, 
                               "error", 
                               self)
                return               
            f = open(filename, "r")
            self.filename = filename
            self.editor.text = f.read().decode('utf-8')
            self.editor.modified = False
            self.cb_action.enable(bool(self.editor.text))
    
    def on_save(self, ev=None):
        if not self.filename:
            self.on_save_as()
        else:
            self.save()
            
    def on_save_as(self, ev=None):
        filename = gui.FileDialog.save(
            parent=self, 
            wildcards={"Text files (*.txt)":"*.txt", 
                        "All (*.*)":"*.*"}
            )
        if not filename:
            return
            
        if os.path.exists(filename):
            if gui.Message.yesno(
                "Confirmation", 
                'Overwrite file %s' %filename, 
                "question", 
                self) == 'no':
                
                return
        self.filename = filename
        self.save()
        
    def save(self):
        f = open(self.filename, "w")
        try:
            f.write(self.editor.text)
        except UnicodeEncodeError:
            f.write(self.editor.text.encode('utf-8'))
        self.editor.modified = False
        
    def on_export(self, ev=None):
        assert self.filename is not None
        if self.prevent_lost():
            dlg = ExportDialog(self.filename)
            dlg.popup(self)
            dlg.destroy()
        
    def on_cut(self, ev):
        self.editor.cut()
        
    def on_copy(self, ev):
        self.editor.copy()
        
    def on_paste(self, ev):
        self.editor.paste()
        
    def on_undo(self, ev):
        self.editor.undo()
        
    def on_select_all(self, ev):
        self.editor.select_all()
        
    def on_editor_update(self, ev=None):
        if self.editor.can_undo():
            self.edit_menu[0].enable()
        self.cb_action.enable(bool(self.editor.text))
            
    def on_bdown(self, event):
        if gui.recon_context(self.editor, event):
            edit_menu = gui.PopupMenu()
            edit_menu.append("Undo", callback=self.on_undo, enabled=self.editor.can_undo())
            edit_menu.append_separator()
            edit_menu.append("Cut", callback=self.on_cut)
            edit_menu.append("Copy", callback=self.on_cut)
            edit_menu.append("Paste", callback=self.on_paste)
            edit_menu.append_separator()
            edit_menu.append("Select all", callback=self.on_select_all)
            
            gui.context_menu(self.editor, event, edit_menu)
        else:
            event.skip()
        
    def on_about(self, ev):
        dlg = AboutDialog()
        dlg.popup()
        dlg.destroy()
        
    def on_help_contents(self, ev):
        doc_path = os.path.abspath(
                    os.path.join("restdoc", 
                    "introduction.html")
                    )
        os.startfile(doc_path)
        
    def on_preview(self, ev):
        cur = gui.BusyCursor()
        dlg = PreviewDialog()
        dlg.value = render_preview(self.editor.text)
        del cur
        dlg.popup(self)
        dlg.destroy()
    
    def markup(self, ch):
        text = self.editor.selected_text
        text = "%s%s%s" %(ch, text, ch)
        self.editor.selected_text = text
         
    def underline(self, ch):
        text = self.editor.selected_text
        if text:
            line = ch * len(text)
            text = "%s\r\n%s" %(text, line)
            self.editor.selected_text = text
    
if __name__ == '__main__':
    app = gui.Application(MainFrame())
    app.run()
