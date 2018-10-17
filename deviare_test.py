import win32com.client
import ctypes, sys
import logging
import time


class NktSpyMgrEvents:

    def OnAgentLoad(self, proc, errorCode):
        # A few processes will fail due to restricted privileges.
        if not errorCode == 0:
            print("OnAgentLoad error code: %d" % (errorCode,))

    def OnProcessStarted(self, nktProcessAsPyIDispatch):
        nktProcess = win32com.client.Dispatch(nktProcessAsPyIDispatch)
        print("New Process: pid = {}, name = {}".format(nktProcess.Id, nktProcess.Name))

    def OnProcessTerminated(self, nktProcessAsPyIDispatch):
        nktProcess = win32com.client.Dispatch(nktProcessAsPyIDispatch)
        print("Process stopped: pid = {}, name = {}".format(nktProcess.Id, nktProcess.Name))

    def OnFunctionCalled(self, nktHookAsPyIDispatch, nktProcessAsPyIDispatch, nktHookCallInfoAsPyIDispatch):
        # We instantiate INktHookCallInfo and INktProcess objects. It's easy to get the hook through the call information object.
        nktHookCallInfo = win32com.client.Dispatch(nktHookCallInfoAsPyIDispatch)
        nktProcess = win32com.client.Dispatch(nktProcessAsPyIDispatch)
        print("process {}:{} called: {}".format(nktProcess.Name, nktProcess.Id, nktHookCallInfo.Hook().FunctionName))

class HookManager:

    # init with a spymanager
    def __init__(self, mgr):
        self.spy_mgr = mgr
        self.pids = set()
        self.mod_funcs = set()
        self.hooks_enum = self.spy_mgr.CreateHooksCollection()

    def add_hook(self, mod_fun, flag = 0x0001):
        # CreateHook takes a function string (whose format is functionModule!functionName) and flags to customize the hook.
        # PostCall only hook flag = 0x0020, PreCall only hook flag = 0x0010, AutoHookChildProcess flag = 0x0001
        if mod_fun in self.mod_funcs:
            return
        self.mod_funcs.add(mod_fun)
        hook = self.spy_mgr.CreateHook(mod_fun, flag) #
        hook.Hook(True)
        for pid in self.pids:
            hook.Attach(pid, True)
        self.hooks_enum.Add(hook)
        print("hook {} registered successfully.".format(mod_fun))


    def add_pid(self, pid):
        self.pids.add(pid)
        self.hooks_enum.Attach(pid, True)

    def exec(self, exe):
        app, continue_event = self.spy_mgr.CreateProcess(exe, True)
        self.add_pid(app.Id)
        self.spy_mgr.ResumeProcess(app, continue_event)



if __name__ == "__main__":
    win32com.client.pythoncom.CoInitialize()
    spyManager = win32com.client.DispatchWithEvents("DeviareCOM.NktSpyMgr", NktSpyMgrEvents)
    result = spyManager.Initialize()
    if not result == 0:
        print("ERROR: Could not initialize the SpyManager. Error code: %d" % (result))
        sys.exit(0)

    hook_mgr = HookManager(spyManager)
    hook_mgr.add_hook("Ws2_32.dll!WSAConnectByNameA")
    hook_mgr.add_hook("Ws2_32.dll!WSAConnectByNameW")
    hook_mgr.add_hook("Ws2_32.dll!gethostbyname")
    hook_mgr.add_hook("Ws2_32.dll!accept")
    hook_mgr.add_hook("Ws2_32.dll!WSAAccept")
    hook_mgr.add_hook("Mswsock.dll!AcceptEx")
    hook_mgr.add_hook("Mswsock.dll!GetAcceptExSockaddrs")
    hook_mgr.add_hook("Ws2_32.dll!getaddrinfo")
    hook_mgr.add_hook("Ws2_32.dll!GetAddrInfoExA")
    hook_mgr.add_hook("Ws2_32.dll!GetAddrInfoExW")
    hook_mgr.add_hook("Ws2_32.dll!GetAddrInfoW")
    hook_mgr.add_hook("Ws2_32.dll!WSASendTo")
    hook_mgr.add_hook("Ws2_32.dll!WSARecvFrom")
    hook_mgr.add_hook("Ws2_32.dll!sendto")
    hook_mgr.add_hook("Ws2_32.dll!recvfrom")
    hook_mgr.add_hook("Ws2_32.dll!connect")
    hook_mgr.add_hook("Ws2_32.dll!WSAConnect")
    hook_mgr.add_hook("Ws2_32.dll!WSAConnectByList")
    hook_mgr.add_hook("Ws2_32.dll!WSAConnectByNameA")
    hook_mgr.add_hook("Ws2_32.dll!WSAConnectByNameW")
    # hook_mgr.add_hook("kernel32.dll!CreateFileW")

    if len(sys.argv) >= 3 and sys.argv[1] == '-e':
        hook_mgr.exec(sys.argv[2])
    else:
        for pid in sys.argv[1:]:
            hook_mgr.add_pid(int(pid))

    MessageBox = ctypes.windll.user32.MessageBoxW
    MessageBox(None, "Press OK to end the demo.", "Deviare Python Demo", 0)


