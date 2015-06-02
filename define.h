#ifndef __define_h__
#define __define_h__

#ifndef NULL
#define NULL 0
#endif

#define CMD_PING        0x01
#define CMD_PONG        0x02
#define CMD_WHOIS       0x03
#define CMD_DESCRIPTION 0x04
#define CMD_ACK         0x05
#define CMD_DRAW_PIXELS 0x06
#define CMD_SET_PALET   0x07
#define CMD_CLICK       0x08

#define CONSUMER_STATE_WAITING      0x00
#define CONSUMER_STATE_READ_HEADER  0x01
#define CONSUMER_STATE_READ_DATA    0x02

struct msg_base
{
    uint8     cmd;
    uint8     cmd_id;
};

struct msg_description
{
    struct msg_base     base;
    char                name[16];
    char                version[6];
};

#endif
