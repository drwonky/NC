from kivy.app import App
#from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition,\
    SlideTransition
from kivy.utils import get_color_from_hex
from serial.tools.list_ports import comports
from kivy.uix.button import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
#from kivy.uix.codeinput import CodeInput
#from kivy.config import Config
#from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from threading import Thread
from profilehooks import profile

#from kivy.uix.scrollview import ScrollView

from fadalLexer import GcodeLexer

from wifi import Cell, Scheme  # @UnresolvedImport

import rpi_backlight as bl
import time
import platform

class MainMenu(Screen):
#    def __init__(self, **kwargs):
#        super(Widget, self).__init__(**kwargs)
    pass

class LoadScreen(Screen):
#    def __init__(self, **kwargs):
#        super(LoadScreen, self).__init__(**kwargs)
    @profile
    def load_code(self,dt):
            self.code.text = self.f.read()
            self.code.multiline = True
            self.code.focus = True
            self.code.cursor = (0,0)
            self.f.close()

    def load_file(self):
        try:
            l = Message()
            l.show('Loading...')
            self.f = open(self.ids.filelist.selection[0],"r")
            self.code = self.manager.get_screen('edit').ids.code
            self.code.filename = self.ids.filelist.selection[0]

            Clock.schedule_once(self.load_code)

            self.manager.transition.direction = 'left'
            self.manager.current='edit'
            l.dismiss()
        except IOError as e:
            Alert().show('Error','Unable to open file: {0}'.format(e.strerror))
            self.code.filename = ''

        

class SetupScreen(Screen):
    pass

class IconButton(ButtonBehavior, BoxLayout):
    pass

class PortScreen(Screen):
    def __init__(self, **kwargs):
        super(PortScreen, self).__init__(**kwargs)
        self.config = App.get_running_app().config
        port_list = sorted(comports())
        port_selected = self.config.get('connection','port')
        
        for n, (port, desc, hwid) in enumerate(port_list,1):  # @UnusedVariable
            name=port.split('/')[-1]
            
            if 'AMA' in desc:
                button = IconButton(desc='Builtin',icon='rpi128.png',meta=port,text_color=(1,1,1,1),width=128,height=148,icon_size=(128,128),selected=1 if port == port_selected else 0)
                pass
            elif 'USB' in desc:
                button = IconButton(desc=name,icon='usb_serial_icon128.png',meta=port,text_color=(1,1,1,1),width=128,height=148,icon_size=(128,128),selected=1 if port == port_selected else 0)
                pass
            else:
                button = IconButton(desc=name,icon='serial_icon128.png',meta=port,text_color=(1,1,1,1),width=128,height=148,icon_size=(128,128),selected=1 if port == port_selected else 0)
            
            button.bind(on_press=self.set_port)
            self.ids.layout.add_widget(button)
            
    def set_port(self,obj):
        self.config.set('connection','port',obj.meta)
        buttons = obj.parent.children
        for b in buttons:
            b.selected=0
        obj.selected=1

class WifiScreen(Screen):
    aplist = None
    ap = None
    wifi_iface = None
    
    def __init__(self, **kwargs):
        super(WifiScreen, self).__init__(**kwargs)
        self.config = App.get_running_app().config
        self.wifi_iface = self.config.get('networking','wifi_iface')
        try:
            current_essid = Cell.current_essid(self.wifi_iface)
            current_ip = Cell.current_ip(self.wifi_iface)
            if current_essid is not None:
                self.ids.essid.text = str.format("Connected to\n[b]{0}[/b]\n\n[b]IP:[/b]{1}",current_essid,current_ip)
            else:
                self.ids.essid.text = ''
        except:
            pass
        
    def scan(self):
        self.aplist = Cell.all(self.wifi_iface)
        
        print ('scan')
        self.ids.layout.clear_widgets()
        wifiap = self.config.get('networking','wifiap')
        for ap in self.aplist:
            print ('ssid',ap.ssid, ' encrypted', ap.encrypted)
            if ap.encrypted:
                icon = 'wifi-lock.png'
            else:
                icon = 'wifi.png'
            
            button = IconButton(icon=icon,meta=ap,desc=ap.ssid,width=128,height=148,icon_size=(128,128),text_color=(1,1,1,1),selected=1 if ap.ssid == wifiap else 0)
            button.bind(on_press=self.pick_ap)
            self.ids.layout.add_widget(button)

    def activate_thread(self, scheme):
        self.activation_status = None
        print ('activating')
        try:
            self.activation_status = scheme.activate()
            print ('activation complete')
        except:
            print ('exception during activation')
            pass
        
    def validate_pw(self, obj):
        self.popup.dismiss()
        scheme = Scheme.find(self.wifi_iface,self.ap.ssid)
        
        if scheme != None:
            scheme.delete()
            print ('scheme found, deleting')

        scheme = Scheme.for_cell(self.wifi_iface,self.ap.ssid,self.ap,obj.text)
        scheme.save()

        progressbar = ProgressBar(max=10)
        progress = Popup(title='Connecting...',size_hint=(None,None),size=(400,100),content=progressbar)
        progress.open()

        activatethread = Thread(target=self.activate_thread,args=(scheme,))
        activatethread.start()
        print ('thread started')
        
        while self.activation_status is None:
            time.sleep(1)
            progressbar.value = (progressbar.value + 1) % 10
            print ('tick')

        progress.dismiss()
        
        if self.activation_status:
            self.save_ap()
            print ('activated')
        else:
            scheme.delete()
            self.ask_pass()
            print ('failed, asking again')
        pass
    
    def pick_ap(self, obj):
        self.ap = obj.meta

        if self.ap.encrypted:
            self.ask_pass()
        else:
            self.set_ap()
        pass
    
    def ask_pass(self):
        self.popup = PasswordPopup()
        self.popup.ids.password.bind(on_text_validate=self.validate_pw)
        self.popup.ids.ok.bind(on_press=self.validate_pw)
        self.popup.open()

        pass
    
    def save_ap(self):
        self.config.set('networking','wifiap',self.ap.ssid)

    pass
        
