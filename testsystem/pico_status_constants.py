#
# Copyright 2023 EAS Group
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this 
# software and associated documentation files (the “Software”), to deal in the Software 
# without restriction, including without limitation the rights to use, copy, modify, 
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to the following 
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies 
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

# Copied and modified from PicoStatus.h (part of PicoSDK)

PICO_ERROR_CODES = {
    0: ("PICO_OK", "The PicoScope is functioning correctly."),
    1: (
        "PICO_MAX_UNITS_OPENED",
        "An attempt has been made to open more than <API>_MAX_UNITS.",
    ),
    2: (
        "PICO_MEMORY_FAIL",
        "Not enough memory could be allocated on the host machine.",
    ),
    3: ("PICO_NOT_FOUND", "No Pico Technology device could be found."),
    4: ("PICO_FW_FAIL", "Unable to download firmware."),
    5: ("PICO_OPEN_OPERATION_IN_PROGRESS", "The driver is busy opening a device."),
    6: ("PICO_OPERATION_FAILED", "An unspecified failure occurred."),
    7: (
        "PICO_NOT_RESPONDING",
        "The PicoScope is not responding to commands from the PC.",
    ),
    8: (
        "PICO_CONFIG_FAIL",
        "The configuration information in the PicoScope is corrupt or missing.",
    ),
    9: (
        "PICO_KERNEL_DRIVER_TOO_OLD",
        "The picopp.sys file is too old to be used with the device driver.",
    ),
    10: (
        "PICO_EEPROM_CORRUPT",
        "The EEPROM has become corrupt, so the device will use a default setting.",
    ),
    11: (
        "PICO_OS_NOT_SUPPORTED",
        "The operating system on the PC is not supported by this driver.",
    ),
    12: ("PICO_INVALID_HANDLE", "There is no device with the handle value passed."),
    13: ("PICO_INVALID_PARAMETER", "A parameter value is not valid."),
    14: ("PICO_INVALID_TIMEBASE", "The timebase is not supported or is invalid."),
    15: (
        "PICO_INVALID_VOLTAGE_RANGE",
        "The voltage range is not supported or is invalid.",
    ),
    16: (
        "PICO_INVALID_CHANNEL",
        "The channel number is not valid on this device or no channels have been set.",
    ),
    17: (
        "PICO_INVALID_TRIGGER_CHANNEL",
        "The channel set for a trigger is not available on this device.",
    ),
    18: (
        "PICO_INVALID_CONDITION_CHANNEL",
        "The channel set for a condition is not available on this device.",
    ),
    19: ("PICO_NO_SIGNAL_GENERATOR", "The device does not have a signal generator."),
    20: (
        "PICO_STREAMING_FAILED",
        "Streaming has failed to start or has stopped without user request.",
    ),
    21: (
        "PICO_BLOCK_MODE_FAILED",
        "Block failed to start - a parameter may have been set wrongly.",
    ),
    22: ("PICO_NULL_PARAMETER", "A parameter that was required is NULL."),
    23: (
        "PICO_ETS_MODE_SET",
        "The current functionality is not available while using ETS capture mode.",
    ),
    24: ("PICO_DATA_NOT_AVAILABLE", "No data is available from a run block call."),
    25: (
        "PICO_STRING_BUFFER_TO_SMALL",
        "The buffer passed for the information was too small.",
    ),
    26: ("PICO_ETS_NOT_SUPPORTED", "ETS is not supported on this device."),
    27: (
        "PICO_AUTO_TRIGGER_TIME_TO_SHORT",
        (
            "The auto trigger time is less than the time it will take to collect the"
            " pre-trigger data."
        ),
    ),
    28: (
        "PICO_BUFFER_STALL",
        "The collection of data has stalled as unread data would be overwritten.",
    ),
    29: (
        "PICO_TOO_MANY_SAMPLES",
        (
            "Number of samples requested is more than available in the current memory"
            " segment."
        ),
    ),
    30: (
        "PICO_TOO_MANY_SEGMENTS",
        "Not possible to create number of segments requested.",
    ),
    31: (
        "PICO_PULSE_WIDTH_QUALIFIER",
        (
            "A null pointer has been passed in the trigger function or one of the"
            " parameters is out of range."
        ),
    ),
    32: ("PICO_DELAY", "One or more of the hold-off parameters are out of range."),
    33: ("PICO_SOURCE_DETAILS", "One or more of the source details are incorrect."),
    34: ("PICO_CONDITIONS", "One or more of the conditions are incorrect."),
    35: (
        "PICO_USER_CALLBACK",
        (
            "The driver's thread is currently in the <API>Ready callback function and"
            " therefore the action cannot be carried out."
        ),
    ),
    36: (
        "PICO_DEVICE_SAMPLING",
        (
            "An attempt is being made to get stored data while streaming. Either stop"
            " streaming by calling <API>Stop, or use <API>GetStreamingLatestValues."
        ),
    ),
    37: (
        "PICO_NO_SAMPLES_AVAILABLE",
        "Data is unavailable because a run has not been completed.",
    ),
    38: ("PICO_SEGMENT_OUT_OF_RANGE", "The memory segment index is out of range."),
    39: ("PICO_BUSY", "The device is busy so data cannot be returned yet."),
    40: (
        "PICO_STARTINDEX_INVALID",
        "The start time to get stored data is out of range.",
    ),
    41: (
        "PICO_INVALID_INFO",
        "The information number requested is not a valid number.",
    ),
    42: (
        "PICO_INFO_UNAVAILABLE",
        (
            "The handle is invalid so no information is available about the device."
            " Only PICO_DRIVER_VERSION is available."
        ),
    ),
    43: (
        "PICO_INVALID_SAMPLE_INTERVAL",
        "The sample interval selected for streaming is out of range.",
    ),
    44: (
        "PICO_TRIGGER_ERROR",
        (
            "ETS is set but no trigger has been set. A trigger setting is required for"
            " ETS."
        ),
    ),
    45: ("PICO_MEMORY", "Driver cannot allocate memory."),
    46: ("PICO_SIG_GEN_PARAM", "Incorrect parameter passed to the signal generator."),
    47: (
        "PICO_SHOTS_SWEEPS_WARNING",
        (
            "Conflict between the shots and sweeps parameters sent to the signal"
            " generator."
        ),
    ),
    48: (
        "PICO_SIGGEN_TRIGGER_SOURCE",
        (
            "A software trigger has been sent but the trigger source is not a software"
            " trigger."
        ),
    ),
    49: (
        "PICO_AUX_OUTPUT_CONFLICT",
        (
            "An <API>SetTrigger call has found a conflict between the trigger source"
            " and the AUX output enable."
        ),
    ),
    50: (
        "PICO_AUX_OUTPUT_ETS_CONFLICT",
        "ETS mode is being used and AUX is set as an input.",
    ),
    51: (
        "PICO_WARNING_EXT_THRESHOLD_CONFLICT",
        (
            "Attempt to set different EXT input thresholds set for signal generator and"
            " oscilloscope trigger."
        ),
    ),
    52: (
        "PICO_WARNING_AUX_OUTPUT_CONFLICT",
        (
            "An <API>SetTrigger... function has set AUX as an output and the signal"
            " generator is using it as a trigger."
        ),
    ),
    53: (
        "PICO_SIGGEN_OUTPUT_OVER_VOLTAGE",
        (
            "The combined peak to peak voltage and the analog offset voltage exceed the"
            " maximum voltage the signal generator can produce."
        ),
    ),
    54: ("PICO_DELAY_NULL", "NULL pointer passed as delay parameter."),
    55: (
        "PICO_INVALID_BUFFER",
        "The buffers for overview data have not been set while streaming.",
    ),
    56: ("PICO_SIGGEN_OFFSET_VOLTAGE", "The analog offset voltage is out of range."),
    57: ("PICO_SIGGEN_PK_TO_PK", "The analog peak-to-peak voltage is out of range."),
    58: ("PICO_CANCELLED", "A block collection has been cancelled."),
    59: ("PICO_SEGMENT_NOT_USED", "The segment index is not currently being used."),
    60: (
        "PICO_INVALID_CALL",
        "The wrong GetValues function has been called for the collection mode in use.",
    ),
    61: ("PICO_GET_VALUES_INTERRUPTED", ""),
    63: ("PICO_NOT_USED", "The function is not available."),
    64: (
        "PICO_INVALID_SAMPLERATIO",
        "The aggregation ratio requested is out of range.",
    ),
    65: ("PICO_INVALID_STATE", "Device is in an invalid state."),
    66: (
        "PICO_NOT_ENOUGH_SEGMENTS",
        (
            "The number of segments allocated is fewer than the number of captures"
            " requested."
        ),
    ),
    67: (
        "PICO_DRIVER_FUNCTION",
        (
            "A driver function has already been called and not yet finished. Only one"
            " call to the driver can be made at any one time."
        ),
    ),
    68: ("PICO_RESERVED", "Not used"),
    69: (
        "PICO_INVALID_COUPLING",
        "An invalid coupling type was specified in <API>SetChannel.",
    ),
    70: (
        "PICO_BUFFERS_NOT_SET",
        "An attempt was made to get data before a data buffer was defined.",
    ),
    71: (
        "PICO_RATIO_MODE_NOT_SUPPORTED",
        "The selected downsampling mode (used for data reduction) is not allowed.",
    ),
    72: (
        "PICO_RAPID_NOT_SUPPORT_AGGREGATION",
        "Aggregation was requested in rapid block mode.",
    ),
    73: (
        "PICO_INVALID_TRIGGER_PROPERTY",
        "An invalid parameter was passed to <API>SetTriggerChannelProperties.",
    ),
    74: (
        "PICO_INTERFACE_NOT_CONNECTED",
        "The driver was unable to contact the oscilloscope.",
    ),
    75: (
        "PICO_RESISTANCE_AND_PROBE_NOT_ALLOWED",
        (
            "Resistance-measuring mode is not allowed in conjunction with the specified"
            " probe."
        ),
    ),
    76: ("PICO_POWER_FAILED", "The device was unexpectedly powered down."),
    77: (
        "PICO_SIGGEN_WAVEFORM_SETUP_FAILED",
        "A problem occurred in <API>SetSigGenBuiltIn or <API>SetSigGenArbitrary.",
    ),
    78: ("PICO_FPGA_FAIL", "FPGA not successfully set up."),
    79: ("PICO_POWER_MANAGER", ""),
    80: (
        "PICO_INVALID_ANALOGUE_OFFSET",
        "An impossible analog offset value was specified in <API>SetChannel.",
    ),
    81: ("PICO_PLL_LOCK_FAILED", "There is an error within the device hardware."),
    82: ("PICO_ANALOG_BOARD", "There is an error within the device hardware."),
    83: ("PICO_CONFIG_FAIL_AWG", "Unable to configure the signal generator."),
    84: (
        "PICO_INITIALISE_FPGA",
        "The FPGA cannot be initialized, so unit cannot be opened.",
    ),
    86: (
        "PICO_EXTERNAL_FREQUENCY_INVALID",
        "The frequency for the external clock is not within 15% of the nominal value.",
    ),
    87: ("PICO_CLOCK_CHANGE_ERROR", "The FPGA could not lock the clock signal."),
    88: (
        "PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH",
        (
            "You are trying to configure the AUX input as both a trigger and a"
            " reference clock."
        ),
    ),
    89: (
        "PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH",
        (
            "You are trying to configure the AUX input as both a pulse width qualifier"
            " and a reference clock."
        ),
    ),
    90: (
        "PICO_UNABLE_TO_OPEN_SCALING_FILE",
        "The requested scaling file cannot be opened.",
    ),
    91: (
        "PICO_MEMORY_CLOCK_FREQUENCY",
        "The frequency of the memory is reporting incorrectly.",
    ),
    92: (
        "PICO_I2C_NOT_RESPONDING",
        "The I2C that is being actioned is not responding to requests.",
    ),
    93: (
        "PICO_NO_CAPTURES_AVAILABLE",
        "There are no captures available and therefore no data can be returned.",
    ),
    95: (
        "PICO_TOO_MANY_TRIGGER_CHANNELS_IN_USE",
        (
            "The number of trigger channels is greater than 4, except for a PS4824"
            " where 8 channels are allowed for rising/falling/rising_or_falling trigger"
            " directions."
        ),
    ),
    96: (
        "PICO_INVALID_TRIGGER_DIRECTION",
        (
            "When more than 4 trigger channels are set on a PS4824 and the direction is"
            " out of range."
        ),
    ),
    97: (
        "PICO_INVALID_TRIGGER_STATES",
        (
            "When more than 4 trigger channels are set and their trigger condition"
            " states are not <API>_CONDITION_TRUE."
        ),
    ),
    94: (
        "PICO_NOT_USED_IN_THIS_CAPTURE_MODE",
        (
            "The capture mode the device is currently running in does not support the"
            " current request."
        ),
    ),
    259: ("PICO_GET_DATA_ACTIVE", ""),
    260: (
        "PICO_IP_NETWORKED",
        (
            "The device is currently connected via the IP Network socket and thus the"
            " call made is not supported."
        ),
    ),
    261: (
        "PICO_INVALID_IP_ADDRESS",
        "An incorrect IP address has been passed to the driver.",
    ),
    262: ("PICO_IPSOCKET_FAILED", "The IP socket has failed."),
    263: ("PICO_IPSOCKET_TIMEDOUT", "The IP socket has timed out."),
    264: ("PICO_SETTINGS_FAILED", "Failed to apply the requested settings."),
    265: ("PICO_NETWORK_FAILED", "The network connection has failed."),
    266: ("PICO_WS2_32_DLL_NOT_LOADED", "Unable to load the WS2 DLL."),
    267: ("PICO_INVALID_IP_PORT", "The specified IP port is invalid."),
    268: (
        "PICO_COUPLING_NOT_SUPPORTED",
        "The type of coupling requested is not supported on the opened device.",
    ),
    269: (
        "PICO_BANDWIDTH_NOT_SUPPORTED",
        "Bandwidth limiting is not supported on the opened device.",
    ),
    270: (
        "PICO_INVALID_BANDWIDTH",
        "The value requested for the bandwidth limit is out of range.",
    ),
    271: (
        "PICO_AWG_NOT_SUPPORTED",
        "The arbitrary waveform generator is not supported by the opened device.",
    ),
    272: (
        "PICO_ETS_NOT_RUNNING",
        (
            "Data has been requested with ETS mode set but run block has not been"
            " called, or stop has been called."
        ),
    ),
    273: (
        "PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED",
        "White noise output is not supported on the opened device.",
    ),
    274: (
        "PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED",
        "The wave type requested is not supported by the opened device.",
    ),
    275: (
        "PICO_INVALID_DIGITAL_PORT",
        "The requested digital port number is out of range (MSOs only).",
    ),
    276: (
        "PICO_INVALID_DIGITAL_CHANNEL",
        (
            "The digital channel is not in the range <API>_DIGITAL_CHANNEL0 to"
            " <API>_DIGITAL_CHANNEL15, the digital channels that are supported."
        ),
    ),
    277: (
        "PICO_INVALID_DIGITAL_TRIGGER_DIRECTION",
        (
            "The digital trigger direction is not a valid trigger direction and should"
            " be equal in value to one of the <API>_DIGITAL_DIRECTION enumerations."
        ),
    ),
    278: (
        "PICO_SIG_GEN_PRBS_NOT_SUPPORTED",
        "Signal generator does not generate pseudo-random binary sequence.",
    ),
    279: (
        "PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS",
        "When a digital port is enabled, ETS sample mode is not available for use.",
    ),
    280: (
        "PICO_WARNING_REPEAT_VALUE",
        (
            "There has been no new sample taken, this value has already been returned"
            " previously"
        ),
    ),
    281: (
        "PICO_POWER_SUPPLY_CONNECTED",
        "4-channel scopes only: The DC power supply is connected.",
    ),
    282: (
        "PICO_POWER_SUPPLY_NOT_CONNECTED",
        "4-channel scopes only: The DC power supply is not connected.",
    ),
    283: (
        "PICO_POWER_SUPPLY_REQUEST_INVALID",
        "Incorrect power mode passed for current power source.",
    ),
    284: (
        "PICO_POWER_SUPPLY_UNDERVOLTAGE",
        "The supply voltage from the USB source is too low.",
    ),
    285: (
        "PICO_CAPTURING_DATA",
        "The oscilloscope is in the process of capturing data.",
    ),
    286: (
        "PICO_USB3_0_DEVICE_NON_USB3_0_PORT",
        "A USB 3.0 device is connected to a non-USB 3.0 port.",
    ),
    287: (
        "PICO_NOT_SUPPORTED_BY_THIS_DEVICE",
        "A function has been called that is not supported by the current device.",
    ),
    288: (
        "PICO_INVALID_DEVICE_RESOLUTION",
        "The device resolution is invalid (out of range).",
    ),
    289: (
        "PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION",
        (
            "The number of channels that can be enabled is limited in 15 and 16-bit"
            " modes. (Flexible Resolution Oscilloscopes only)"
        ),
    ),
    290: (
        "PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED",
        "USB power not sufficient for all requested channels.",
    ),
    291: (
        "PICO_SIGGEN_DC_VOLTAGE_NOT_CONFIGURABLE",
        "The signal generator does not have a configurable DC offset.",
    ),
    292: (
        "PICO_NO_TRIGGER_ENABLED_FOR_TRIGGER_IN_PRE_TRIG",
        (
            "An attempt has been made to define pre-trigger delay without first"
            " enabling a trigger."
        ),
    ),
    293: (
        "PICO_TRIGGER_WITHIN_PRE_TRIG_NOT_ARMED",
        (
            "An attempt has been made to define pre-trigger delay without first arming"
            " a trigger."
        ),
    ),
    294: (
        "PICO_TRIGGER_WITHIN_PRE_NOT_ALLOWED_WITH_DELAY",
        "Pre-trigger delay and post-trigger delay cannot be used at the same time.",
    ),
    295: (
        "PICO_TRIGGER_INDEX_UNAVAILABLE",
        "The array index points to a nonexistent trigger.",
    ),
    296: ("PICO_AWG_CLOCK_FREQUENCY", ""),
    297: (
        "PICO_TOO_MANY_CHANNELS_IN_USE",
        "There are more 4 analog channels with a trigger condition set.",
    ),
    298: ("PICO_NULL_CONDITIONS", "The condition parameter is a null pointer."),
    299: (
        "PICO_DUPLICATE_CONDITION_SOURCE",
        "There is more than one condition pertaining to the same channel.",
    ),
    300: (
        "PICO_INVALID_CONDITION_INFO",
        "The parameter relating to condition information is out of range.",
    ),
    301: ("PICO_SETTINGS_READ_FAILED", "Reading the meta data has failed."),
    302: ("PICO_SETTINGS_WRITE_FAILED", "Writing the meta data has failed."),
    303: (
        "PICO_ARGUMENT_OUT_OF_RANGE",
        "A parameter has a value out of the expected range.",
    ),
    304: (
        "PICO_HARDWARE_VERSION_NOT_SUPPORTED",
        "The driver does not support the hardware variant connected.",
    ),
    305: (
        "PICO_DIGITAL_HARDWARE_VERSION_NOT_SUPPORTED",
        "The driver does not support the digital hardware variant connected.",
    ),
    306: (
        "PICO_ANALOGUE_HARDWARE_VERSION_NOT_SUPPORTED",
        "The driver does not support the analog hardware variant connected.",
    ),
    307: (
        "PICO_UNABLE_TO_CONVERT_TO_RESISTANCE",
        "Converting a channel's ADC value to resistance has failed.",
    ),
    308: (
        "PICO_DUPLICATED_CHANNEL",
        "The channel is listed more than once in the function call.",
    ),
    309: (
        "PICO_INVALID_RESISTANCE_CONVERSION",
        "The range cannot have resistance conversion applied.",
    ),
    310: ("PICO_INVALID_VALUE_IN_MAX_BUFFER", "An invalid value is in the max buffer."),
    311: ("PICO_INVALID_VALUE_IN_MIN_BUFFER", "An invalid value is in the min buffer."),
    312: (
        "PICO_SIGGEN_FREQUENCY_OUT_OF_RANGE",
        (
            "When calculating the frequency for phase conversion, the frequency is"
            " greater than that supported by the current variant."
        ),
    ),
    313: (
        "PICO_EEPROM2_CORRUPT",
        (
            "The device's EEPROM is corrupt. Contact Pico Technology support:"
            " https://www.picotech.com/tech-support."
        ),
    ),
    314: ("PICO_EEPROM2_FAIL", "The EEPROM has failed."),
    315: (
        "PICO_SERIAL_BUFFER_TOO_SMALL",
        "The serial buffer is too small for the required information.",
    ),
    316: (
        "PICO_SIGGEN_TRIGGER_AND_EXTERNAL_CLOCK_CLASH",
        (
            "The signal generator trigger and the external clock have both been set."
            " This is not allowed."
        ),
    ),
    317: (
        "PICO_WARNING_SIGGEN_AUXIO_TRIGGER_DISABLED",
        (
            "The AUX trigger was enabled and the external clock has been enabled, so"
            " the AUX has been automatically disabled."
        ),
    ),
    318: (
        "PICO_SIGGEN_GATING_AUXIO_NOT_AVAILABLE",
        (
            "The AUX I/O was set as a scope trigger and is now being set as a signal"
            " generator gating trigger. This is not allowed."
        ),
    ),
    319: (
        "PICO_SIGGEN_GATING_AUXIO_ENABLED",
        (
            "The AUX I/O was set by the signal generator as a gating trigger and is now"
            " being set as a scope trigger. This is not allowed."
        ),
    ),
    320: ("PICO_RESOURCE_ERROR", "A resource has failed to initialise"),
    321: ("PICO_TEMPERATURE_TYPE_INVALID", "The temperature type is out of range"),
    322: (
        "PICO_TEMPERATURE_TYPE_NOT_SUPPORTED",
        "A requested temperature type is not supported on this device",
    ),
    323: ("PICO_TIMEOUT", "A read/write to the device has timed out"),
    324: ("PICO_DEVICE_NOT_FUNCTIONING", "The device cannot be connected correctly"),
    325: (
        "PICO_INTERNAL_ERROR",
        (
            "The driver has experienced an unknown error and is unable to recover from"
            " this error"
        ),
    ),
    326: (
        "PICO_MULTIPLE_DEVICES_FOUND",
        (
            "Used when opening units via IP and more than multiple units have the same"
            " IP address"
        ),
    ),
    327: ("PICO_WARNING_NUMBER_OF_SEGMENTS_REDUCED", ""),
    328: (
        "PICO_CAL_PINS_STATES",
        "the calibration pin states argument is out of range",
    ),
    329: (
        "PICO_CAL_PINS_FREQUENCY",
        "the calibration pin frequency argument is out of range",
    ),
    330: (
        "PICO_CAL_PINS_AMPLITUDE",
        "the calibration pin amplitude argument is out of range",
    ),
    331: (
        "PICO_CAL_PINS_WAVETYPE",
        "the calibration pin wavetype argument is out of range",
    ),
    332: (
        "PICO_CAL_PINS_OFFSET",
        "the calibration pin offset argument is out of range",
    ),
    333: ("PICO_PROBE_FAULT", "the probe's identity has a problem"),
    334: ("PICO_PROBE_IDENTITY_UNKNOWN", "the probe has not been identified"),
    335: (
        "PICO_PROBE_POWER_DC_POWER_SUPPLY_REQUIRED",
        (
            "enabling the probe would cause the device to exceed the allowable current"
            " limit"
        ),
    ),
    336: (
        "PICO_PROBE_NOT_POWERED_WITH_DC_POWER_SUPPLY",
        (
            "The DC power supply is connected; enabling the probe would cause the"
            " device to exceed the allowable current limit."
        ),
    ),
    337: ("PICO_PROBE_CONFIG_FAILURE", "failed to complete probe configuration"),
    338: (
        "PICO_PROBE_INTERACTION_CALLBACK",
        (
            "failed to set the callback function, as currently in current callback"
            " function"
        ),
    ),
    339: (
        "PICO_UNKNOWN_INTELLIGENT_PROBE",
        "the probe has been verified but not known on this driver",
    ),
    340: ("PICO_INTELLIGENT_PROBE_CORRUPT", "the intelligent probe cannot be verified"),
    341: (
        "PICO_PROBE_COLLECTION_NOT_STARTED",
        (
            "The callback is null, probe collection will only start when first callback"
            " is a none null pointer."
        ),
    ),
    342: (
        "PICO_PROBE_POWER_CONSUMPTION_EXCEEDED",
        "The current drawn by the probe(s) has exceeded the allowed limit.",
    ),
    343: (
        "PICO_WARNING_PROBE_CHANNEL_OUT_OF_SYNC",
        (
            "The channel range limits have changed due to connecting or disconnecting a"
            " probe the channel has been enabled"
        ),
    ),
    344: ("PICO_ENDPOINT_MISSING", ""),
    345: ("PICO_UNKNOWN_ENDPOINT_REQUEST", ""),
    346: (
        "PICO_ADC_TYPE_ERROR",
        "The ADC on board the device has not been correctly identified",
    ),
    347: ("PICO_FPGA2_FAILED", ""),
    348: ("PICO_FPGA2_DEVICE_STATUS", ""),
    349: ("PICO_ENABLE_PROGRAM_FPGA2_FAILED", ""),
    350: ("PICO_NO_CHANNELS_OR_PORTS_ENABLED", ""),
    351: ("PICO_INVALID_RATIO_MODE", ""),
    352: ("PICO_READS_NOT_SUPPORTED_IN_CURRENT_CAPTURE_MODE", ""),
    353: (
        "PICO_READ1_SELECTION_CHECK_FAILED",
        (
            "These selection tests can be masked together to show that mode than one"
            " read selection has failed the tests, therefore theses error codes cover"
            " 0x00000161UL to 0x0000016FUL."
        ),
    ),
    354: (
        "PICO_READ2_SELECTION_CHECK_FAILED",
        (
            "These selection tests can be masked together to show that mode than one"
            " read selection has failed the tests, therefore theses error codes cover"
            " 0x00000161UL to 0x0000016FUL."
        ),
    ),
    356: (
        "PICO_READ3_SELECTION_CHECK_FAILED",
        (
            "These selection tests can be masked together to show that mode than one"
            " read selection has failed the tests, therefore theses error codes cover"
            " 0x00000161UL to 0x0000016FUL."
        ),
    ),
    360: (
        "PICO_READ4_SELECTION_CHECK_FAILED",
        (
            "These selection tests can be masked together to show that mode than one"
            " read selection has failed the tests, therefore theses error codes cover"
            " 0x00000161UL to 0x0000016FUL."
        ),
    ),
    368: (
        "PICO_READ_SELECTION_OUT_OF_RANGE",
        "The requested read is not one of the reads available in enPicoReadSelection.",
    ),
    369: (
        "PICO_MULTIPLE_RATIO_MODES",
        "The downsample ratio options cannot be combined together for this request.",
    ),
    370: (
        "PICO_NO_SAMPLES_READ",
        "The enPicoReadSelection request has no samples available.",
    ),
    371: (
        "PICO_RATIO_MODE_NOT_REQUESTED",
        (
            "The enPicoReadSelection did not include one of the downsample ratios now"
            " requested."
        ),
    ),
    372: ("PICO_NO_USER_READ_REQUESTS_SET", "No read requests have been made."),
    373: (
        "PICO_ZERO_SAMPLES_INVALID",
        "The parameter for <number of values> cannot be zero.",
    ),
    374: (
        "PICO_ANALOGUE_HARDWARE_MISSING",
        (
            "The analogue hardware cannot be identified; contact Pico Technology"
            " Technical Support."
        ),
    ),
    375: (
        "PICO_ANALOGUE_HARDWARE_PINS",
        "Setting of the analogue hardware pins failed.",
    ),
    376: ("PICO_ANALOGUE_HARDWARE_SMPS_FAULT", "An SMPS fault has occurred."),
    377: (
        "PICO_DIGITAL_ANALOGUE_HARDWARE_CONFLICT",
        (
            "There appears to be a conflict between the expected and actual hardware in"
            " the device; contact Pico Technology Technical Support."
        ),
    ),
    378: (
        "PICO_RATIO_MODE_BUFFER_NOT_SET",
        "One or more of the enPicoRatioMode requested do not have a data buffer set.",
    ),
    379: (
        "PICO_RESOLUTION_NOT_SUPPORTED_BY_VARIANT",
        "The resolution is valid but not supported by the opened device.",
    ),
    380: (
        "PICO_THRESHOLD_OUT_OF_RANGE",
        (
            "The requested trigger threshold is out of range for the current device"
            " resolution"
        ),
    ),
    381: (
        "PICO_INVALID_SIMPLE_TRIGGER_DIRECTION",
        "The simple trigger only supports upper edge direction options",
    ),
    382: ("PICO_AUX_NOT_SUPPORTED", "The aux trigger is not supported on this variant"),
    383: ("PICO_NULL_DIRECTIONS", "The trigger directions pointer may not be null"),
    384: (
        "PICO_NULL_CHANNEL_PROPERTIES",
        "The trigger channel properties pointer may not be null",
    ),
    385: (
        "PICO_TRIGGER_CHANNEL_NOT_ENABLED",
        "A trigger is set on a channel that has not been enabled",
    ),
    386: (
        "PICO_CONDITION_HAS_NO_TRIGGER_PROPERTY",
        "A trigger condition has been set but a trigger property not set",
    ),
    387: (
        "PICO_RATIO_MODE_TRIGGER_MASKING_INVALID",
        (
            "When requesting trigger data, this option can only be combined with the"
            " segment header ratio mode flag"
        ),
    ),
    388: (
        "PICO_TRIGGER_DATA_REQUIRES_MIN_BUFFER_SIZE_OF_40_SAMPLES",
        "The trigger data buffer must be 40 or more samples in size",
    ),
    389: (
        "PICO_NO_OF_CAPTURES_OUT_OF_RANGE",
        (
            "The number of requested waveforms is greater than the number of memory"
            " segments allocated"
        ),
    ),
    390: (
        "PICO_RATIO_MODE_SEGMENT_HEADER_DOES_NOT_REQUIRE_BUFFERS",
        (
            "When requesting segment header information, the segment header does not"
            " require a data buffer, to get the segment information use GetTriggerInfo"
        ),
    ),
    391: (
        "PICO_FOR_SEGMENT_HEADER_USE_GETTRIGGERINFO",
        "Use GetTriggerInfo to retrieve the segment header information",
    ),
    392: ("PICO_READ_NOT_SET", "A read request has not been set"),
    393: (
        "PICO_ADC_SETTING_MISMATCH",
        "The expected and actual states of the ADCs do not match",
    ),
    394: (
        "PICO_DATATYPE_INVALID",
        "The requested data type is not one of the enPicoDataType listed ",
    ),
    395: (
        "PICO_RATIO_MODE_DOES_NOT_SUPPORT_DATATYPE",
        (
            "The down sample ratio mode requested does not support the enPicoDataType"
            " option chosen"
        ),
    ),
    396: (
        "PICO_CHANNEL_COMBINATION_NOT_VALID_IN_THIS_RESOLUTION",
        "The channel combination is not valid for the resolution ",
    ),
    397: ("PICO_USE_8BIT_RESOLUTION", ""),
    398: (
        "PICO_AGGREGATE_BUFFERS_SAME_POINTER",
        (
            "The buffer for minimum data values and maximum data values are the same"
            " buffers"
        ),
    ),
    399: (
        "PICO_OVERLAPPED_READ_VALUES_OUT_OF_RANGE",
        (
            "The read request number of samples requested for an overlapped operation"
            " are more than the total number of samples to capture."
        ),
    ),
    400: (
        "PICO_OVERLAPPED_READ_SEGMENTS_OUT_OF_RANGE",
        (
            "The overlapped read request has more segments specified than segments"
            " allocated"
        ),
    ),
    401: (
        "PICO_CHANNELFLAGSCOMBINATIONS_ARRAY_SIZE_TOO_SMALL",
        (
            "The number of channel combinations available are greater than the array"
            " size received"
        ),
    ),
    402: (
        "PICO_CAPTURES_EXCEEDS_NO_OF_SUPPORTED_SEGMENTS",
        (
            "The number of captures is larger than the maximum number of segments"
            " allowed for the device variant"
        ),
    ),
    403: (
        "PICO_TIME_UNITS_OUT_OF_RANGE",
        "The time unit requested is not one of the listed enPicoTimeUnits",
    ),
    404: (
        "PICO_NO_SAMPLES_REQUESTED",
        "The number of samples parameter may not be zero",
    ),
    405: ("PICO_INVALID_ACTION", "The action requested is not listed in enPicoAction"),
    406: (
        "PICO_NO_OF_SAMPLES_NEED_TO_BE_EQUAL_WHEN_ADDING_BUFFERS",
        (
            "When adding buffers for the same read request the buffers for all ratio"
            " mode requests have to be the same size"
        ),
    ),
    407: (
        "PICO_WAITING_FOR_DATA_BUFFERS",
        (
            "The data is being processed but there is no empty data buffers available,"
            " a new data buffer needs to be set sent to the driver so that the data can"
            " be processed"
        ),
    ),
    408: (
        "PICO_STREAMING_ONLY_SUPPORTS_ONE_READ",
        "when streaming data, only one read option is available",
    ),
    409: (
        "PICO_CLEAR_DATA_BUFFER_INVALID",
        "A clear read request is not one of the enPicoAction listed",
    ),
    410: (
        "PICO_INVALID_ACTION_FLAGS_COMBINATION",
        "The combination of action flags are not allowed",
    ),
    411: (
        "PICO_BOTH_MIN_AND_MAX_NULL_BUFFERS_CANNOT_BE_ADDED",
        (
            " PICO_ADD request has been made but both data buffers are set to null and"
            " so there is nowhere to put the data."
        ),
    ),
    412: (
        "PICO_CONFLICT_IN_SET_DATA_BUFFERS_CALL_REMOVE_DATA_BUFFER_TO_RESET",
        (
            "A conflict between the data buffers being set has occurred. Please use the"
            " PICO_CLEAR_ALL action to reset "
        ),
    ),
    413: (
        "PICO_REMOVING_DATA_BUFFER_ENTRIES_NOT_ALLOWED_WHILE_DATA_PROCESSING",
        "While processing data,  buffers cannot be removed from the data buffers list",
    ),
    512: ("PICO_CYUSB_REQUEST_FAILED", " An USB request has failed"),
    513: (
        "PICO_STREAMING_DATA_REQUIRED",
        (
            "A request has been made to retrieve the latest streaming data, but with"
            " either a null pointer or an array size set to zero"
        ),
    ),
    514: (
        "PICO_INVALID_NUMBER_OF_SAMPLES",
        "A buffer being set has a length that is invalid (ie less than zero)",
    ),
    515: ("PICO_INVALID_DISTRIBUTION", "The distribution size may not be zero"),
    516: (
        "PICO_BUFFER_LENGTH_GREATER_THAN_INT32_T",
        "The buffer length in bytes is greater than a 4 byte word",
    ),
    521: ("PICO_PLL_MUX_OUT_FAILED", "The PLL has failed "),
    522: (
        "PICO_ONE_PULSE_WIDTH_DIRECTION_ALLOWED",
        "Pulse width only supports one direction",
    ),
    523: (
        "PICO_EXTERNAL_TRIGGER_NOT_SUPPORTED",
        "There is no external trigger available on the device specified by the handle",
    ),
    524: (
        "PICO_NO_TRIGGER_CONDITIONS_SET",
        "The condition parameter is a null pointer.",
    ),
    525: (
        "PICO_NO_OF_CHANNEL_TRIGGER_PROPERTIES_OUT_OF_RANGE",
        (
            "The number of trigger channel properties it outside the allowed range (is"
            " less than zero )"
        ),
    ),
    526: (
        "PICO_PROBE_COMPONENT_ERROR",
        "A probe has been plugged into a channel, but can not be identified correctly",
    ),
    528: (
        "PICO_INVALID_TRIGGER_CHANNEL_FOR_ETS",
        "The requested channel for ETS triggering is not supported",
    ),
    4096: (
        "PICO_INVALID_VARIANT",
        "The device variant is not supported by this current driver",
    ),
    4097: (
        "PICO_MEMORY_MODULE_ERROR",
        "The actual memory module does not match the expected memory module",
    ),
    8192: (
        "PICO_PULSE_WIDTH_QUALIFIER_LOWER_UPPER_CONFILCT",
        (
            "A null pointer has been passed in the trigger function or one of the"
            " parameters is out of range."
        ),
    ),
    8193: (
        "PICO_PULSE_WIDTH_QUALIFIER_TYPE",
        "The Pulse width qualifier type is not one of the listed options",
    ),
    8194: (
        "PICO_PULSE_WIDTH_QUALIFIER_DIRECTION",
        "The pulse width qualifier direction is not one of the listed options",
    ),
    8195: (
        "PICO_THRESHOLD_MODE_OUT_OF_RANGE",
        "The threshold range is not one of the listed options",
    ),
    8196: (
        "PICO_TRIGGER_AND_PULSEWIDTH_DIRECTION_IN_CONFLICT",
        "The trigger direction and pulse width option conflict with each other",
    ),
    8197: (
        "PICO_THRESHOLD_UPPER_LOWER_MISMATCH",
        (
            "The thresholds upper limits and thresholds lower limits conflict with each"
            " other"
        ),
    ),
    8198: (
        "PICO_PULSE_WIDTH_LOWER_OUT_OF_RANGE",
        "The pulse width lower count is out of range",
    ),
    8199: (
        "PICO_PULSE_WIDTH_UPPER_OUT_OF_RANGE",
        "The pulse width upper count is out of range",
    ),
    8200: ("PICO_FRONT_PANEL_ERROR", "The devices front panel has caused an error"),
    8201: (
        "PICO_FRONT_PANEL_SETUP_FAILED",
        "While trying to configure the device front panel, set up failed",
    ),
    8202: (
        "PICO_FRONT_PANEL_SECURITY_FAILED",
        "The front panel did not pass the security checks",
    ),
    8203: (
        "PICO_FRONT_PANEL_MODE",
        "The actual and expected mode of the front panel do not match",
    ),
    8204: (
        "PICO_FRONT_PANEL_FEATURE",
        "A front panel feature is not available or failed to configure",
    ),
    8205: (
        "PICO_NO_PULSE_WIDTH_CONDITIONS_SET",
        (
            "When setting the pulse width conditions either the pointer is null or the"
            " number of conditions is set to zero"
        ),
    ),
    12288: (
        "PICO_PROBE_VERSION_ERROR",
        "A probe has been connected, but the version is not recognised",
    ),
    12289: (
        "PICO_INVALID_PROBE_LED_POSITION",
        (
            "A probe LED position requested is not one of the available probe positions"
            " in ProbeLedPosition enum"
        ),
    ),
    12290: (
        "PICO_PROBE_LED_POSITION_NOT_SUPPORTED",
        "The led position is not supported by the selected variant",
    ),
    12291: (
        "PICO_DUPLICATE_PROBE_CHANNEL_LED_POSITION",
        (
            "A channel has more than one of the same led position in the"
            " ProbeChannelLedSetting struct"
        ),
    ),
    12292: ("PICO_PROBE_LED_FAILURE", "Setting the probes led has failed"),
    12293: (
        "PICO_PROBE_NOT_SUPPORTED_BY_THIS_DEVICE",
        "Probe is not supported by the selected variant",
    ),
    12294: (
        "PICO_INVALID_PROBE_NAME",
        "the probe name is not in the list of enPicoConnectProbe enums",
    ),
    12295: (
        "PICO_NO_PROBE_COLOUR_SETTINGS",
        (
            "the number of colour settings are zero or a null pointer passed to the"
            " function"
        ),
    ),
    16384: (
        "PICO_AUTO_TRIGGER_TIME_TOO_LONG",
        "the requested trigger time is to long for the selected variant",
    ),
    16777216: (
        "PICO_DEVICE_TIME_STAMP_RESET",
        "The time stamp per waveform segment has been reset.",
    ),
    33554433: (
        "PICO_TRIGGER_TIME_NOT_REQUESTED",
        "when requesting the TriggerTimeOffset the trigger time has not been set",
    ),
    33554434: ("PICO_TRIGGER_TIME_BUFFER_NOT_SET", "trigger time buffer not set"),
    33554436: (
        "PICO_TRIGGER_TIME_FAILED_TO_CALCULATE",
        "the trigger time failed to be calculated",
    ),
    33554688: (
        "PICO_TRIGGER_TIME_STAMP_NOT_REQUESTED",
        "the trigger time stamp was not requested",
    ),
    50331664: (
        "PICO_SIGGEN_SETTINGS_MISMATCH",
        "Attempted to set up the signal generator with an inconsistent configuration.",
    ),
    50331665: (
        "PICO_SIGGEN_SETTINGS_CHANGED_CALL_APPLY",
        (
            "The signal generator has been partially reconfigured and the new settings"
            " must be applied before it can be paused or restarted."
        ),
    ),
    50331666: (
        "PICO_SIGGEN_WAVETYPE_NOT_SUPPORTED",
        "The wave type is not listed in enPicoWaveType.",
    ),
    50331667: (
        "PICO_SIGGEN_TRIGGERTYPE_NOT_SUPPORTED",
        "The trigger type is not listed in enSigGenTrigType.",
    ),
    50331668: (
        "PICO_SIGGEN_TRIGGERSOURCE_NOT_SUPPORTED",
        "The trigger source is not listed in enSigGenTrigSource.",
    ),
    50331669: (
        "PICO_SIGGEN_FILTER_STATE_NOT_SUPPORTED",
        "The filter state is not listed in enPicoSigGenFilterState.",
    ),
    50331680: (
        "PICO_SIGGEN_NULL_PARAMETER",
        "the arbitrary waveform buffer is a null pointer",
    ),
    50331681: (
        "PICO_SIGGEN_EMPTY_BUFFER_SUPPLIED",
        "the arbitrary waveform buffer length is zero",
    ),
    50331682: (
        "PICO_SIGGEN_RANGE_NOT_SUPPLIED",
        "the sig gen voltage offset and peak to peak have not been set",
    ),
    50331683: (
        "PICO_SIGGEN_BUFFER_NOT_SUPPLIED",
        "the sig gen arbitrary waveform buffer not been set",
    ),
    50331684: (
        "PICO_SIGGEN_FREQUENCY_NOT_SUPPLIED",
        "the sig gen frequency have not been set",
    ),
    50331685: (
        "PICO_SIGGEN_SWEEP_INFO_NOT_SUPPLIED",
        "the sig gen sweep information has not been set",
    ),
    50331686: (
        "PICO_SIGGEN_TRIGGER_INFO_NOT_SUPPLIED",
        "the sig gen trigger information has not been set",
    ),
    50331687: (
        "PICO_SIGGEN_CLOCK_FREQ_NOT_SUPPLIED",
        "the sig gen clock frequency have not been set",
    ),
    50331696: (
        "PICO_SIGGEN_TOO_MANY_SAMPLES",
        "the sig gen arbitrary waveform buffer length is too long",
    ),
    50331697: (
        "PICO_SIGGEN_DUTYCYCLE_OUT_OF_RANGE",
        "the duty cycle value is out of range",
    ),
    50331698: (
        "PICO_SIGGEN_CYCLES_OUT_OF_RANGE",
        "the number of cycles is out of range",
    ),
    50331699: ("PICO_SIGGEN_PRESCALE_OUT_OF_RANGE", "the pre scaler is out of range"),
    50331700: (
        "PICO_SIGGEN_SWEEPTYPE_INVALID",
        "the sweep type is not listed in enPicoSweepType",
    ),
    50331701: (
        "PICO_SIGGEN_SWEEP_WAVETYPE_MISMATCH",
        "a mismatch has occurred while checking the sweeps wave type",
    ),
    50331702: (
        "PICO_SIGGEN_INVALID_SWEEP_PARAMETERS",
        "the sweeps or shots and trigger type are not valid when combined together",
    ),
    50331703: (
        "PICO_SIGGEN_SWEEP_PRESCALE_NOT_SUPPORTED",
        "the sweep and prescaler are not valid when combined together",
    ),
    50335744: (
        "PICO_PORTS_WITHOUT_ANALOGUE_CHANNELS_ONLY_ALLOWED_IN_8BIT_RESOLUTION",
        (
            "the digital ports without analogue channels are only allowed in 8bit"
            " resolution"
        ),
    ),
    268435456: (
        "PICO_WATCHDOGTIMER",
        "An internal error has occurred and a watchdog timer has been called.",
    ),
    268435457: ("PICO_IPP_NOT_FOUND", "The picoipp.dll has not been found."),
    268435458: (
        "PICO_IPP_NO_FUNCTION",
        "A function in the picoipp.dll does not exist.",
    ),
    268435459: ("PICO_IPP_ERROR", "The Pico IPP call has failed."),
    268435460: (
        "PICO_SHADOW_CAL_NOT_AVAILABLE",
        "Shadow calibration is not available on this device.",
    ),
    268435461: (
        "PICO_SHADOW_CAL_DISABLED",
        "Shadow calibration is currently disabled.",
    ),
    268435462: ("PICO_SHADOW_CAL_ERROR", "Shadow calibration error has occurred."),
    268435463: ("PICO_SHADOW_CAL_CORRUPT", "The shadow calibration is corrupt."),
    268435464: (
        "PICO_DEVICE_MEMORY_OVERFLOW",
        "the memory on board the device has overflowed",
    ),
    285212672: ("PICO_RESERVED_1", ""),
    536870912: (
        "PICO_SOURCE_NOT_READY",
        "the Pico source device is not ready to accept instructions",
    ),
    536870913: ("PICO_SOURCE_INVALID_BAUD_RATE", ""),
    536870914: ("PICO_SOURCE_NOT_OPENED_FOR_WRITE", ""),
    536870915: ("PICO_SOURCE_FAILED_TO_WRITE_DEVICE", ""),
    536870916: ("PICO_SOURCE_EEPROM_FAIL", ""),
    536870917: ("PICO_SOURCE_EEPROM_NOT_PRESENT", ""),
    536870918: ("PICO_SOURCE_EEPROM_NOT_PROGRAMMED", ""),
    536870919: ("PICO_SOURCE_LIST_NOT_READY", ""),
    536870920: ("PICO_SOURCE_FTD2XX_NOT_FOUND", ""),
    536870921: ("PICO_SOURCE_FTD2XX_NO_FUNCTION", ""),
}
