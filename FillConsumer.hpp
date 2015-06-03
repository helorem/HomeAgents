#ifndef __FillConsumer_h__
#define __FillConsumer_h__

#include "BaseConsumer.h"
#include "functions.hpp"

class FillConsumer : public BaseConsumer
{
    private:
        struct msg_fill alloc_header;

    protected:
        virtual void end()
        {
            for (uint16 i = 0; i < this->alloc_header.h; ++i)
            {
                for (uint16 j = 0; j < this->alloc_header.w; ++j)
                {
                    drawPixel(this->alloc_header.x + j, this->alloc_header.y + i, this->alloc_header.color);
                }
            }

            struct msg_base res;
            res.cmd = CMD_ACK;
            res.cmd_id = ((struct msg_base *)this->header)->cmd_id;
            socket_send((uint8*)&res, sizeof(res));
        }

    public:
        FillConsumer() : BaseConsumer(CMD_FILL_COLOR, sizeof(this->alloc_header), (uint8 *)&(this->alloc_header)) {}
};

#endif
