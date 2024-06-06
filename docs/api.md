# API Reference

## Buffers

### Timetag Formats
!!! example "Timetag Formats"
    === "Standard"
        ```c
        // Timetag format
        typedef struct std {
            u8 channel;
            u64 timestamp;
        } timetag_standard;

        typedef f64 resolution_standard;
        ```

    === "Clocked"
        ```c
        typedef struct timestamp_clocked {
            u64 clock;
            u64 delta;
        } timestamp_clocked;

        // Timetag format
        typedef struct timetag_clocked {
            u8 channel;
            timestamp_clocked timestamp;
        } timetag_clocked;

        typedef struct resolution_clocked {
            f64 coarse;
            f64 fine;
        } resolution_clocked;
        ```

### :::tangy.Records
    options:
        allow_inspection: false
        show_root_heading: true
        show_source: false

### :::tangy.TangyBufferType
    options:
        allow_inspection: true
        show_root_heading: true
        show_source: false


### :::tangy.TangyBuffer
    options:
        allow_inspection: true
        show_root_heading: true
        show_source: false

## Buffer Management

### :::tangy.buffer_list_update
    options:
        allow_inspection: true
        show_symbol_type_heading: true
        show_root_heading: true
        show_source: false

### :::tangy.buffer_list_append
    options:
        allow_inspection: true
        show_symbol_type_heading: true
        show_root_heading: true
        show_source: false

### :::tangy.buffer_list_delete_all
    options:
        allow_inspection: true
        show_symbol_type_heading: true
        show_root_heading: true
        show_source: false

### :::tangy.buffer_list_show
    options:
        allow_inspection: true
        show_symbol_type_heading: true
        show_root_heading: true
        show_source: false

## File Readers
### :::tangy.PTUFile
    options:
        show_symbol_type_heading: true
        members:
            - records
            - read
            - read_seconds
        show_root_heading: true
        show_source: false

## Devices
### :::tangy._uqd.UQDLogic16
    options:
        show_symbol_type_heading: true
        show_root_heading: true
        show_source: false
        members:
            - is_open
            - calibrate
            - led_brightness
            - fpga_version
            - resolution
            - number_of_channels
            - input_threshold
            - inversion
            - input_delay
            - function_generator
            - external_10MHz_reference
            - start_timetags
            - stop_timetags
            - read_tags
            - filter_min_count
            - filter_max_time
            - exclusion
            - level_gate
            - time_gating
            - time_gate_width
            - buffer
            - write_to_buffer

