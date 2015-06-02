#ifndef __PingConsumer_h__
#define __PingConsumer_h__

#include "BaseConsumer.h"
#include  "functions.hpp"

class PingConsumer : public BaseConsumer
{
    protected:
        virtual void end()
        {
            struct msg_base res;
            res.cmd = CMD_PONG;
            res.cmd_id = ((struct msg_base *)this->header)->cmd_id;
            socket_send((uint8*)&res, sizeof(res));
        }

    public:
        PingConsumer() : BaseConsumer(CMD_PING) {}
};

#endif
