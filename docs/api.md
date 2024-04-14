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

#### :::tangy.RecordsStandard
    options:
        show_root_heading: true
        show_source: false

#### :::tangy.RecordsClocked
    options:
        show_root_heading: true
        show_source: false

### :::tangy.TagBuffer
    options:
        show_root_heading: true
        show_source: false

## Measurements
### :::tangy.timetrace
    options:
        show_root_heading: true
        show_source: false

### :::tangy.find_zero_delay
    options:
        show_root_heading: true
        show_source: false

### :::tangy.singles
    options:
        show_root_heading: true
        show_source: false

### :::tangy.Coincidences
    options:
        show_root_heading: true
        show_source: false

### :::tangy.JointDelayHistogram
    options:
        show_root_heading: true
        show_source: false

## File Readers
### :::tangy.PTUFile
    options:
        members:
            - records
            - read
            - read_seconds
        show_root_heading: true
        show_source: false
