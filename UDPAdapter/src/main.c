/*
 * Copyright (C) 2019-2019 Wuming Liu (lwmqwer@163.com)
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <pthread.h>
#include "type.h"
#include "adapter.h"


record_t records[] = {
#include "map"
};
portmap_t map;
option_t  option = {0, 0, 50000, 20482, "192.168.2.100"};


static void
init_portmap(portmap_t *map, record_t *records, uint_t num_record) {
    map->num_records = num_record;
    map->records = records;
}

static void
parse_option(int argc, char *argv[])
{
    int           opt;
    struct option longopts[] = {
        {"print_packet", 0, NULL, 'p'},
        {"debug", 1, NULL, 'd'},
        {"listen_port", 1, NULL, 'l'},
        {"fpga_port", 1, NULL, 'f'},
        {"fpga_ip", 1, NULL, 'i'},
        {NULL, 0, NULL, 0}
    };

    for (;;) {
        opt = getopt_long(argc, argv, "pd:l:f:i:", longopts, NULL);
        if (opt == -1) {
            break;
        }
        switch (opt) {
        case 'p':
            option.print_packet = 1;
            break;
        case 'd':
            option.debug_level = atoi(optarg);
            break;
        case 'l':
            option.listen_port = atoi(optarg);
            break;
        case 'f':
            option.fpga_port = atoi(optarg);
            break;
        case 'i':
            option.fpga_ip = optarg;
            break;
        default:
            break;
        }
    }
}

int
main(int argc, char *argv[]) {
    int rc;
    pthread_t send_thread, recv_thread;

    parse_option(argc, argv);

    init_portmap(&map, records, sizeof(records) / sizeof(record_t));

    rc = pthread_create(&send_thread, NULL, sender, (void *) &map);
    if (rc != 0) {
        perror("Fail to create send thread");
        exit(EXIT_FAILURE);
    }
    rc = pthread_create(&recv_thread, NULL, receiver, (void *) &map);
    if (rc != 0) {
        perror("Fail to create creceive thread");
        exit(EXIT_FAILURE);
    }

    rc = pthread_join(recv_thread, NULL);
    if (rc != 0) {
        perror("Receiver thread exit unnormally");
        exit(EXIT_FAILURE);
    }
    exit(EXIT_SUCCESS);
}


