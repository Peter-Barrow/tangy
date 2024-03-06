#include "./picoquant_reader.h"



// tag_buffer* picoquant_reader(u64_t buffer_size){
//
//     tag_buffer* buffer;
//     buffer = create_tag_buffer(1, buffer_size);
//
//     return buffer;
// }

READER_STATUS *set_reader_status(u64 num_records) {

    READER_STATUS *reader_stat;
    reader_stat = (READER_STATUS *)malloc(sizeof(READER_STATUS));

    reader_stat->overflow = 0;
    reader_stat->total_records = num_records;
    reader_stat->record_count = 0;
    reader_stat->photon_count = 0;
    reader_stat->current_count = 0;

    return reader_stat;
}


