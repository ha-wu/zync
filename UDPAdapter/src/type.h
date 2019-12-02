/*
 * Copyright (C) 2019-2019 Wuming Liu (lwmqwer@163.com)
 */
#ifndef _UDPADAPTER_TYPE_H
#define _UDPADAPTER_TYPE_H

#define ADP_OK     0
#define ADP_ERROR -1

typedef unsigned char  uchar_t;
typedef unsigned short ushort_t;
typedef unsigned int   uint_t;
typedef unsigned long  ulong_t;

typedef struct {
    uchar_t      code;
    ushort_t     listen_port;
    ushort_t     source_port;
    const char  *source_ip;
} record_t;

typedef struct {
    uint_t          num_records;
    const record_t *records;
} portmap_t;

typedef struct {
    int    print_packet:1;
    int    debug_level:3;
    int    listen_port;
    int    fpga_port;
    char  *fpga_ip;
} option_t;
#endif
