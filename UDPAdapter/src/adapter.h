/*
 * Copyright (C) 2019-2019 Wuming Liu (lwmqwer@163.com)
 */
#ifndef _UDPADAPTER_SENDER_H
#define _UDPADAPTER_SENDER_H

#define MAX_SEND_TRY 1
#define MAX_SEND_FPGA_TRY 1


void *sender(void *args);
void *receiver(void *args);
#endif
