# distutils: language = c++

import cython
import numpy as np
cimport numpy as cnp
from libcpp cimport bool
from _uqd cimport CTimeTag, CLogic

INPUT_THRESHOLD_ERROR_MESSAGE = '''Arguments must be a tuple.
\tEither (channel, voltage) or ([c1,c2,...cN], [v1,v2,...vN])'''

ERR_STR_DataOverflow = 'An overflow in the 512 k values SRAM FIFO has been detected. The time-tag generation rate is higher than the USB transmission rate.'
ERR_STR_NegFifoOverflow = 'Internal reason, should never occur'
ERR_STR_PosFifoOverflow = 'Internal reason, should never occur'
ERR_STR_DoubleError = 'One input had two pulses within the coincidence window.'
ERR_STR_InputFifoOverflow = 'More than 1024 successive tags were detected with a rate greater 100 MHz'
ERR_STR_10MHzHardError = 'The 10 MHz input is not connected or connected to a wrong type of signal.'
ERR_STR_10MHzSoftError = 'The 10 MHz input is connected, but the frequency is not 10 MHz.'
ERR_STR_OutFifoOverflow = 'Internal error, should never occur'
ERR_STR_OutDoublePulse = 'An output pulse was generated, while another pulse was still present on the same output. The pulse length is too long for the given rate.'
ERR_STR_OutTooLate = 'The internal processing was too slow. This is because the output event queue is too small for the given rate. Increase the value with SetOutputEventQueue()'

UQD_ERROR_FLAG = { 
        1: 'DataOverflow', 
        2: 'NegFifoOverflow',
        4: 'PosFifoOverflow',
        8: 'DoubleError',
        16: 'InputFifoOverflow',
        32: '10MHzHardError',
        64: '10MHzSoftError',
        128: 'OutFifoOverflow',
        256: 'OutDoublePulse',
        512: 'OutTooLate',
        }

UQD_ERROR_TEXT = {
        'DataOverflow': ERR_STR_DataOverflow,
        'NegFifoOverflow': ERR_STR_NegFifoOverflow,
        'PosFifoOverflow': ERR_STR_PosFifoOverflow,
        'DoubleError': ERR_STR_DoubleError,
        'InputFifoOverflow': ERR_STR_InputFifoOverflow,
        '10MHzHardError': ERR_STR_10MHzHardError,
        '10MHzSoftError': ERR_STR_10MHzSoftError,
        'OutFifoOverflow': ERR_STR_OutFifoOverflow,
        'OutDoublePulse': ERR_STR_OutDoublePulse,
        'OutTooLate': ERR_STR_OutTooLate,
        }


