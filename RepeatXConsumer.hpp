#ifndef __RepeatXConsumer_h__
#define __RepeatXConsumer_h__

#include "BaseConsumer.h"
#include "functions.hpp"
#include "PaletConsumer.hpp"

class RepeatXConsumer : public BaseConsumer
{
    private:
        struct msg_pixels alloc_header;
        uint8 alloc_buffer[2];
        PaletConsumer* palet_cons;
        uint32 real_index;

    protected:
        virtual void end()
        {
            drawEnd();
            this->real_index = 0;

            struct msg_base res;
            res.cmd = CMD_ACK;
            res.cmd_id = ((struct msg_base *)this->header)->cmd_id;
            socket_send((uint8*)&res, sizeof(res));
        }

        virtual uint32 parseHeader()
        {
            return this->alloc_header.size;
        }

        virtual void proceed_item(uint8* buffer, uint32 index)
        {
            uint16 x2;
            uint16 y2;
            uint16 color = this->palet_cons->getColor(buffer[1]);
            for (uint16 i = 0; i < buffer[0]; ++i)
            {
                y2 = this->real_index;
                for (uint16 x2 = 0; x2 < this->alloc_header.w; ++x2)
                {
                    drawPixel(this->alloc_header.x + x2, this->alloc_header.y + y2, color);
                }
                ++(this->real_index);
            }
        }

    public:
        RepeatXConsumer() : BaseConsumer(CMD_REPEAT_X, sizeof(this->alloc_header), (uint8 *)&(this->alloc_header), sizeof(this->alloc_buffer), (uint8 *)&(this->alloc_buffer)), real_index(0) {}
        void setPalet(PaletConsumer* palet_cons)
        {
            this->palet_cons = palet_cons;
        }
};

#endif
