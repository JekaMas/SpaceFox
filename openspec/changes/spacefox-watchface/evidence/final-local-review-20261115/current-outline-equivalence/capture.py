import ctypes,struct,zlib,sys
X=ctypes.CDLL('libX11.so.6');X.XOpenDisplay.argtypes=[ctypes.c_char_p];X.XOpenDisplay.restype=ctypes.c_void_p;X.XDefaultRootWindow.argtypes=[ctypes.c_void_p];X.XDefaultRootWindow.restype=ctypes.c_ulong;X.XGetImage.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_int,ctypes.c_uint,ctypes.c_uint,ctypes.c_ulong,ctypes.c_int];X.XGetImage.restype=ctypes.c_void_p;X.XGetPixel.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int];X.XGetPixel.restype=ctypes.c_ulong
D=X.XOpenDisplay(None);assert D;root=X.XDefaultRootWindow(D);im=X.XGetImage(D,root,88,255,390,390,0xffffffff,2);assert im
rows=[]
for y in range(390):
 row=bytearray([0])
 for x in range(390):
  p=X.XGetPixel(im,x,y);row.extend(((p>>16)&255,(p>>8)&255,p&255))
 rows.append(row)
def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
open('/out/equivalence/phase-'+sys.argv[1]+'.png','wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',390,390,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows),6))+chunk(b'IEND',b''))
