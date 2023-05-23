import idaapi, idc, idautils
import sark


def hello():
    print("Hello world!")
    print("ImageBase: " + hex(idaapi.get_imagebase()))
    print("Current function:")
    print(sark.Function())


class HelloPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_PROC
    comment = "Sark Hello World"
    help = "My first ever IDAPython plugin"
    wanted_name = "Sark Hello World"
    wanted_hotkey = "Shift+H"

    def init(self):
        return idaapi.PLUGIN_KEEP

    def term(self):
        pass

    def run(self, arg):
        hello()


def PLUGIN_ENTRY():
    return HelloPlugin()
