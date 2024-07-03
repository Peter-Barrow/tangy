from numpy cimport uint8_t, int8_t, int32_t, int64_t

ctypedef int8_t  Int8      # 8  bit integer for GCC
ctypedef int32_t Int32     # 32 bit integer for GCC
ctypedef int64_t Int64     # 64 bit integer for GCC
ctypedef uint8_t Uint8     #  8 bit unsigned int f GCC
ctypedef int32_t Bln32     # integer used as boolean
DEF LLXFORMAT = "PRIx64"   # 64 bit hex printf format
DEF LLDFORMAT = "PPRId64"  # 64 bit dec printf format

cdef extern from "../opt/QUTAG/userlib/inc/tdcbase.h":

    # Type of the TDC device
    ctypedef enum TDC_DevType:
        DEVTYPE_QUTAG_MC,    # quTAG MC device
        DEVTYPE_QUTAG_HR,    # quTAG HR device
        DEVTYPE_NONE         # No device / simulated device

    # Bitmasks for feature inquiry
    ctypedef enum TDC_FeatureFlag:
        FEATURE_HBT       = 0x0001, # Cross correlation (HBT) software functions
        FEATURE_LIFETIME  = 0x0002, # Lifetime software functions
        FEATURE_MARKERS   = 0x0020, # Marker input
        FEATURE_FILTERS   = 0x0040, # Event filters for timestamp stream
        FEATURE_EXTCLK    = 0x0080, # External clock enabled
        FEATURE_DEVSYNC   = 0x0100  # Synchronisation of multiple devices

    # A combination of feature Flags
    ctypedef Int32 TDC_FeatureFlags;

    # Output file format
    ctypedef enum TDC_FileFormat:
        FORMAT_ASCII,       # ASCII format
        FORMAT_BINARY,      # Uncompressed binary format (40B header, 10B/time tag)
        FORMAT_COMPRESSED,  # Compressed binary format   (40B header,  5B/time tag)
        FORMAT_RAW,         # Uncompressed binary without header (for compatiblity)
        FORMAT_NONE         # No format / invalid

    # Type of signal conditioning
    ctypedef enum TDC_SignalCond:
        SCOND_LVTTL = 1,  # For LVTTL signals:
                          #   Trigger at 2V rising edge, termination optional
        SCOND_NIM   = 2,  # For NIM signals:
                          #   Trigger at -0.6V falling edge, termination fixed on
        SCOND_MISC  = 3,  # Other signal type: Conditioning on, everything optional
        SCOND_NONE  = 4   # No signal / invalid

    # Type of output filter
    ctypedef enum TDC_FilterType:
        FILTER_NONE,     # No filter
        FILTER_MUTE,     # Mute filter
        FILTER_COINC,    # Coincidence filter
        FILTER_SYNC,     # Sync filter
        FILTER_INVALID   # invalid

    # Type of generated timestamps
    ctypedef enum TDC_SimType:
        SIM_FLAT,     # Time diffs and channel numbers uniformly distributed.
                      #   Requires 2 parameters: center, width for time diffs
                      #   in TDC units.
        SIM_NORMAL,   # Time diffs normally distributed, channels uniformly.
                      #   Requires 2 parameters: center, width for time diffs
                      #   int TDC units.
        SIM_NONE      # No type / invalid

    cdef double TDC_getVersion()

    cdef const char * TDC_perror( int rc )

    cdef int TDC_getTimebase( double * timebase )

    cdef int TDC_init( int deviceId )

    cdef int TDC_deInit()

    cdef TDC_DevType TDC_getDevType()

    cdef Bln32 TDC_checkFeatureHbt()

    cdef Bln32 TDC_checkFeatureLifeTime()

    cdef TDC_FeatureFlags TDC_checkFeatures()

    cdef Int32 TDC_getChannelCount()

    cdef int TDC_getClockState(Bln32* locked, Bln32* uplink )

    cdef int TDC_disableClockReset( Bln32 disable )

    cdef int TDC_getClockResetDisabled( Bln32 * disabled )

    cdef int TDC_preselectSingleStop( Bln32 single )

    cdef int TDC_getSingleStopPreselection( Bln32 * single )

    cdef int TDC_startCalibration()

    cdef int TDC_getCalibrationState( Bln32 * active )

    cdef int TDC_enableChannels( Bln32 enStart, Int32 channelMask )

    cdef int TDC_getChannelsEnabled( Bln32 * enStart, Int32 * channelMask )

    cdef int TDC_enableMarkers( Int32 markerMask )

    cdef int TDC_getMarkersEnabled( Int32 * markerMask )

    cdef int TDC_configureSignalConditioning( Int32          channel,
            TDC_SignalCond conditioning,
            Bln32          edge,
            double         threshold )

    cdef int TDC_getSignalConditioning( Int32    channel,
            Bln32  * edge,
            double * threshold )

    cdef int TDC_configureSyncDivider( Int32 divider,
            Bln32 reconstruct )

    cdef int TDC_getSyncDivider( Int32 * divider,
            Bln32 * reconstruct )

    cdef int TDC_setCoincidenceWindow( Int32 coincWin )

    cdef int TDC_configureFilter( Int32          channel,
            TDC_FilterType type,
            Int32          chMask )

    cdef int TDC_getFilter( Int32            channel,
            TDC_FilterType * type,
            Int32          * chMask )

    cdef int TDC_setExposureTime( Int32 expTime )

    cdef int TDC_getDeviceParams( Int32 * coincWin,
            Int32 * expTime   )

    cdef int TDC_setChannelDelay( Int32 channel, Int32 delay )

    cdef int TDC_getChannelDelay( Int32 channel, Int32 * delay )

    cdef int TDC_configureSelftest( Int32 channelMask,
            Int32 period,
            Int32 burstSize,
            Int32 burstDist )

    cdef int TDC_getDataLost( Bln32 * lost )

    cdef int TDC_setTimestampBufferSize( Int32 size )

    cdef int TDC_getTimestampBufferSize( Int32 * size )

    cdef int TDC_enableTdcInput( Bln32 enable )

    cdef int TDC_freezeBuffers( Bln32 freeze )

    cdef int TDC_getCoincCounters( Int32 * data, Int32 * updates )

    cdef int TDC_getLastTimestamps( Bln32   reset,
            Int64 * timestamps,
            Uint8 * channels,
            Int32 * valid )

    cdef int TDC_writeTimestamps( const char *   filename,
            TDC_FileFormat format )

    cdef int TDC_inputTimestamps( const Int64 * timestamps,
            const Uint8 * channels,
            Int32         count )

    cdef int TDC_readTimestamps( const char *   filename,
            TDC_FileFormat format )

    cdef int TDC_generateTimestamps( TDC_SimType type,
            double *    par,
            Int32       count )


