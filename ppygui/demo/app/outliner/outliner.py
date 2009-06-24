import os
#import pickle
import cPickle as pickle
from urllib import quote, unquote

import ppygui as gui
from task import Task
from imagelist import ImageList
from markup import render_html

class DescriptionEdit(gui.Edit):
    def __init__(self, parent):
        gui.Edit.__init__(self, parent, multiline=True)
        self.bind(lbdown=self.on_bdown)
        
    def on_bdown(self, ev):
        if gui.recon_context(self, ev):
            edit_menu = gui.PopupMenu()
            edit_menu.append("Annuler", callback=self.on_undo, enabled=self.can_undo())
            edit_menu.append_separator()
            edit_menu.append("Couper", callback=self.on_cut)
            edit_menu.append("Copier", callback=self.on_cut)
            edit_menu.append("Coller", callback=self.on_paste)
            edit_menu.append_separator()
            edit_menu.append("Tout selectionner", 
                             callback=self.on_select_all)
            edit_menu.append_separator()
            edit_menu.append("Inserer lien vers fichier", 
                             callback=self.insert_file_link)
            edit_menu.append("Inserer lien web")
            gui.context_menu(self, ev, edit_menu)
            #menu.append()
        else:
            ev.skip()
            
    def on_cut(self, ev):
        self.cut()
        
    def on_copy(self, ev):
        self.copy()
        
    def on_paste(self, ev):
        self.paste()
        
    def on_undo(self, ev):
        self.undo()
        
    def on_select_all(self, ev):
        self.select_all()
    
    def insert(self, txt):
        start, stop = self.selection
        self.selection = start, start
        self.selected_text = txt
        
    def insert_file_link(self, ev):
        f = gui.FileDialog.open(wildcards=\
                                {"Tous (*.*)" : "*.*"},
                                parent=self.parent)
        if f:
            self.insert("file://%s" %quote(f))

    def insert_mail_link(self, ev):
        dlg = LienMailDialog()
        if dlg.popup(self.parent) == 'ok':
            self.insert(dlg.mail)
        dlg.destroy()
        
class LienMailDialog(gui.Dialog):
    def __init__(self):
        gui.Dialog.__init__(
            self, 
            "Insert mail link", 
            action=("Cancel", self.on_cancel))
          
        self.email_edit = gui.Edit(self)
        sizer = gui.VSizer((2,2,2,2))
        sizer.addfixed(self.email_edit, 20)
        self.sizer = sizer
        
    def on_cancel(self, ev):
        self.end('cancel')
        
    def get_mail(self):
        return "mailto:%s" %self.email_edit.text
        
class TaskDialog(gui.Dialog):
    def __init__(self, title):
        gui.Dialog.__init__(
            self, 
            title, 
            action=("Cancel", self.on_cancel))
        
        #self.butt_ok = gui.Button(self, "&Ok", action=self.onok)
        
        self.label_1 = gui.Label(self, "Nom:")
        self.label_2 = gui.Label(self, "Description:")
        self.name_entry = gui.Edit(self)
        
        self.check_date = gui.Button(self, u"Ech\xe9ance", style="check")
        self.check_date.checked = False
        self.check_date.bind(clicked=self.on_enddatechecked)
        
        self.end_date = gui.Date(self)
        self.end_date.disable()
         
        self.desc_entry = DescriptionEdit(self)
        self.button_linkfile = gui.Button(self, "Lien fichier", action=self.desc_entry.insert_file_link)
        self.button_linkmail = gui.Button(self, "Lien mail", action=self.desc_entry.insert_mail_link)
        self.sippref = gui.SIPPref(self)
        
        sizer = gui.VSizer((2,2,2,2))
        sizer.addfixed(self.label_1, 15)
        sizer.addfixedspace(2)
        sizer.addfixed(self.name_entry, 20)
        sizer.addfixedspace(2)
        
        sizer2 = gui.HSizer()
        sizer2.addfixed(self.check_date, 90)
        sizer2.addfixedspace(2)
        sizer2.addfixed(self.end_date, 65)
        
        sizer.addfixed(sizer2, 20)
       
        sizer3 = gui.HSizer()
        sizer3.addfixed(self.button_linkfile, 80)
        sizer3.addfixedspace(2)
        sizer3.addfixed(self.button_linkmail, 80)
        
        
        sizer.addfixed(gui.HLine(self), 10)
        sizer.addfixed(self.label_2, 15)
        sizer.addfixedspace(2)
        sizer.add(self.desc_entry)
        sizer.addfixedspace(2)
        sizer.addfixed(sizer3, 20)
        self.sizer = sizer
        
    def on_enddatechecked(self, ev):
        self.end_date.enable(self.check_date.checked)
        
    def onok(self):
        if not self.name_entry.text:
            gui.Message.ok('Warning',
                           'Please give a name to the task',
                           'warning',
                           self)
        else:
            self.end('ok')
            
    def on_cancel(self, ev):
        if self.name_entry.modified or \
           self.desc_entry.modified :
               
            if gui.Message.yesno("Confirmation",
                           'Annuler les modifications ?',
                           'question',
                           self) == 'yes':
                self.end('cancel')
        else:
            self.end('cancel')
        
