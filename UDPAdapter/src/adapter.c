/*
 * Copyright (C) 2019-2019 Wuming Liu (lwmqwer@163.com)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <unistd.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <netinet/udp.h>
#include <netinet/ip.h>
#include <arpa/inet.h>
#include <pthread.h>

#include "type.h"
#include "msg_type.h"
#include "adapter.h"


extern option_t option;


static uchar_t
get_code(uint16_t port, const portmap_t *map)
{
    uint_t i;

    for (i = 0; i < map->num_records; i++) {
        if (map->records[i].listen_port == port) {
            return map->records[i].code;
        }
    }
    return 0xFF;
}


static void
send_msg_to_fpga(uchar_t *msg, size_t len){
    int                 i, sockfd;
    size_t              socklen;
    ssize_t             send;
    struct sockaddr_in  addr;

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr(option.fpga_ip);
    addr.sin_port = htons(option.fpga_port);
    socklen = sizeof(addr);

    for(i = 0; i < MAX_SEND_FPGA_TRY; i++) {
        sockfd = socket(AF_INET, SOCK_DGRAM, 0);
        send = sendto(sockfd, msg, len, 0,
                    (struct sockaddr *) &addr, socklen);
        if (send <= 0 || (size_t) send <= len) {
            break;
        }
    }
    close(sockfd);
}


static void
adapt_msg_to_fpga(uchar_t *udp_packet, size_t len, const portmap_t *map)
{
    fpga_msg_hdr_t *hdr;
    struct udphdr  *udphdr = (struct udphdr *) udp_packet;

    hdr = (fpga_msg_hdr_t *) (udp_packet + sizeof(struct udphdr) - 1);

    hdr->flag = hdr->code;
    hdr->code = get_code(ntohs(udphdr->dest), map);
    if (hdr->code == 0xFF) {
        fprintf(stderr, "Cannot find code for port %d\n", ntohs(udphdr->dest));
        return;
    }
    send_msg_to_fpga((uchar_t *) hdr, len - sizeof(struct udphdr) + 1);
}


void *
receiver(void *args)
{
    int                 sockfd;
    size_t              len;
    ssize_t             result;
    uchar_t             buffer[MSG_MAXLENTH];
    struct sockaddr_in  addr;
    const portmap_t    *map = (portmap_t *) args;

    printf("Receive thread start!\n");
    sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_UDP);
    if (sockfd == -1) {
        pthread_exit("Fail to create socket");
    }

    while (1) {
        result = recvfrom(sockfd, buffer, sizeof(buffer), 0, (struct sockaddr *)&addr, (socklen_t *) &len);
        if (result <= 0) {
            perror("Receive failed");
        }

        if (option.print_packet) {
            uchar_t *body, *body_end;
            struct udphdr  *hdr = (struct udphdr *) (buffer + sizeof(struct iphdr));

            body = buffer + sizeof(struct iphdr) + sizeof(struct udphdr);
            body_end = buffer + result;
            printf("Receive from: %s, ", inet_ntoa(addr.sin_addr));
            printf("Source Port: %d, Destination Port: %d\n",
                   ntohs(hdr->source), ntohs(hdr->dest));
            printf("Body: %*s\n", (int) (body_end - body), body);
        }

        adapt_msg_to_fpga(buffer + sizeof(struct iphdr), result - sizeof(struct iphdr), map);
    }
    pthread_exit("Receiver exit normally");
}


static int
get_peer_addr_v4(uchar_t code, const portmap_t *map, struct sockaddr_in *addr)
{
    uint_t i;

    for (i = 0; i < map->num_records; i++) {
        if (map->records[i].code == code) {
            addr->sin_family = AF_INET;
            addr->sin_addr.s_addr = inet_addr(map->records[i].source_ip);
            addr->sin_port = htons(map->records[i].source_port);
            return ADP_OK;
        }
    }
    return ADP_ERROR;
}


int
send_to_control(uchar_t *fpgamsg, size_t size, const portmap_t *map)
{
    int                 sockfd;
    ssize_t             result;
    struct sockaddr_in  addr;
    fpga_msg_hdr_t     *hdr = (fpga_msg_hdr_t *) fpgamsg;

    if (get_peer_addr_v4(hdr->code, map, &addr) != ADP_OK) {
        fprintf(stderr, "Cannot find ip and port for code %d\n", hdr->code);
        return ADP_ERROR;
    }
    hdr->code = hdr->flag;

    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    result = sendto(sockfd, &hdr->code, size - 1, 0,
                    (struct sockaddr *) &addr, sizeof(addr));

    close(sockfd);
    return (size_t ) result == size - 1 ? ADP_OK : ADP_ERROR;
}


void *
sender(void *args)
{
    int                 i, sockfd;
    uchar_t             buf[MSG_MAXLENTH];
    size_t              len;
    ssize_t             size;
    const portmap_t    *map = (portmap_t *) args;
    struct sockaddr_in  addr;

    printf("Sender thread start!\n");
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd == -1) {
        perror("Fail to connect FPGA device");
        pthread_exit("Fail to connect FPGA device");
    }

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(option.listen_port);
    len = sizeof(addr);
    bind(sockfd, (struct sockaddr *) &addr, len);

    for(;;) {
        size = recvfrom(sockfd, buf, sizeof(buf), 0, (struct sockaddr *) &addr, (socklen_t *) &len);
        if (size <= 0) {
            continue;
        }

        if (option.print_packet) {
            printf("Receive from: %s:%d\n", inet_ntoa(addr.sin_addr), ntohs(addr.sin_port));
            printf("Body: %*s\n", (int) size, buf);
        }

        for(i = 0; i < MAX_SEND_TRY; i++) {
            if (send_to_control(buf, size, map) == ADP_OK) {
                break;
            }
        }
    }
    close(sockfd);
    pthread_exit("Sender exit normally");
}
