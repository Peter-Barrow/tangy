#ifndef TIMETAG_H
#define TIMETAG_H

#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint8_t u8;
typedef int64_t i64;

typedef long long c_TimeType;
typedef u8 c_ChannelType;

typedef void* CTimeTag_ptr;

// Constructor and destructor
CTimeTag_ptr
CTimeTag_create();
void
CTimeTag_destroy(CTimeTag_ptr timetag);

// Main functions
void CTimeTag_open(CTimeTag_ptr timetag, int nr);

int CTimeTag_isOpen(CTimeTag_ptr timetag);

void CTimeTag_close(CTimeTag_ptr timetag);

void CTimeTag_calibrate(CTimeTag_ptr timetag);

void CTimeTag_setInputThreshold(CTimeTag_ptr timetag, int input, double voltage);

void CTimeTag_setFilterMinCount(CTimeTag_ptr timetag, int MinCount);

void CTimeTag_setFilterMaxTime(CTimeTag_ptr timetag, int MaxTime);

double CTimeTag_getResolution(CTimeTag_ptr timetag);

int CTimeTag_getFpgaVersion(CTimeTag_ptr timetag);

void CTimeTag_setLedBrightness(CTimeTag_ptr timetag, int percent);

// const char* CTimeTag_getErrorText(CTimeTag_ptr timetag, int flags);

void CTimeTag_enableGating(CTimeTag_ptr timetag, int enable);

void CTimeTag_gatingLevelMode(CTimeTag_ptr timetag, int enable);

void CTimeTag_setGateWidth(CTimeTag_ptr timetag, int duration);

void CTimeTag_switchSoftwareGate(CTimeTag_ptr timetag, int onOff);

void CTimeTag_setInversionMask(CTimeTag_ptr timetag, int mask);

void CTimeTag_setDelay(CTimeTag_ptr timetag, int Channel, int Delay);

int CTimeTag_readErrorFlags(CTimeTag_ptr timetag);

int CTimeTag_getNoInputs(CTimeTag_ptr timetag);

void CTimeTag_useTimetagGate(CTimeTag_ptr timetag, int use);

void CTimeTag_useLevelGate(CTimeTag_ptr timetag, int use);

int CTimeTag_levelGateActive(CTimeTag_ptr timetag);

void CTimeTag_use10MHz(CTimeTag_ptr timetag, int use);

void CTimeTag_setFilterException(CTimeTag_ptr timetag, int exception);

void CTimeTag_startTimetags(CTimeTag_ptr timetag);

void CTimeTag_stopTimetags(CTimeTag_ptr timetag);

int CTimeTag_readTags(CTimeTag_ptr timetag,
                  c_ChannelType* channel_ret,
                  c_TimeType* time_ret);

void CTimeTag_saveDcCalibration(CTimeTag_ptr timetag, char* filename);

void CTimeTag_loadDcCalibration(CTimeTag_ptr timetag, char* filename);

void CTimeTag_setFG(CTimeTag_ptr timetag, int period, int high);

void CTimeTag_setFGCount(CTimeTag_ptr timetag, int period, int high, int count);

int CTimeTag_getSingleCount(CTimeTag_ptr timetag, int i);

int64_t CTimeTag_freezeSingleCounter(CTimeTag_ptr timetag);

#ifdef __cplusplus
}
#endif

#endif // TIMETAG_H