class OutlineTree(gui.Tree):
    def __init__(self, parent, main_task):
        gui.Tree.__init__(self, parent, border=False)
        self.main_task = main_task
        self.root = self.add_root(main_task.name, data=self.main_task, image=3, selected_image=3)
        self.populate_task()
        self.bind(lbdown=self.on_context,
                  selchanged=self.on_selchanged)
        
        self.il = ImageList(32, 32)
        self.il.add_from_resource(os.path.abspath("outlinerres.dll"), [101, 102, 103], 32, 32)
        self.image_list = self.il
        
        self._cut_buffer = None
        
    def populate_task(self):
        tasks = [(self.main_task, self.root)]
        while tasks:
            new_tasks = []
            for task, item in tasks:
                for subtask in task.subtasks:
                    image = 0
                    if subtask.done:
                        image = 1
                    elif subtask.is_late():
                        image = 2
                    new_item = item.append(subtask.name, data=subtask, image=image, selected_image=image)
                    new_tasks.append((subtask, new_item))
                #item.expand()
            tasks = new_tasks 
        self.root.select()
        self.root.expand()
        
    def on_context(self, event):
        if gui.recon_context(self, event):
            item = self.selection
            if item is not None:
                menu = gui.PopupMenu()
                menu.append("Ajouter une sous-tache", callback=self.on_add)
                menu.append("Editer",
                            callback=self.on_edit)
                menu.append("Supprimer", 
                            enabled=(item.data!=self.main_task),
                            callback=self.on_remove)
                menu.append_separator()
                menu.append('Couper', callback=self.on_cut)
                menu.append('Coller', enabled=(self._cut_buffer is not None), callback=self.on_paste)
                gui.context_menu(self, event, menu)
        else:
            event.skip()
            
    def on_cut(self, ev):
        item = self.selection
        assert item is not None
        task = item.data
        task.detach()
        self._cut_buffer = task
        parent_item = item.parent
        item.remove()
        self._update_parent_item(parent_item)
        
    def on_paste(self, ev):
        item = self.selection
        assert item is not None
        task = item.data
        task.attach(self._cut_buffer)
        
        image = 0
        if self._cut_buffer.done:
            image = 1
        elif self._cut_buffer.is_late():
            image = 2
        new_item = item.append(self._cut_buffer.name, data=self._cut_buffer, image=image, selected_image=image)
        new_item.select()            
        #child = item.append()
        tasks = [(self._cut_buffer, new_item)]
        while tasks:
            new_tasks = []
            for task, item in tasks:
                for subtask in task.subtasks:
                    image = 0
                    if subtask.done:
                        image = 1
                    elif subtask.is_late():
                        image = 2
                    new_item = item.append(subtask.name, data=subtask, image=image, selected_image=image)
                    new_tasks.append((subtask, new_item))
                item.expand()
            tasks = new_tasks 
            
        self._update_parent_item(item)
        self._cut_buffer = None
    def on_add(self, ev=None):
        item = self.selection
        assert item is not None
        dlg = TaskDialog("Ajouter une sous-tache")
        if dlg.popup(self) == 'ok':
            task = Task(dlg.name_entry.text)
            task.description = dlg.desc_entry.text
            if dlg.check_date.checked:
                task.enddate = dlg.end_date.date
            item.data.add(task)
            image = 0
            task.set_done(False)
