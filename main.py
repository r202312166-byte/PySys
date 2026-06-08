import sys
import os
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import ListProperty

# --- Color Definitions ---
COLOR_BG = (0.918, 0.718, 0.945, 1)
COLOR_BTN_BG = (0.725, 0.725, 0.910, 1)
COLOR_TXT_BG = (0.980, 0.922, 0.961, 1)
COLOR_TXT_FG = (0.000, 0.671, 0.055, 1)

# --- Custom TextInput to force Tab to 4 spaces ---
class CodeInput(TextInput):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        # Intercept the Tab key and insert 4 spaces instead
        if keycode[1] == 'tab':
            self.insert_text('    ')
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)

# Explicitly tell Kivy that 'CodeInput' in KV refers to this Python class
Factory.register('CodeInput', cls=CodeInput)

# --- Stdout Redirector for the Terminal ---
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.text += message
        self.text_widget.cursor = (len(self.text_widget.text), 0)
        self.text_widget.scroll_y = 0  # 0 is bottom in Kivy

    def flush(self):
        pass

# --- KV Layout String ---
KV = '''
<RootWidget>:
    orientation: 'vertical'
    padding: 20
    spacing: 20
    canvas.before:
        Color:
            rgba: root.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    # Main Content Area
    BoxLayout:
        spacing: 20
        
        # Left Panel: Page Management
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: None
            width: 300
            spacing: 15
            
            Button:
                text: 'Save New Page'
                size_hint_y: None
                height: 70
                font_size: '22sp'
                background_color: root.btn_bg_color
                on_release: root.save_page_popup()
                
            ScrollView:
                BoxLayout:
                    id: pages_container
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: 10
                    padding: 5

            # Changed to vertical orientation for Load/Delete buttons
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 140
                spacing: 10
                Button:
                    text: 'Load Selected'
                    size_hint_y: None
                    height: 65
                    font_size: '20sp'
                    background_color: root.btn_bg_color
                    on_release: root.load_page()
                Button:
                    text: 'Delete Selected'
                    size_hint_y: None
                    height: 65
                    font_size: '20sp'
                    background_color: root.btn_bg_color
                    on_release: root.delete_page()

        # Right Panel: Editor & Terminal
        BoxLayout:
            orientation: 'vertical'
            spacing: 15
            
            CodeInput:
                id: editor
                size_hint_y: 0.65
                font_size: '22sp'
                background_color: root.txt_bg_color
                foreground_color: root.txt_fg_color
                cursor_color: root.txt_fg_color
                multiline: True
                tab_width: 4

            TextInput:
                id: terminal
                size_hint_y: 0.35
                font_size: '18sp'
                readonly: True
                background_color: root.txt_bg_color
                foreground_color: root.txt_fg_color
                cursor_color: root.txt_fg_color

    # Bottom Toolbar (Moved from top)
    BoxLayout:
        size_hint_y: None
        height: 80
        spacing: 15
        Button:
            text: 'Open'
            font_size: '24sp'
            background_color: root.btn_bg_color
            on_release: root.open_file()
        Button:
            text: 'Save'
            font_size: '24sp'
            background_color: root.btn_bg_color
            on_release: root.save_file()
        Button:
            text: 'Save As'
            font_size: '24sp'
            background_color: root.btn_bg_color
            on_release: root.save_as_file()
        Button:
            text: 'Run'
            font_size: '24sp'
            background_color: root.btn_bg_color
            on_release: root.run_py()
'''
Builder.load_string(KV)

