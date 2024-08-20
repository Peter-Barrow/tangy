from libcpp cimport bool
from libcpp.string cimport string

cdef extern from "CTimeTag.h" namespace "TimeTag":
    cdef cppclass CTimeTag:
        CTimeTag()

        void Open(int)
        int IsOpen()
        void Close()
        void Calibrate()
        void SetInputThreshold(int input_channel, double voltage)
        void SetFilterMinCount(int MinCount)

        void SetFilterMaxTime(int MaxTime)

        double GetResolution()
        int GetFpgaVersion()
        void SetLedBrightness(int percent)
        string GetErrorText(int flags)
        void EnableGating(bool enable)
        void GatingLevelMode(bool enable)
        void SetGateWidth(int duration)
        void SwitchSoftwareGate(bool onOff)

        void SetInversionMask(int mask)
        void SetDelay(int Input, int Delay)
        int ReadErrorFlags()
        int GetNoInputs()
        void UseTimetagGate(bool use)
        void UseLevelGate(bool p)
        bool LevelGateActive()
        void Use10MHz(bool use)
        void SetFilterException(int exception)

        void StartTimetags()
        void StopTimetags()
        int ReadTags(unsigned char* channel_ret, long long *time_ret)

        void SaveDcCalibration(char * filename)
        void LoadDcCalibration(char * filename)
        void SetFG(int period, int high)


cdef extern from "CLogic.h" namespace "TimeTag":
    cdef cppclass CLogic(CTimeTag):
        CLogic(CTimeTag *interface)

        void SwitchLogicMode()

        void SetWindowWidth(int window)
        void SetWindowWidthEx(int index, int window)
        void SetDelay(int channel, int delay)
        void ReadLogic()
        int CalcCountPos(int pattern)

        int CalcCount(int pos, int neg)
        int GetTimeCounter()

        void SetOutputWidth(int width)

        void SetOutputPattern(int output, int pos, int neg)
        void SetOutputEventCount(int events)

cdef inline void ctimetag_new(CTimeTag* ctt):
    ctt = new CTimeTag()

cdef inline void clogic_new(CTimeTag* ctt, CLogic* cl):
    cl = new CLogic(ctt)
