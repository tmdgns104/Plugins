import pyvisa
import time
import datetime


class KIKUSUICtrl:
    def __init__(self):
        self._isConnected = False
        self._kikusui_dev = None
        self._defaultRM = None
        self._portNum = 0


    def Open(self, port):
        if self._portNum == 0:
            self._portNum = int(port[3:])

        print("[KIKUSUI_Ctrl_Client] Kikusui Power Connect....")

        if self._isConnected:
            print("[KIKUSUI_Ctrl_Client] Already connected")
            return "pass"
        else:
            try:
                self._defaultRM = pyvisa.ResourceManager("@py")
                if len(self._defaultRM.list_resources()) > 0:
                    addr = 'ASRL{0}::INSTR'.format(self._portNum)
                    self._kikusui_dev = self._defaultRM.open_resource(addr)
                else:
                    print("[KIKUSUI_Ctrl_Client] Kikusui Power is not exist!!")
                    return "PortErr"
                print("[KIKUSUI_Ctrl_Client] Kikusui Power Connect Ok")
                self._isConnected = True
            except Exception as ex:
                print("[KIKUSUI_Ctrl_Client] Kikusui Power Connect fail!! [{0}]".format(str(ex)))
                return "IvalPramErr", str(ex)
        return "pass"


    def Close(self):
        print("[KIKUSUI_Ctrl_Client] Kikusui Power Disconnect...")
        if self._isConnected:
            try:
                if self._kikusui_dev is not None:
                    self._kikusui_dev.close()
                    self._kikusui_dev = None
                if self._defaultRM is not None:
                    self._defaultRM.close()
                    self._defaultRM = None
                self._isConnected = False
            except Exception as ex:
                print("[KIKUSUI_Ctrl_Client] Kikusui Power disconnect fail!! [{0}]".format(str(ex)))
                return "Err"
        else:
            print("[KIKUSUI_Ctrl_Client] Already disconnected")
            return "pass"
        return "pass"


    def ReadString(self):
        result = ''
        try:
            print("[KIKUSUI_Ctrl_Client] ReadString..............")
            readstr = self._kikusui_dev.read()
            left_mark_pos = readstr.find('\x13\x11')
            right_mark_pos = readstr.find('\r\n')
            if left_mark_pos >= 0:
                if right_mark_pos >= 0:
                    resultstr = str(readstr[2:right_mark_pos])
                else:
                    resultstr = str(readstr[2:])
            else:
                if right_mark_pos >= 0:
                    resultstr = str(readstr[:right_mark_pos])
                else:
                    resultstr = str(readstr[:])
            return "pass", resultstr
        except Exception as ex:
            print("[KIKUSUI_Ctrl_Client] ReadString fail!! [{0}]".format(str(ex)))
            return "Err", str(ex)


    def sendCommand(self, command, readResponse=1):
        print("[KIKUSUI_Ctrl_Client] SendCommand[{0}].....".format(command))
        if self._isConnected:
            if self._kikusui_dev is None:
                return "ExceptErr", "Kikusui resource is none!!"
            if readResponse:
                return self._SendCommand(command, True)
            else:
                return self._SendCommand(command, False)
        else:
            print("[KIKUSUI_Ctrl_Client] Kikusui not connected!!!")
            return "Err", 'Kikusui not connected!!'

    def _SendCommand(self, command, readResponse=True):
        try:
            self._kikusui_dev.write(command.rstrip() + "\n")
            print("[KIKUSUI_Ctrl_Client] SendCommand OK!!")
            if readResponse and '?' in command:
                return self.ReadString()
            return "pass", ""
        except Exception as ex:
            print("[KIKUSUI_Ctrl_Client] SendCommand fail!! [{0}]...".format(str(ex)))
            return "Err", str(ex)


    def SetVolt(self, volt):
        volt = float(volt)
        strcmd = 'VOLT %.3f' % volt
        return self.sendCommand(strcmd, 0)


    def WaveOpen(self, nProgramNum):
        strcmd = 'PROG:NAME "{0}"'.format(nProgramNum)
        return self.sendCommand(strcmd, 0)


    def WaveRun(self):
        return self.sendCommand("PROG:EXEC:STAT RUN", 0)


    def WaveStop(self):
        return self.sendCommand("PROG:EXEC:STAT STOP", 0)


    def ReadVolt(self):
        return self.sendCommand("READ:VOLT?")


    def ReadCurr(self):
        return self.sendCommand("READ:CURR?")


    def FetcVolt(self):
        return self.sendCommand("FETC:VOLT?")


    def FetcCurr(self):
        return self.sendCommand("FETC:CURR?")

    def Timer_Compare(self, Time_Init, Time_check):
        nTime = time.time() - Time_Init
        mydelta = datetime.timedelta(seconds=nTime)
        mytime = datetime.datetime.min + mydelta
        h, m, s = mytime.hour, mytime.minute, mytime.second
        ret = ("%d hour %02d minute %02d second" % (h, m, s))
        return ret


    def Kikusui_Current(self, minCurr, maxCurr, compTime):
        count = 0
        cnt_sec = float(compTime) / 1000.0
        fMin = float(minCurr)
        fMax = float(maxCurr)
        ret_time = ' '
        errortext = 'all error'

        if fMax is not None and fMin is not None:
            startTime = time.time()
            while True:
                time.sleep(0.2)
                cnt_sec -= 0.4
                ret, curr = self.ReadCurr()
                try:
                    current = float(curr)
                except:
                    current = -1
                if current < 0:
                    current = 0

                if current >= fMin and current <= fMax:
                    count += 1
                else:
                    ret = "ExceptErr"
                    errortext = "{0} Current Check Fail!! Value is {1}".format(ret_time, current)
                    count = 0
                if cnt_sec <= 0:
                    break
                elif count >= 10:
                    endTime = time.time()
                    ret_time = self.Timer_Compare(startTime, endTime)
                    ret = "pass"
                    errortext = "{0} Current Check Pass!! value is {1}".format(ret_time, current)
                    break
        else:
            ret = ('error', 'invalid data: {0}'.format(compTime))
            return ret

        if ret == 'ExceptErr':
            final_ret = ('fail', errortext)
        elif ret != "pass":
            final_ret = ("error", errortext)
        else:
            final_ret = ("pass", errortext)

        return final_ret