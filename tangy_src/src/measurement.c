#include "measurement.h"

fmsrmnt
measurement_set_flag(const fmsrmnt target, const MeasureFlags flag) {
    bf_fmsrmnt_Result result = bf_fmsrmnt_set(target, flag, FLAGMAXVALUE);

    return result.bit_flag;
}

fmsrmnt
measurement_unset_flag(const fmsrmnt target, const MeasureFlags flag) {

    bf_fmsrmnt_Result result = bf_fmsrmnt_unset(target, flag, FLAGMAXVALUE);

    return result.bit_flag;
}


bool
measurement_contains_flag(const fmsrmnt target, const MeasureFlags flag) {
    return bf_fmsrmnt_contains(target, flag, FLAGMAXVALUE);
}

static inline MeasurementError
_assert_number_of_channels(Measurement* conf, u64 n_channels) {
    if (conf->n_channels == 0) {
        conf->n_channels = n_channels;
    }

    if (conf->n_channels != n_channels) {
        return ECHANNELCOUNT;
    }

    return MEASUREMENT_Ok;
}

#define ASSERT_NUM_CHANNELS(ERR, CONF, NC)                                     \
    ERR = _assert_number_of_channels(CONF, NC);                                \
    if (ERR != MEASUREMENT_Ok) {                                               \
        return ERR;                                                            \
    }

MeasurementError
measurement_add_channels(Measurement* conf, u64 n_channels, u8* channels) {
    MeasurementError err = MEASUREMENT_Ok;

    ASSERT_NUM_CHANNELS(err, conf, n_channels);

    // move channels array
    conf->channels = channels;
    channels = NULL;

    conf->features = measurement_set_flag(conf->features, FMCHANNELS);

    return err;
}

MeasurementError
measurement_add_delays(Measurement* conf, u64 n_channels, f64* delays) {
    MeasurementError err = MEASUREMENT_Ok;

    ASSERT_NUM_CHANNELS(err, conf, n_channels);

    // move delays array
    conf->delays = delays;
    delays = NULL;

    conf->features = measurement_set_flag(conf->features, FMDELAYS);
    return err;
}
