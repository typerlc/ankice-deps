import datetime

class Task(object):
    def __init__(self, name):
        self.name = name
        self.description = ''
        self.subtasks = []
        self.enddate = None
        self.parent = None
        self.done = False
        
    def add(self, subtask):
        self.subtasks.append(subtask)
        subtask.parent = self
        
    def insert(self, index, subtask):
        self.subtasks.insert(index, subtask)
        subtask.parent = self
        
    def attach(self, subtask, index=None):
        if index is None:
            self.add(subtask)
        else:
            self.insert(subtask, i)
            
        parent_done = True
        for task in self.subtasks:
            if not task.done:
                parent_done = False
        
        self._set_parent_done(parent_done)
            
    #def swap()
    def detach(self):
        if self.parent is not None:
            self.parent.subtasks.remove(self)
            
            parent_done = True
            for task in self.parent.subtasks:
                if not task.done:
                    parent_done = False
            
            self.parent._set_parent_done(parent_done)
        
    def remove(self):
        if self.parent is not None:
            self.parent.subtasks.remove(self)
            
            parent_done = True
            for task in self.parent.subtasks:
                if not task.done:
                    parent_done = False
            
            self.parent._set_parent_done(parent_done)
         
        for subtask in self.subtasks:
            subtask.remove()
        
    def is_late(self):
        if self.enddate is None:
            return False
        return datetime.date.today() > self.enddate
        
    def set_done(self, done):
        if done:
            self.done = True
        else:
            self.done = False
        
        if self.parent is not None:
            parent_done = True
            for task in self.parent.subtasks:
                if not task.done:
                    parent_done = False
            
            self.parent._set_parent_done(parent_done)
            
        for subtask in self.subtasks:
            subtask._set_sub_done(done)
        
    def _set_parent_done(self, done):
        if done:
            self.done = True
        else:
            self.done = False
        
        if self.parent is not None:
            parent_done = True
            for task in self.parent.subtasks:
                if not task.done:
                    parent_done = False
            
            self.parent._set_parent_done(parent_done)
            
            
    def _set_sub_done(self, done):
        self.done = done
        for subtask in self.subtasks:
            subtask._set_sub_done(done)
            
            