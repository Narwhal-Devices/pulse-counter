import struct

def decode_internal_error(message):
    ''' Messagein identifier:  1 byte: 200
    Message format:                     BITS USED   FPGA INDEX.
    tags:               1 byte  [0]     2 bits      [0+:2]      unsigned int.
        invalid_identifier_received     1 bit       [0]
        timeout_waiting_for_full_msg    1 bit       [1]  
        received_message_not_forwarded  1 bit       [2]  
    error information:  1 byte  [1]     8 bits      [8+:8]     unsigned int.

    The 'error_info' represents the "device_index" for the received message, which basically says where the meassage should have headed in the FPGA.
    '''
    tags, =         struct.unpack('<Q', message[0:1] + bytes(7))
    error_info, =   struct.unpack('<Q', message[1:2] + bytes(7))
    invalid_identifier_received_tag =       (tags >> 0) & 0b1        
    timeout_waiting_for_msg_tag =           (tags >> 1) & 0b1     
    received_message_not_forwarded_tag =    (tags >> 2) & 0b1 
    invalid_identifier_received =       decode_lookup['invalid_identifier'][invalid_identifier_received_tag]
    timeout_waiting_for_msg =           decode_lookup['msg_receive_timeout'][timeout_waiting_for_msg_tag]
    received_message_not_forwarded =    decode_lookup['msg_not_forwarded'][received_message_not_forwarded_tag]
    return {'invalid_identifier_received':invalid_identifier_received, 'timeout_waiting_to_receive_message':timeout_waiting_for_msg, 'received_message_not_forwarded':received_message_not_forwarded, 'error_info':error_info}

def decode_serialecho(message):
    ''' Messagein identifier:  1 byte: 201
    Message format:                     BITS USED   FPGA INDEX.
    echoed byte:        1 bytes [0:1]   8 bits      [0+:8]     
    device version:     7 bytes [1:8]   56 bits     [8+:56]    '''
    echoed_byte = message[0:1]
    try:
        device_version = message[1:8].decode()
        unprintable_byte = False
    except UnicodeDecodeError as err:
        device_version = message[1:8].decode(errors='ignore')
        unprintable_byte = True
    return {'echoed_byte':echoed_byte, 'device_version':device_version, 'unprintable_byte':unprintable_byte}

def decode_easyprint(message):
    ''' Messagein identifier:  1 byte: 202
    Message format:                     BITS USED   FPGA INDEX.
    printed message:    8 bytes [0:3]   64 bits     [0+:64]     '''
    binary_representation = []
    for letter in message[::-1]:
        binary_representation.append('{:08b} '.format(letter))
    return {'printed':''.join(binary_representation)}

def decode_pulserecord(message):
    ''' Messagein identifier:  1 byte: 204
    Message format:                     BITS USED   FPGA INDEX.
    pulse count:           7 bytes [0:7]   56 bits     [0+:56]     unsigned int.
    '''
    pulse_count, = struct.unpack('<Q', message[0:7] + bytes(1))
    return {'pulse_count':pulse_count}

def decode_devicestatus(message):
    ''' Messagein identifier:  1 byte: 203
    Message format:                     BITS USED   FPGA INDEX.
    FIFO_slots_used:      bytes [0:3]   25 bits     [0+:25]     unsigned int.
    '''
    slots_used, = struct.unpack('<Q', message[0:4] + bytes(4))
    return {'slots_used':slots_used}

#### encode
def encode_echo(byte_to_echo):
    ''' Messageout identifier:  1 byte: 150
    Message format:                             BITS USED   FPGA INDEX.
    byte_to_echo:               1 byte  [0:18]  8 bits     [0+:8]  
    '''    
    message_identifier = struct.pack('B', msgout_identifier['echo'])
    return message_identifier + byte_to_echo