cdef extern from "../opt/QUTAG/userlib/inc/tdcdecl.h":
    IF UNAME_SYSNAME == "Windows":
        ctypedef __int8  Int8              # 8  bit integer for MSVC
        ctypedef __int32 Int32             # 32 bit integer for MSVC
        ctypedef __int64 Int64             # 64 bit integer for MSVC
        ctypedef unsigned __int8 Uint8     #  8-Bit unsigned int for MSVC
        ctypedef __int32 Bln32             # integer used as boolean
        DEF LLXFORMAT =  "I64x"            # 64 bit hex printf format
        DEF LLDFORMAT =  "I64d"            # 64 bit dec printf format
        #undef  __STDC_FORMAT_MACROS
        #define __STDC_FORMAT_MACROS
    ELSE:
        #include <inttypes.h>
        cdef extern from 'inttypes.h':
            ctypedef int8_t  Int8      # 8  bit integer for GCC
            ctypedef int32_t Int32     # 32 bit integer for GCC
            ctypedef int64_t Int64     # 64 bit integer for GCC
            ctypedef uint8_t Uint8     #  8 bit unsigned int f GCC
            ctypedef int32_t Bln32     # integer used as boolean
        DEF LLXFORMAT = PRIx64         # 64 bit hex printf format
        DEF LLDFORMAT = PRId64         # 64 bit dec printf format

    DEF TDC_Ok =              0     # Success
    DEF TDC_Error =         (-1)    # Unspecified error
    DEF TDC_Timeout =         1     # Receive timed out
    DEF TDC_NotConnected =    2     # No connection was established
    DEF TDC_DriverError =     3     # Error accessing the USB driver
    DEF TDC_DeviceLocked =    7     # Can't connect device because already in use
    DEF TDC_Unknown =         8     # Unknown error
    DEF TDC_NoDevice =        9     # Invalid device number used in call
    DEF TDC_OutOfRange =     10     # Parameter in function call is out of range
    DEF TDC_CantOpen =       11     # Failed to open specified file
    DEF TDC_NotInitialized = 12     # Library has not been initialized
    DEF TDC_NotEnabled =     13     # Requested feature is not enabled
    DEF TDC_NotAvailable =   14     # Requested feature is not available


