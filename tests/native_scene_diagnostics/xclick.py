import ctypes,sys
x=ctypes.CDLL('libX11.so.6'); t=ctypes.CDLL('libXtst.so.6')
x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=ctypes.c_void_p
x.XFlush.argtypes=[ctypes.c_void_p]
t.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong];t.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
d=x.XOpenDisplay(None);assert d;t.XTestFakeMotionEvent(d,-1,int(sys.argv[1]),int(sys.argv[2]),0);button=int(sys.argv[3]) if len(sys.argv)>3 else 1;t.XTestFakeButtonEvent(d,button,1,0);t.XTestFakeButtonEvent(d,button,0,0);x.XFlush(d)