def encode_general_debug(message):
    ''' Messageout identifier:  1 byte: 151
    Message format:                             BITS USED   FPGA INDEX.
    general_putpose_input:      8 bytes [0:8]   64 bits     [0+:64]     unsigned int.
    '''
    message_identifier =    struct.pack('B', msgout_identifier['general_input'])
    message =               struct.pack('<Q', message)[:8]
    return message_identifier + message

def encode_settings(enable_counter=None, enable_send_counts=None, holdoff_time=None, request_status=False, purge_memory=False, zero_pulse_counter=False, reset_device=False, request_counter_value=False):
    ''' Messageout identifier:  1 byte: 152
    Message format:                             BITS USED   FPGA INDEX.
    Tag_settings:               1 byte  [0]     8 bits      [0+:8]       unsigned int.
        enable_record                           1bit        [0]
        update_enable_record                    1bit        [1]
        enable_send_record                      1bit        [2]
        update_enable_send_record               1bit        [3]
        request_status                          1bit        [4]
        purge_memory                            1bit        [5]
        zero_pulse_timer                        1bit        [6]
        reset_device                            1bit        [7]
    holdoff_time                4 bytes         28bits      [7+:28]
        update_holdoff_time                     1bit        [35]
    request_counter_value_tag                   1bit        [36]

    Note, this is now a mix of setting and action requests.
    '''
    request_counter_value_tag = encode_lookup['request_counter_value'][request_counter_value] << 29 #Note, this is a bit of a hack. I couldnt be bothered making a whole other tag byte.

    holdoff_time_val = 0 | request_counter_value_tag
    if holdoff_time         is not None: holdoff_time_val = holdoff_time | (1 << 28)

    enable_record_tag       = encode_lookup['enable_record'][enable_counter] << 0
    enable_send_record_tag  = encode_lookup['enable_send_record'][enable_send_counts] << 2
    request_status_tag      = encode_lookup['request_status'][request_status] << 4
    purge_memory_tag        = encode_lookup['purge_memory'][purge_memory] << 5
    zero_pulse_timer_tag    = encode_lookup['zero_pulse_timer'][zero_pulse_counter] << 6
    reset_device_tag        = encode_lookup['reset_device'][reset_device] << 7
    tags = enable_record_tag | enable_send_record_tag | request_status_tag | purge_memory_tag | zero_pulse_timer_tag | reset_device_tag
    message_identifier =    struct.pack('B', msgout_identifier['settings'])
    tags =                  struct.pack('<Q', tags)[:1]
    holdoff_time =          struct.pack('<Q', holdoff_time_val)[:4]
    return message_identifier + tags + holdoff_time

msgin_decodeinfo = {
    200:{'message_length':3, 'decode_function':decode_internal_error},
    201:{'message_length':9, 'decode_function':decode_serialecho},
    202:{'message_length':9, 'decode_function':decode_easyprint},
    203:{'message_length':5, 'decode_function':decode_devicestatus},
    204:{'message_length':8, 'decode_function':decode_pulserecord}}

msgin_identifier = {
    'error':200,
    'echo':201,
    'print':202,
    'devicestatus':203,
    'pulserecord':204}

decode_lookup = {
    'invalid_identifier':{1:True, 0:False},
    'msg_not_forwarded':{1:True, 0:False},
    'msg_receive_timeout':{1:True, 0:False}
}

msgout_identifier = {
    'echo':150,
    'general_input':151,
    'settings':152
}

encode_lookup = {
    'request_status':{True:1, False:0},
    'reset_device':{True:1, False:0},
    'purge_memory':{True:1, False:0},
    'zero_pulse_timer':{True:1, False:0},
    'enable_record':{True:0b11, False:0b10, None:0b00},
    'enable_send_record':{True:0b11, False:0b10, None:0b00},
    'request_counter_value':{True:1, False:0}
}

def print_bytes(bytemessage):
    print('Message:')
    # for letter in instruction[:1:-1]:
    for letter in bytemessage[::-1]:
        print('{:08b}'.format(letter), end =" ")
    print('')
