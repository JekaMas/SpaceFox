import ctypes,sys
from pathlib import Path
class Image(ctypes.Structure):
 _fields_=[('width',ctypes.c_int),('height',ctypes.c_int),('xoffset',ctypes.c_int),('format',ctypes.c_int),('data',ctypes.c_void_p),('byte_order',ctypes.c_int),('bitmap_unit',ctypes.c_int),('bitmap_bit_order',ctypes.c_int),('bitmap_pad',ctypes.c_int),('depth',ctypes.c_int),('bytes_per_line',ctypes.c_int),('bits_per_pixel',ctypes.c_int),('red_mask',ctypes.c_ulong),('green_mask',ctypes.c_ulong),('blue_mask',ctypes.c_ulong)]
x=ctypes.CDLL('libX11.so.6');x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=ctypes.c_void_p;x.XDefaultRootWindow.argtypes=[ctypes.c_void_p];x.XDefaultRootWindow.restype=ctypes.c_ulong
x.XGetImage.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_int,ctypes.c_uint,ctypes.c_uint,ctypes.c_ulong,ctypes.c_int];x.XGetImage.restype=ctypes.POINTER(Image)
d=x.XOpenDisplay(None);assert d
im=x.XGetImage(d,x.XDefaultRootWindow(d),0,0,1024,768,0xffffffffffffffff,2);assert im
v=im.contents;assert v.bits_per_pixel==32 and v.byte_order==0
raw=ctypes.string_at(v.data,v.bytes_per_line*v.height);out=bytearray()
for y in range(v.height):
 for z in range(v.width):
  i=y*v.bytes_per_line+z*4;b,g,r,_=raw[i:i+4];out.extend((r,g,b))
Path(sys.argv[1]).write_bytes(('P6\n%d %d\n255\n'%(v.width,v.height)).encode()+out)
