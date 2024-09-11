#ifndef B
#error " template type 'B' supplied for bit field"
#endif

#ifndef BSET
#error " template type 'BSET' supplied for bit field"
#endif

#define __BITFLAGS__

#include "base.h"

#define BFLAG_STUB JOIN(bf, B)
#define FN_BFLAG(fn) JOIN(BFLAG_STUB, fn)
#define MAX_SHIFT sizeof(B) * 8

typedef struct JOIN(BFLAG_STUB, Result) JOIN(BFLAG_STUB, Result);
struct JOIN(BFLAG_STUB, Result) {
    bool Ok;
    B bit_flag;
};

#define RESULT JOIN(BFLAG_STUB, Result)

#define FLAG_IN_RANGE(RESULT, TARGET, MAXFLAG)                                 \
    if (!(TARGET <= MAXFLAG)) {                                                \
        return RESULT;                                                         \
    }

#define POSITION_IN_RANGE(RESULT, POSITION)                                    \
    if (!(POSITION <= MAX_SHIFT)) {                                            \
        return RESULT;                                                         \
    }

static inline RESULT
FN_BFLAG(flag_from_position)(u8 position, B max_flag) {
    RESULT result = { 0 };
    POSITION_IN_RANGE(result, position)
    result.bit_flag = 1 << position;
    result.Ok = true;
    return result;
}
#define _flag_from_position(pos, max) FN_BFLAG(flag_from_position)(pos, max)

static inline RESULT
FN_BFLAG(set)(B bit_flag, B target, B max_flag) {
    RESULT result = { 0 };

    FLAG_IN_RANGE(result, target, max_flag)

    result.bit_flag = target | bit_flag;
    result.Ok = true;

    return result;
}
#define _set_flag(bitflag, target, max) FN_BFLAG(set)(bitflag, target, max)

static inline RESULT
FN_BFLAG(set_position)(B bit_flag, u8 position, B max_flag) {
    RESULT result = _flag_from_position(position, max_flag);
    if (result.Ok == false) {
        return result;
    }

    result = _set_flag(bit_flag, result.bit_flag, max_flag);
    return result;
}
#define _set_position(bitflag, pos, max)                                       \
    FN_BFLAG(set_position)(bitflag, pos, max)

static inline RESULT
FN_BFLAG(unset)(B bit_flag, B target, B max_flag) {
    RESULT result = { 0 };

    FLAG_IN_RANGE(result, target, max_flag)

    result.bit_flag = bit_flag & (~target);
    result.Ok = true;

    return result;
}
#define _unset_flag(bitflag, target, max) FN_BFLAG(unset)(bitflag, target, max)

static inline RESULT
FN_BFLAG(unset_position)(B bit_flag, u8 position, B max_flag) {
    RESULT result = _flag_from_position(position, max_flag);
    if (result.Ok == false) {
        return result;
    }

    result = _unset_flag(bit_flag, result.bit_flag, max_flag);

    return result;
}
#define _unset_position(bitflag, pos, max)                                     \
    FN_BFLAG(unset_position)(bitflag, pos, max)

static inline bool
FN_BFLAG(contains)(B bit_flag, B target, B max_flag) {
    bool result = false;

    // FLAG_IN_RANGE(result, target, max_flag)

    if ((target & bit_flag) == target) {
        result = true;
        return result;
    }

    return result;
}
#define _contains(bitflag, target, max)                                        \
    FN_BFLAG(contains)(bitflag, target, max)

static inline RESULT
FN_BFLAG(extract)(B bit_flag, B num_flags, BSET* collection) {
    RESULT result = { 0 };
    int j = 0;
    B flag_max = 1 << num_flags;
    for (int i = 0; i < num_flags; i++) {
        RESULT current_flag = _flag_from_position(i, flag_max);
        if(_contains(bit_flag, current_flag.bit_flag, flag_max)) {
            result.Ok = false;
            result.bit_flag = current_flag.bit_flag;
        }

        collection[j] = (BSET)current_flag.bit_flag;
        j += 1;
    }

    result.Ok = true;
    return result;
}

static inline RESULT
FN_BFLAG(extract_positions)(B bit_flag, B max_flag, u8* collection) {

    RESULT result = { 0 };
    int j = 0;
    for (u8 i = 0; i < max_flag; i++) {
        RESULT current_flag = _flag_from_position(i, max_flag);
        if (_contains(bit_flag, current_flag.bit_flag, max_flag)) {
            result.Ok = false;
            result.bit_flag = 1 << i;
            return result;
        }
        collection[j] = i;
        j += 1;
    }

    result.Ok = true;
    return result;
}

static inline RESULT
FN_BFLAG(collect)(const BSET* const targets, const u64 n_targets, B max_flag) {

    RESULT result = { 0 };
    for (int i = 0; i < n_targets; i++) {
        FLAG_IN_RANGE(result, targets[i], max_flag)

        result = _set_flag(result.bit_flag, targets[i], max_flag);
        if (result.Ok == false) {
            return result;
        }
    }

    result.Ok = true;
    return result;
}

static inline RESULT
FN_BFLAG(collect_positions)(const u8* const targets,
                             const u64 n_targets,
                             B max_flag) {

    RESULT result = { 0 };
    for (int i = 0; i < n_targets; i++) {
        if (targets[i] > max_flag) {
            result.Ok = false;
            return result;
        }

        RESULT current_flag = _flag_from_position(targets[i], max_flag);
        result = _set_flag(result.bit_flag, current_flag.bit_flag, max_flag);

        if (result.Ok == false) {
            return result;
        }
    }

    result.Ok = true;
    return result;
}

#undef B
#undef BSET
#undef BFLAG_STUB
#undef FN_BFLAG
#undef RESULT
#undef FLAG_IN_RANGE
#undef POSITION_IN_RANGE
#undef _flag_from_position
#undef _set_flag
#undef _set_position
#undef _unset_flag
#undef _unset_position
#undef _contains
