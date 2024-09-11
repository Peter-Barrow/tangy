#ifndef __MEASUREMENT__
#define __MEASUREMENT__

#include "base.h"

typedef enum {
    MEASUREMENT_Ok,
    ECHANNELCOUNT,

} MeasurementError;

typedef enum {
    FMCHANNELS = 1 << 0,
    FMDELAYS = 1 << 1,
    FMCLOCK = 1 << 2,
    FMREAD_TIME = 1 << 3,
    FMSTART_INDEX = 1 << 4,
    FMSTOP_INDEX = 1 << 5,
    FMRADIUS = 1 << 6,
    FMRESOLUTION = 1 << 7,
} MeasureFlags;

#define FLAGMAX 7
#define FLAGMAXVALUE 1 << FLAGMAX

typedef u32 fmsrmnt;

#define B fmsrmnt
#define BSET MeasureFlags
#include "bitflags_tmpl.h"
/* Including this header will add the following types and functions
 *
 *  bf_fmsrmnt_Result struct {
 *      bool Ok;
 *      fmsrmnt bit_flag;
 *  };
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_flag_from_position(u8 position, int max_flag);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_set(fmsrmnt bit_flag,
 *                                  fmsrmnt target,
 *                                  fmsrmnt max_flag);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_set_position(fmsrmnt bit_flag,
 *                                           u8 position,
 *                                           fmsrmnt max_flag);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_unset(fmsrmnt bit_flag,
 *                                    fmsrmnt target,
 *                                    fmsrmnt max_flag);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_unset_position(fmsrmnt bit_flag,
 *                                             u8 position,
 *                                             fmsrmnt max_flag);
 *
 * bool bf_fmsrmnt_contains(fmsrmnt bit_flag,
 *                          fmsrmnt target,
 *                          fmsrmnt max_flag);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_extract(fmsrmnt bit_flag,
 *                                      fmsrmnt num_flags,
 *                                      MeasureFlags* collection);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_extract_positions(fmsrmnt bit_flag,
 *                                                fmsrmnt max_flag,
 *                                                u8* collection);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_collect(const MeasureFlags* const targets,
 *                                      const u64 n_targets,
 *                                      fmsrmnt max_flag);
 *
 * bf_fmsrmnt_Result bf_fmsrmnt_collect_positions(const u8* const targets,
 *                                                const u64 n_targets,
 *                                                fmsrmnt max_flag);
 */

fmsrmnt
measurement_set_flag(const fmsrmnt target, const MeasureFlags flag);
fmsrmnt
measurement_unset_flag(const fmsrmnt target, const MeasureFlags flag);
bool
measurement_contains_flag(const fmsrmnt target, const MeasureFlags flag);

typedef struct Measurement Measurement;
struct Measurement {
    MeasureFlags features;
    u64 n_channels;
    u8* channels;
    f64* delays;
    u8 clock;
    f64 read_time;
    u64 start_index;
    u64 stop_index;
    f64 radius;
    f64 resolution;
};

MeasurementError
measurement_add_channels(Measurement* conf, u64 n_channels, u8* channels);
MeasurementError
measurement_add_delays(Measurement* conf, u64 n_channels, f64* delays);

#endif
