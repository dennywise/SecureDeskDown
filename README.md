# SecureDeskDown
SecureDeskDown: Unprivileged Keystroke Injection to SYSTEM via G HUB. Local Privilege Escalation via UAC Bypass.

## Full public disclosure as they see this as 'informative'.

A non-elevated local process opens a LocalSystem kernel driver's control device and executes its device-control IOCTLs. The driver's purpose is synthetic keyboard/mouse input, so this is an unauthenticated input-injection primitive available to any user.

## 1 · The flaw

The G HUB virtual-HID bus (device `ROOT\SYSTEM\0001`, drivers `logi_joy_bus_enum.x64.sys` + filter `logi_joy_xlcore.x64.sys`) registers two custom device-interface GUIDs:

```
\\?\ROOT#SYSTEM#0001#{dfbedcdd-2148-416d-9e4d-cecc2424128c}
\\?\ROOT#SYSTEM#0001#{1abc05c0-c378-41b9-9cef-df1aba82b015}
```

Both are openable read-write by any user - the `IRP_MJ_CREATE` handler applies no privilege check. The `IRP_MJ_DEVICE_CONTROL` dispatcher (`bus_enum` `sub_140007090`, `xlcore` `sub_1400021c0`) then processes the caller's IOCTLs with **no authorization check**. The driver records owner PIDs (IOCTL `0x2a2044` plus a process-exit notify routine) but only for lifecycle cleanup; that list is never consulted to gate commands. The data-carrying IOCTLs - including the ones that set the virtual keyboard/mouse HID report state - are reachable by anyone.

## 2 · Why it is a privilege-escalation 

The drivers exist to inject keyboard and mouse input (G HUB key remapping and macros) through virtual HID devices. Input emitted by a kernel HID device is indistinguishable from real hardware, so it is **not** subject to UIPI/`SendInput` restrictions: it can target higher-integrity windows and the UAC secure desktop. An unprivileged process that can command this driver can therefore synthesize trusted input into elevated contexts - the classic path from Medium integrity to SYSTEM/admin via a consent prompt or an elevated application.

