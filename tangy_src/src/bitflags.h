#define B u64
#define BSET u64
#include "bitflags_tmpl.h"
/* Including this header will add the following types and functions
 *
 *  bf_u64_Result struct {
 *      bool Ok;
 *      u64 bit_flag;
 *  };
 *
 * bf_u64_Result bf_u64_flag_from_position(u8 position, int max_flag);
 *
 * bf_u64_Result bf_u64_set(u64 bit_flag, u64 target, u64 max_flag);
 *
 * bf_u64_Result bf_u64_set_position(u64 bit_flag, u8 position, u64 max_flag);
 *
 * bf_u64_Result bf_u64_unset(u64 bit_flag, u64 target, u64 max_flag);
 *
 * bf_u64_Result bf_u64_unset_position(u64 bit_flag,
 *                                     u8 position,
 *                                     u64 max_flag);
 *
 * bool bf_u64_contains(u64 bit_flag, u64 target, u64 max_flag);
 *
 * bf_u64_Result bf_u64_extract(u64 bit_flag, u64 num_flags, u64* collection);
 *
 * bf_u64_Result bf_u64_extract_positions(u64 bit_flag,
 *                                        u64 max_flag,
 *                                        u8* collection);
 *
 * bf_u64_Result bf_u64_collect(const u64* const targets,
 *                              const u64 n_targets,
 *                              u64 max_flag);
 *
 * bf_u64_Result bf_u64_collect_positions(const u8* const targets,
 *                                        const u64 n_targets,
 *                                        u64 max_flag);
 */


