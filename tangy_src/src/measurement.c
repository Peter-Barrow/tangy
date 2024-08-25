#include "measurement.h"

m_flag measurement_set_flag(const m_flag target, const measurement_flags flag) {
    return target | flag;
}

m_flag measurement_unset_flag(const m_flag target, const measurement_flags flag){
    return target & (~flag);
}

bool measurement_contains_flag(const m_flag target, const measurement_flags flag){
    return (target & flag) == flag;
}

