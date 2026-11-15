import ctypes,sys
x=ctypes.CDLL('libX11.so.6');t=ctypes.CDLL('libXtst.so.6');x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=ctypes.c_void_p;x.XStringToKeysym.argtypes=[ctypes.c_char_p];x.XStringToKeysym.restype=ctypes.c_ulong;x.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];x.XKeysymToKeycode.restype=ctypes.c_uint;x.XFlush.argtypes=[ctypes.c_void_p];t.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong];d=x.XOpenDisplay(None)
for name in sys.argv[1:]:
 k=x.XKeysymToKeycode(d,x.XStringToKeysym(name.encode()));t.XTestFakeKeyEvent(d,k,1,0);t.XTestFakeKeyEvent(d,k,0,0)
x.XFlush(d)
