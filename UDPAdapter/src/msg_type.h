/*
 * Copyright (C) 2019-2019 Wuming Liu (lwmqwer@163.com)
 */
#ifndef _UDPADAPTER_MSG_TYPE_H
#define _UDPADAPTER_MSG_TYPE_H

#include "type.h"

#define MSG_MAXLENTH 2048

typedef struct {
    uchar_t flag;
    uchar_t NS;
    uchar_t type;
} pc_msg_hdr_t;

typedef struct {
    uchar_t flag;
    uchar_t code;
    uchar_t NS;
    uchar_t type;
} fpga_msg_hdr_t;
#endif
