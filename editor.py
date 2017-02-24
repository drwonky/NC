from kivy.uix.label import Label
from kivy.uix.widget import Widget

class EditorWidget(Widget):
    def __init__(self, **kwargs):
        super(EditorWidget, self).__init__(**kwargs)
        
        self.font_size = '16dp'
        self.spacing = 4
        self.data = None
        self.viewport = None
        self.lines = 0
        
    def _set_text(self,text):
        self.data = text.split(u'\n')
        self.update_view()
        
    def update_view(self):
        label = Label(font_size=self.font_size,max_lines=1)
        self.lines = int(self.height / (label.height + self.spacing) - 1)
        for n in range(self.lines):
            self.viewport[n] = Label(font_size=self.font_size,max_lines=1,text_size=(self.width,None),size_hint=(1,1))
            
            