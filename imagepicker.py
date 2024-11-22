import os
import json
import sys
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_LOG_MODE"] = "PYTHON"
os.environ["KCFG_KIVY_LOG_LEVEL"] = "critical"
ScriptPath = os.path.dirname(os.path.realpath(__file__))
FontPath = os.path.join(ScriptPath, "font.ttf")
ConfigFile = os.path.join(ScriptPath, "config.json")
WindowTitle = "Select Image"

from kivy.config import Config
Config.set('kivy', 'default_font', [FontPath, FontPath, FontPath, FontPath, FontPath])
Config.set('kivy', 'log_enable', 0)
Config.set('kivy', 'desktop', 1)
Config.set('kivy', 'exit_on_escape', 1)
Config.set('graphics', 'fbo', 'software')
Config.set('graphics', 'multisamples', 0)
Config.set('graphics', 'show_taskbar_icon', 0)
Config.set('graphics', 'width', 600)
Config.set('graphics', 'height', 900)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from KivyOnTop import register_topmost, unregister_topmost


ImagePickerStr = """
<MyLayout>
    id: my_widget
    BoxLayout:
        orientation: "vertical"
        size: root.width, root.height

        padding: 8
        spacing: 5
        
        Image:
            id: my_image
            source: ""

        FileChooserListView:
            id: filechooser
            sort_func: lambda a, b: root.sort_folders_first(sort_type.state == 'normal', reverse.state == 'down', a, b)
            on_selection: my_widget.selected(filechooser.selection)
            
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: 30
            
            ToggleButton:
                id: sort_type
                font_size: 16
                text: 'Sort by Date'
                on_state: my_widget.sort_button_state()

            ToggleButton:
                id: reverse
                font_size: 16
                text: 'Newer First'
                disabled: sort_type.state == 'normal'
                on_state: my_widget.reverse_button_state()
            
            Button:
                text: "Open"
                font_size: 16
                on_release: my_widget.select_file()
                
            Button:
                text: "Close"
                font_size: 16
                on_release: app.stop()
"""

Builder.load_string(ImagePickerStr)

StyleOverride = '''
[FileListEntry@FloatLayout+TreeViewNode]:
    locked: False
    entries: []
    path: ctx.path
    # FIXME: is_selected is actually a read_only treeview property. In this
    # case, however, we're doing this because treeview only has single-selection
    # hardcoded in it. The fix to this would be to update treeview to allow
    # multiple selection.
    is_selected: self.path in ctx.controller().selection

    orientation: 'horizontal'
    size_hint_y: None
    height: 16
    # Don't allow expansion of the ../ node
    is_leaf: not ctx.isdir or ctx.name.endswith('..' + ctx.sep) or self.locked
    on_touch_down: self.collide_point(*args[1].pos) and ctx.controller().entry_touched(self, args[1])
    on_touch_up: self.collide_point(*args[1].pos) and ctx.controller().entry_released(self, args[1])
    BoxLayout:
        pos: root.pos
        size_hint_x: None
        width: root.width - dp(10)
        Label:
            id: filename
            font_size: 16                                  # adjust this font size
            size_hint_x: None
            width: root.width - sz.width                       # this allows filename Label to fill width less size Label
            text_size: self.width, None
            halign: 'left'
            shorten: True
            text: ctx.name
        Label:
            id: sz
            font_size: 16                                  # adjust this font size
            #text_size: self.width, None
            size_hint_x: None
            width: self.texture_size[0]                        # this makes the size Label to minimum width
            text: '{}'.format(ctx.get_nice_size())
'''

Builder.load_string(StyleOverride)

class MyLayout(Widget):
    
    def sort_folders_first(self, b, r, files, filesystem):
        if b:
            return (sorted(f for f in files if filesystem.is_dir(f)) +
                    sorted(f for f in files if not filesystem.is_dir(f)))
        else:
            return (sorted(f for f in files if filesystem.is_dir(f)) +
                sorted((f for f in files if not filesystem.is_dir(f)), key=lambda fi: os.stat(fi).st_mtime, reverse = r))
            
    def do_mods(self):
        filechooser_children = self.ids.filechooser.children[0].children[0].children
        for child in filechooser_children:
            if isinstance(child, BoxLayout):
                for _c in child.children:
                    if isinstance(_c, Label):
                        if _c.text == "Name" or _c.text == "Size":
                            _c.font_size = 16
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_mods()
        self.ids.filechooser.filters = ["*.jpg", "*.png", "*.jpeg"]
        self.ids.my_image.color = [0,0,0,0]
        self.font_size = 15
        self._last_selected = None
        self._last_folder = None
        self._sort_by_date = False
        self._newer_first = False
        self.load_config()
        
    def sort_button_state(self):
        sort_by_date = False
        if self.ids.sort_type.state == "down":
            sort_by_date = True
        if sort_by_date != self._sort_by_date:
            self._sort_by_date = sort_by_date
            self.save_config()
        self.ids.filechooser._update_files()
        
    def reverse_button_state(self):
        sort_reverse = False
        if self.ids.reverse.state == "down":
            sort_reverse = True
        if sort_reverse != self._newer_first:
            self._newer_first = sort_reverse 
            self.save_config()
        self.ids.filechooser._update_files()
        
    def save_config(self):
        if self._last_folder is not None:
            config = {
                "last_folder": self._last_folder,
                "last_selected": self._last_selected,
                "sort_by_date": self._sort_by_date,
                "newer_first": self._newer_first
            }
            with open(ConfigFile, "w") as f:
                json.dump(config, f)
                
    def load_config(self):
        if os.path.exists(ConfigFile):
            with open(ConfigFile, "r") as f:
                config = json.load(f)
                self._last_folder = config.get("last_folder", None)
                self._last_selected = config.get("last_selected", None)
                self._sort_by_date = config.get("sort_by_date", False)
                self._newer_first = config.get("newer_first", False)
                if self._last_folder is not None:
                    self.ids.filechooser.path = self._last_folder
                self.ids.sort_type.state = "down" if self._sort_by_date else "normal"
                self.ids.reverse.state = "down" if self._newer_first else "normal"
    
    def selected(self, filename):
        try:
            self.ids.my_image.color = [1,1,1,1]
            self.ids.my_image.source = filename[0]
            self._last_selected = filename[0]
            self._last_folder = os.path.dirname(filename[0])
            self.save_config()
        except:
            pass
        
    def select_file(self):
        App.get_running_app().stop()

class MyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._layout = None
        self._filter = None
    
    def on_start(self):
        from kivy.core.window import Window
        Window.set_title(WindowTitle)
        register_topmost(Window, WindowTitle)
        self.bind(on_stop=lambda *args, w=Window, t=WindowTitle: unregister_topmost(w, t))
        
    def build(self):
        self._layout = MyLayout()
        if self._filter is not None:
            self._layout.ids.filechooser.filters = self._filter
        return self._layout
    
    def run(self, filter = None):
        from kivy.core.window import Window
        if filter is not None:
            if not isinstance(filter, list):
                if ',' in filter:
                    filter = filter.split(',')
                if ';' in filter:
                    filter = filter.split(';')
                else:
                    filter = [filter]
            self._filter = filter
        Window.show()
        super().run()
        Window.hide()
        return self.root._last_selected
    
def get_selected_image(filter = None):
    selected_image = MyApp().run(filter)
    MyApp().stop()
    return selected_image