class PasswordPopup(Popup):
    pass

class EditScreen(Screen):
    def __init__(self, **kwargs):
        super(EditScreen, self).__init__(**kwargs)
        self.ids.code.lexer=GcodeLexer()
        self.row = 1
        self.col = 1
        self.lines = 1
        #self.ids.code.bind(cursor=self.set_cursor)
        #self.ids.code.bind(_lines=self.set_lines)
#        self.ids.code.style_name='colorful'

    def set_lines(self,instance,value):
        self.lines = len(value)
        self.bytes = sum(map(len, value))

    def set_cursor(self,instance,value):
        self.col, self.row = value
        self.update_info()

    def update_info(self):
        #self.ids.info.text = '{:>40}, {:<6} {:>7} lines'.format(self.row+1,self.col+1,self.lines)
        #self.ids.info.text = '{:>6}, {:<3} {:>7} lines'.format(self.row+1,self.col+1,self.lines)
        self.ids.info.text = '{:>6}, {:<3} {:>7} lines {:>12} characters'.format(self.row+1,self.col+1,self.lines,self.bytes+(self.lines*2)-2)

    pass

class Alert(Popup):
    def show(self, title,msg):
        self.title = title
        self.msg = msg
        self.open()

class Message(ModalView):
    def show(self, msg):
        self.msg = msg
        self.open()

class LoadingSpinner(ModalView):
    pass

class SplashScreen(Screen):
    
    def on_enter(self):
        Clock.schedule_once(self.showmenu)

    def showmenu(self,dt):
        self.manager.current='menu'
        self.manager.transition=SlideTransition()

    pass

class NCApp(App):
    baudrates = ('1200','2400','4800','9600','19200','38400','57600','115200')
    databits = ('7','8')
    parity = ('even','odd');
    stopbits = ('1','2')
    title = 'NC Helper'

    def build_config(self, config):
        config.setdefaults('connection', {
            'databits': '7',
            'baud': '9600',
            'parity': 'even',
            'stopbits': '2',
            'port': '',
        })
        config.setdefaults('screen', {
            'brightness':128
        })
        config.setdefaults('files', {
            'usbmedia':'/media'
        })
        config.setdefaults('networking', {
            'wifiap':'',
            'wifi_iface':'wlan0'
        })
        
    def wifi_reconnect(self):
        wifiap = self.config.get('networking','wifiap')
        wifi_iface = self.config.get('networking','wifi_iface')
        
        try:
            scheme = Scheme.find(wifi_iface,wifiap)
            if scheme != None:
                activatethread = Thread(target=self.activate_thread,args=(scheme.activate,))
                activatethread.start()
        except:
            pass
        
    def activate_thread(self, scheme):
            try:
                scheme.activate()
            except:
                pass
            
    def startup(self):
        try:
            bl.set_brightness(self.config.getint('screen','brightness'), False)
        except:
            pass
        self.wifi_reconnect()

    def build(self):
        self.startup()
        Window.clearcolor = get_color_from_hex('38393b')
        if platform.node() != 'raspberrypi':
            Window.size = (800, 480)
        self.sm = ScreenManager()
        self.sm.transition=FadeTransition()
        self.sm.add_widget(SplashScreen(name='splash'))
        self.sm.add_widget(MainMenu(name='menu'))
        self.sm.add_widget(LoadScreen(name='load'))
        self.sm.add_widget(SetupScreen(name='setup'))
        self.sm.add_widget(PortScreen(name='ports'))
        self.sm.add_widget(WifiScreen(name='wifi'))
        self.sm.add_widget(EditScreen(name='edit'))
        return self.sm
    
    def on_stop(self):
        self.config.write()
        App.on_stop(self)

if __name__ == '__main__':
    NCApp().run()