#            if task.done:
#                image = 1
            if task.is_late():
                image = 2
            child = item.append(task.name, data=task, image=image, selected_image=image)
            self.update_item(child)
            child.select()
        dlg.destroy()
        
    def on_selchanged(self, ev):
        task = ev.new_item.data
        if task is self.main_task:
            self.parent.cb_action.disable()
        else:
            self.parent.cb_action.enable()
        self.parent.display_task(task)
        
    def on_remove(self, ev):
        item = self.selection
        assert item is not None
        if gui.Message.yesno("Confirmation",
                             "Voulez vous supprimer cette tache?",
                             "question",
                             self.parent) == 'yes':
            item.data.remove()
            parent_item = item.parent
            item.remove()
            self._update_parent_item(parent_item)
            
            
    def on_edit(self, ev):
        item = self.selection
        assert item is not None
        task = item.data
        dlg = TaskDialog("Editer une tache")
        dlg.name_entry.text = task.name
        dlg.desc_entry.text = task.description
        if task.enddate is not None:
            dlg.end_date.enable()
            dlg.end_date.date = task.enddate
            dlg.check_date.checked = True
        
        if dlg.popup(self.parent) == 'ok':
            task.name = dlg.name_entry.text
            task.description = dlg.desc_entry.text
            if dlg.check_date.checked:
                task.enddate = dlg.end_date.date
            else:
                task.enddate = None
            self.update_item(item)
            self.parent.display_task(task)
        
        dlg.destroy()
        
    def _update_item(self, item):
        task = item.data
        item.text = task.name
        if task.done:
            item.image = 1
            item.selected_image = 1
        elif task.is_late():
            item.image = 2
            item.selected_image = 2
        else:
            item.image = 0
            item.selected_image = 0
    
    def update_item(self, item):
        self._update_item(item)
        self._update_parent_item(item.parent)
        for subitem in item:
            self._update_subitem(subitem)
        
    def _update_parent_item(self, item):
        task = item.data
        if task is self.main_task:
            return
        self._update_item(item)
        self._update_parent_item(item.parent)
    
    def _update_subitem(self, item):
        self._update_item(item)
        for subitem in item:
            self._update_subitem(subitem)
            
class TaskHtml(gui.Html):
    def __init__(self, parent):
        gui.Html.__init__(self, parent, border=True)
        self.zoom_level = 0
        self.bind(navigate=self.on_navigate)
        self.html = '<div style="color: #0000ff;">Description</div>'
        
    def display_task(self, task):
        html = \
        '<div style="color: #0000ff;">%s</div>' %task.name
        if task.done:
            html += u'<p><span style="color: #00ff00;">Tache achev\xe9e</span>'
        elif task.enddate is not None:
            if not task.is_late():
                html += u'<p><span style="color: #ff0000;">Ech\xe9ance: </span>%s</p>' %task.enddate.strftime("%d/%m/%Y")
            else:
                html += u'<p><span style="color: #ff0000;">Ech\xe9ance: %s !</span></p>' %task.enddate.strftime("%d/%m/%Y")
        else:
            html += "<p>Tache en cours</p>"
        if task.description:
            html += '<p>%s</p>' %render_html(task.description).replace('\r\n', '<br/>')
#        else:
#            html += '<p>Pas de description</p>'
        self.html = html    
        
    def on_navigate(self, event):
        link = event.url[3:]
        os.startfile(unquote(link))
        
class MainFrame(gui.CeFrame):
    def __init__(self):
        gui.CeFrame.__init__(self,
                             title='Outliner',
                             action=('Done', self.on_done),
                             has_sip=False)
        #self.bring_to_front()
        self.cb_action.disable()
        self.bind(close=self.on_close)
        try:
            f = open("tasks.db", 'rb')
            main_task = pickle.load(f)
            f.close()
        except IOError:
            main_task = Task("My Tasks")
        self.outline_tree = OutlineTree(self, main_task)
        self.description = TaskHtml(self)
        sizer = gui.VSizer()
        sizer.add(self.outline_tree, 7)
        sizer.add(self.description, 3, (-1,0,-1,-1))
        self.sizer = sizer
        
    def display_task(self, task):
        if task.done:
            self.cb_action.text = u"Activer"
        else:
            self.cb_action.text = u"Terminer"
        self.description.display_task(task)
        
    def on_close(self, event):
        f = open("tasks.db", "wb")
        pickle.dump(self.outline_tree.main_task, f, 2)
        f.close()
        event.skip()
        
    def on_done(self, ev):
        item = self.outline_tree.selection
        assert item is not None
        task = item.data
        task.set_done(not task.done)
        self.outline_tree.update_item(item)
        self.display_task(task)
        #event.skip()
        
def main():
    app = gui.Application(MainFrame())
    app.run()
    
if __name__ == '__main__': main()