cdef extern from '../opt/QUTAG/userlib/inc/tdchg2.h':
    cdef int TDC_enableHg2( Bln32 enable )

    cdef int TDC_setHg2Params(Int32 binWidth,
                              Int32 binCount )

    cdef int TDC_getHg2Params(Int32* binWidth,
                              Int32* binCount )

    cdef int TDC_setHg2Input(Int32 idler,
                             Int32 channel1,
                             Int32 channel2 )

    cdef int TDC_getHg2Input(Int32* idler,
                             Int32* channel1,
                             Int32* channel2 )

    cdef int TDC_resetHg2Correlations()

    cdef int TDC_calcHg2G2(double* buffer,
                           Int32 * bufSize,
                           Bln32 reset )

    cdef int TDC_calcHg2Tcp(Int64** buffers,
                            Bln32 reset )

    cdef int TDC_calcHg2Tcp1D(Int64* buffer,
                              Int32* bufSize,
                              Bln32 reset )

    cdef int TDC_getHg2Raw(Int64* evtIdler,
                           Int64* evtCoinc,
                           Int64* bufSsi,
                           Int64* bufS2i,
                           Int32* bufSize )

cdef extern from '../opt/QUTAG/userlib/inc/tdcmultidev.h':
    cdef int TDC_discover(unsigned int* devCount)
    cdef int TDC_getDeviceInfo(unsigned int  devNo,
                               TDC_DevType* type,
                               int* id,
                               char* serialNo,
                               Bln32* connected)
    cdef int TDC_connect(unsigned int devNo)
    cdef int TDC_disconnect(unsigned int devNo)
    cdef int TDC_addressDevice(unsigned int devNo)
    cdef int TDC_getCurrentAddress(unsigned int* devNo)

cdef class StartStop():

    cdef Bln32 is_enabled(self)
    cdef Bln32 _bool32_to_bool(self, value)
    cdef Bln32 _bool_to_bool32(self, value)
    cdef void enable(self, enable)
    cdef void add_histogram(self, start, stop, add)


cdef extern from "../opt/QUTAG/userlib/inc/tdcstartstop.h":

    cdef int TDC_enableStartStop(Bln32 enable)

    cdef int TDC_addHistogram(Int32 startCh,
                              Int32 stopCh,
                              Bln32 add)

    cdef int TDC_setHistogramParams(Int32 binWidth,
                                    Int32 binCount)

    cdef int TDC_getHistogramParams(Int32* binWidth,
                                    Int32* binCount)

    cdef int TDC_clearAllHistograms()

    cdef int TDC_getHistogram(Int32 chStart,
                              Int32 chStop,
                              Bln32 reset,
                              Int32* data,
                              Int32* count,
                              Int32* tooSmall,
                              Int32* tooLarge,
                              Int32* starts,
                              Int32* stops,
                              Int64* expTime)