class RootWidget(BoxLayout):
    # Use ListProperty so KV can safely read these values during initialization
    bg_color = ListProperty(COLOR_BG)
    btn_bg_color = ListProperty(COLOR_BTN_BG)
    txt_bg_color = ListProperty(COLOR_TXT_BG)
    txt_fg_color = ListProperty(COLOR_TXT_FG)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pagecontent = {}
        self.pageitem = []
        self.current_file = " "
        self.selected_page = None

    def update_pages_ui(self):
        container = self.ids.pages_container
        container.clear_widgets()
        for page_name in self.pageitem:
            btn = Button(
                text=page_name,
                size_hint_y=None,
                height=60,
                font_size='20sp',
                background_color=COLOR_BTN_BG if self.selected_page != page_name else (0.6, 0.6, 0.8, 1)
            )
            btn.bind(on_release=lambda instance, name=page_name: self.select_page(name))
            container.add_widget(btn)

    def select_page(self, name):
        self.selected_page = name
        self.update_pages_ui()

    def open_file(self):
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        filechooser = FileChooserListView(path=os.getcwd())
        
        btn_layout = BoxLayout(size_hint_y=None, height=70, spacing=15)
        btn_load = Button(text='Load', font_size='22sp', background_color=COLOR_BTN_BG)
        btn_cancel = Button(text='Cancel', font_size='22sp', background_color=COLOR_BTN_BG)
        
        popup = Popup(title='Open File', content=content, size_hint=(0.8, 0.8))
        
        def load_callback(instance):
            if filechooser.selection:
                filepath = filechooser.selection[0]
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.ids.editor.text = f.read()
                        self.current_file = filepath
                except Exception as e:
                    self.ids.terminal.text += f"Could not load file: {e}\n"
            popup.dismiss()
            
        btn_load.bind(on_release=load_callback)
        btn_cancel.bind(on_release=popup.dismiss)
        
        content.add_widget(filechooser)
        content.add_widget(btn_layout)
        btn_layout.add_widget(btn_load)
        btn_layout.add_widget(btn_cancel)
        popup.open()

    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.ids.editor.text)
            except Exception as e:
                self.ids.terminal.text += f"Could not save file: {e}\n"
        else:
            self.save_as_file()

    def save_as_file(self):
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        filechooser = FileChooserListView(path=os.getcwd())
        
        btn_layout = BoxLayout(size_hint_y=None, height=70, spacing=15)
        btn_save = Button(text='Save', font_size='22sp', background_color=COLOR_BTN_BG)
        btn_cancel = Button(text='Cancel', font_size='22sp', background_color=COLOR_BTN_BG)
        
        popup = Popup(title='Save File', content=content, size_hint=(0.8, 0.8))
        
        def save_callback(instance):
            if filechooser.selection:
                filepath = filechooser.selection[0]
                if os.path.isdir(filepath):
                    filepath = os.path.join(filepath, 'untitled.txt')
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(self.ids.editor.text)
                        self.current_file = filepath
                except Exception as e:
                    self.ids.terminal.text += f"Could not save file: {e}\n"
            popup.dismiss()
            
        btn_save.bind(on_release=save_callback)
        btn_cancel.bind(on_release=popup.dismiss)
        
        content.add_widget(filechooser)
        content.add_widget(btn_layout)
        btn_layout.add_widget(btn_save)
        btn_layout.add_widget(btn_cancel)
        popup.open()

    def run_py(self):
        text = self.ids.editor.text
        self.ids.terminal.text = " "
        old_stdout = sys.stdout
        sys.stdout = StdoutRedirector(self.ids.terminal)
        try:
            exec(text)
        except Exception as e:
            self.ids.terminal.text += str(e) + "\n"
        finally:
            sys.stdout = old_stdout

    def save_page_popup(self):
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        name_input = TextInput(hint_text='Page Name', font_size='22sp', multiline=False)
        
        btn_layout = BoxLayout(size_hint_y=None, height=70, spacing=15)
        btn_ok = Button(text='Save', font_size='22sp', background_color=COLOR_BTN_BG)
        btn_cancel = Button(text='Cancel', font_size='22sp', background_color=COLOR_BTN_BG)
        
        popup = Popup(title='Save Page', content=content, size_hint=(0.6, 0.4))
        
        def ok_callback(instance):
            name = name_input.text.strip()
            if name:
                self.pagecontent[name] = self.ids.editor.text
                if name not in self.pageitem:
                    self.pageitem.append(name)
                self.selected_page = name
                self.update_pages_ui()
            popup.dismiss()
            
        btn_ok.bind(on_release=ok_callback)
        btn_cancel.bind(on_release=popup.dismiss)
        
        content.add_widget(name_input)
        content.add_widget(btn_layout)
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)
        popup.open()

    def load_page(self):
        if self.selected_page and self.selected_page in self.pagecontent:
            self.ids.editor.text = self.pagecontent[self.selected_page]
        else:
            self.ids.terminal.text += "No page selected or page not found.\n"

    def delete_page(self):
        if self.selected_page and self.selected_page in self.pagecontent:
            del self.pagecontent[self.selected_page]
            self.pageitem.remove(self.selected_page)
            self.selected_page = None
            self.update_pages_ui()
        else:
            self.ids.terminal.text += "No page selected to delete.\n"

class PySysApp(App):
    def build(self):
        Window.clearcolor = COLOR_BG
        return RootWidget()

    def on_start(self):
        if len(sys.argv) > 1:
            fpath = sys.argv[1]
            if Path(fpath).exists():
                try:
                    with open(fpath, 'r', encoding='utf-8') as file:
                        self.root.ids.editor.text = file.read()
                        self.root.current_file = fpath
                except Exception as e:
                    self.root.ids.terminal.text += f"Could not load file: {e}\n"

if __name__ == '__main__':
    PySysApp().run()