#cdef class pyTimeTag:
cdef class UQD:
    '''
    Wrapper class for Universal Quantum Devices Logic-16 time correlated
    single photon counting unit. Wraps functions found in CTimeTag and CLogic
    header files and associated timetag library
    '''

    cdef CTimeTag *c_timetag
    cdef CLogic *c_logic

    cdef unsigned char* CHANNEL
    cdef long long* TIMETAG

    cdef int device_id, n_ch, _filter_min_count, _filter_max_time, count
    cdef int _logic_enabled, ledBrightness, gating_enabled
    cdef double [::1] input_thresholds

    def __cinit__(self, int device_id=1):

        self.c_timetag = new CTimeTag()
        self.c_logic = new CLogic(self.c_timetag)

        if device_id is not 0:
            self.device_id = device_id
            #self.open(self.device_id)
            self.device = device_id
            self.n_ch = self.num_channels
            self.input_thresholds = np.zeros(self.n_ch, dtype=float)

        self._filter_min_count = 0
        self._filter_max_time = 0
        self._logic_enabled = 0
        self.ledBrightness = 100
        self.gating_enabled = 0

    def open(self, int device_id=1):
        self.device = device_id

    @property
    def device(self):
        cdef int res = self.c_timetag.IsOpen()
        if res == 1:
            return True, self.device_id
        else:
            return False, self.device_id

    @device.setter
    def device(self, int device_id):
        if device_id == 0:
            device_id += 1
        self.c_timetag.Open(device_id)

    def close(self):
        self.c_timetag.Close()
        return 1

    def __close__(self):
        print('Gracefully closing connection to device...')
        self.c_timetag.Close()

    def __exit__(self):
        print('Gracefully closing connection to device...')
        self.c_timetag.Close()

    def calibrate(self):
        self.c_timetag.Calibrate()

    def set_input_threshold(self, int c, double v):
        self.c_timetag.SetInputThreshold(c, v)
        self.inputThreshold[c-1] = v

    @property
    def input_threshold(self):
        return np.asarray(self.input_thresholds)

    @input_threshold.setter
    def input_threshold(self, channel_voltage):
        cdef int c
        cdef double v
        if len(channel_voltage) == 2:
            if isinstance(channel_voltage[0], (list, np.ndarray)):
                for (c, v) in zip(*channel_voltage):
                    self.c_timetag.SetInputThreshold(c+1, v)
                    self.input_thresholds[c] = v
            else:
                c, v = channel_voltage
                self.c_timetag.SetInputThreshold(c+1, v)
                self.input_thresholds[c] = v
        else:
            raise TypeError(INPUT_THRESHOLD_ERROR_MESSAGE)

    @property
    def filter_min_count(self):
        return self._filter_min_count

    @filter_min_count.setter
    def filter_min_count(self, int minimum_count):
        self._filter_min_count = minimum_count
        self.c_timetag.SetFilterMinCount(minimum_count)

    @property
    def filter_max_time(self):
        return self._filter_max_time
    
    @filter_max_time.setter
    def filter_max_time(self, int maximum_time):
        self._filter_max_time = maximum_time
        self.c_timetag.SetFilterMaxTime(maximum_time)

    @property
    def resolution(self):
        cdef double resolution = self.c_timetag.GetResolution()
        return resolution

    @property
    def fpga_version(self):
        cdef int version = self.c_timetag.GetFpgaVersion()
        return version

    @property
    def led_brightnes(self):
        return self.ledBrightness

    @led_brightnes.setter
    def led_brightnes(self, int percent):
        self.c_timetag.SetLedBrightness(percent)
        self.ledBrightness = percent

    def get_error_text(self, int flags):
        #return self.c_timetag.GetErrorText(flags)
        return UQD_ERROR_TEXT[UQD_ERROR_FLAG[flags]]

    @property
    def gating(self):
        return self.gating_enabled

    @gating.setter
    def gating(self, bool enable):
        self.c_timetag.EnableGating(enable)
        if self.gating:
            self.gating_enabled = False
        else:
            self.gating_enabled = True

    def gating_level_mode(self, bool enable):
        self.c_timetag.GatingLevelMode(enable)

    def switch_software_gate(self, bool enable):
        self.c_timetag.SwitchSoftwareGate(enable)

    def inversion_mask(self, int mask):
        self.c_timetag.SetInversionMask(mask)

    def set_delay(self, int channel, int delay):
        self.c_timetag.SetDelay(channel, delay)
        #if self._logic_enabled:
        #    self.c_timetag.SetDelay(channel, delay)
        #else:
        #    self.c_logic.SetDelay(channel, delay)

    def read_error_flags(self):
        return self.c_timetag.ReadErrorFlags()
    
    @property
    def num_channels(self):
        return self.c_timetag.GetNoInputs()

    def use_timetag_gate(self, bool use):
        self.c_timetag.UseTimetagGate(use)

    def use_level_gate(self, bool use):
        self.c_timetag.UseLevelGate(use)

    def level_gate_active(self):
        return self.c_timetag.LevelGateActive()

    def use_10MHz(self, bool use):
        self.c_timetag.Use10MHz(use)

    def set_filter_exception(self, int exception):
        self.c_timetag.SetFilterException(exception)
    
    def start_timetags(self):
        self.c_timetag.StartTimetags()
    
    def stop_timetags(self):
        self.c_timetag.StopTimetags()
    
    def read_tags(self):
        #cdef unsigned char* CHANNEL
        #cdef long long* TIMETAG
        #cdef int count = self.c_timetag.ReadTags(CHANNEL, TIMETAG)
        self.count = self.c_timetag.ReadTags(self.CHANNEL, self.TIMETAG)
    
        if self.count == 0:
            return self.count, None, None
    
        else:
            channels = np.zeros(self.count, dtype=np.uint8)
            timetags = np.zeros(self.count, dtype=np.uint64)
    
            for i in range(self.count):
                channels[i] = self.CHANNEL[i]
                timetags[i] = self.TIMETAG[i]
    
        return self.count, channels, timetags

    # Logic mode functions

    @property
    def logic_mode(self):
        if self._logic_enabled:
            return True
        else:
            return False

    @logic_mode.setter
    def logic_mode(self, state):
        if state:
            self.c_logic.SwitchLogicMode()
            self._logic_enabled = True
        else:
            self.c_logic.SwitchLogicMode()
            self._logic_enabled = False


    def switch_logic_mode(self):
        self.c_logic.SwitchLogicMode()

    def set_window_width(self, int window):
        self.c_logic.SetWindowWidth(window)
    
    def read_logic(self):
        self.c_logic.ReadLogic()

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def calc_count_pos(self, pattern):
        cdef int pattern_value = 0
        cdef int cur_idx

        if isinstance(pattern, (int)):
            pattern = np.array([pattern], dtype=int)
        elif isinstance(pattern, (list, np.ndarray)):
            pattern = np.array(pattern, dtype=list)

        cur_idx = pattern.shape[0] - 1
        for bit in reversed(range(self.n_ch)):
            if bit == pattern[cur_idx]:
                pattern_value = (pattern_value * 2) + 1
                cur_idx -= 1
            else:
                pattern_value *= 2

        return self.c_logic.CalcCountPos(pattern_value)

    # libTCSPC buffer stuff...
    # cdef void buffer_write(const tag_buffer* const buffer,
    #                   const uint64_t timetag,
    #                   const int channel)
    # cdef tag_buffer* connect_to_tag_buffer(const int map_num,
    #                                   const int map_type)
    

    # def create_buffer(self, buffer_number=0, create=True, buffer_size=None):
    #     if buffer_size:
    #         record_buffer = timetag_buffer(buffer_number= buffer_number,
    #                                        create= create,
    #                                        buffer_size= buffer_size,
    #                                        buffer_type= 0,
    #                                        resolution= self.resolution)
    #     else:
    #         record_buffer = timetag_buffer(buffer_number= buffer_number,
    #                                        create= create,
    #                                        buffer_type= 0,
    #                                        resolution= self.resolution)

    #     # self.t_buf = c_buffer.connect_to_tag_buffer(buffer_number, 0)
    #     self.t_buf = c_buffer.connect_to_tag_buffer(buffer_number)

    #     return record_buffer

    # @cython.boundscheck(False)
    # @cython.wraparound(False)
    # cdef int _write_to_buffer(self):

    #     cdef int count = self.c_timetag.ReadTags(self.CHANNEL, self.TIMETAG)
    # 
    #     for i in range(count):
    #         c_buffer.buffer_write(self.t_buf,
    #                               self.TIMETAG[i],
    #                               self.CHANNEL[i])
    # 
    #     return count

    # def write_to_buffer(self):
    #     return self._write_to_buffer()

