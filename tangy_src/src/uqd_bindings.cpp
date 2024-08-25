#include "CTimeTag.h"
#include "uqd_bindings.h"
#include <cstring>
#include <stdexcept>
#include <vector>


extern "C" {

CTimeTag_ptr CTimeTag_create() {
    return new TimeTag::CTimeTag();
}

void CTimeTag_destroy(CTimeTag_ptr timetag) {
    delete reinterpret_cast<TimeTag::CTimeTag*>(timetag);
}

void CTimeTag_open(CTimeTag_ptr timetag, int nr) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->Open(nr);
}

int CTimeTag_isOpen(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->IsOpen() ? 1 : 0;
}

void CTimeTag_close(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->Close();
}

void CTimeTag_calibrate(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->Calibrate();
}

void CTimeTag_setInputThreshold(CTimeTag_ptr timetag, int input, double voltage) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetInputThreshold(input, voltage);
}

void CTimeTag_setFilterMinCount(CTimeTag_ptr timetag, int MinCount) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetFilterMinCount(MinCount);
}

void CTimeTag_setFilterMaxTime(CTimeTag_ptr timetag, int MaxTime) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetFilterMaxTime(MaxTime);
}

double CTimeTag_getResolution(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->GetResolution();
}

int CTimeTag_getFpgaVersion(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->GetFpgaVersion();
}

void CTimeTag_setLedBrightness(CTimeTag_ptr timetag, int percent) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetLedBrightness(percent);
}

// const char* CTimeTag_getErrorText(CTimeTag_ptr timetag, int flags) {
//     auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
//     return ptr->GetErrorText(flags).c_str();
// }

void CTimeTag_enableGating(CTimeTag_ptr timetag, int enable) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->EnableGating(enable != 0);
}

void CTimeTag_gatingLevelMode(CTimeTag_ptr timetag, int enable) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->GatingLevelMode(enable != 0);
}

void CTimeTag_setGateWidth(CTimeTag_ptr timetag, int duration) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetGateWidth(duration);
}

void CTimeTag_switchSoftwareGate(CTimeTag_ptr timetag, int onOff) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SwitchSoftwareGate(onOff != 0);
}

void CTimeTag_setInversionMask(CTimeTag_ptr timetag, int mask) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetInversionMask(mask);
}

void CTimeTag_setDelay(CTimeTag_ptr timetag, int Input, int Delay) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetDelay(Input, Delay);
}

int CTimeTag_readErrorFlags(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->ReadErrorFlags();
}

int CTimeTag_getNoInputs(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->GetNoInputs();
}

void CTimeTag_useTimetagGate(CTimeTag_ptr timetag, int use) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->UseTimetagGate(use != 0);
}

void CTimeTag_useLevelGate(CTimeTag_ptr timetag, int use) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->UseLevelGate(use != 0);
}

int CTimeTag_levelGateActive(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->LevelGateActive() ? 1 : 0;
}

void CTimeTag_use10MHz(CTimeTag_ptr timetag, int use) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->Use10MHz(use != 0);
}

void CTimeTag_setFilterException(CTimeTag_ptr timetag, int exception) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetFilterException(exception);
}

void CTimeTag_startTimetags(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->StartTimetags();
}

void CTimeTag_stopTimetags(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->StopTimetags();
}

int CTimeTag_readTags(CTimeTag_ptr timetag, c_ChannelType* channel_ret, c_TimeType* time_ret) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->ReadTags(channel_ret, time_ret);
}

void CTimeTag_saveDcCalibration(CTimeTag_ptr timetag, char* filename) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SaveDcCalibration(filename);
}

void CTimeTag_loadDcCalibration(CTimeTag_ptr timetag, char* filename) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->LoadDcCalibration(filename);
}

void CTimeTag_setFG(CTimeTag_ptr timetag, int period, int high) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetFG(period, high);
}

void CTimeTag_setFGCount(CTimeTag_ptr timetag, int period, int high, int count) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    ptr->SetFGCount(period, high, count);
}

int CTimeTag_getSingleCount(CTimeTag_ptr timetag, int i) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->GetSingleCount(i);
}

int64_t CTimeTag_freezeSingleCounter(CTimeTag_ptr timetag) {
    auto ptr = reinterpret_cast<TimeTag::CTimeTag*>(timetag);
    return ptr->FreezeSingleCounter();
}

} // extern "C"
