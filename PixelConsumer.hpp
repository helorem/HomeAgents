#ifndef __PixelConsumer_h__
#define __PixelConsumer_h__

#include "BaseConsumer.h"
#include "functions.hpp"
#include "PaletConsumer.hpp"

class PixelConsumer : public BaseConsumer
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
            for (uint16 i = 0; i < buffer[0]; ++i)
            {
                x2 = this->real_index % this->alloc_header.w;
                y2 = this->real_index / this->alloc_header.w;
                drawPixel(this->alloc_header.x + x2, this->alloc_header.y + y2, this->palet_cons->getColor(buffer[1]));
                ++(this->real_index);
            }
        }

    public:
        PixelConsumer() : BaseConsumer(CMD_DRAW_PIXELS, sizeof(this->alloc_header), (uint8 *)&(this->alloc_header), sizeof(this->alloc_buffer), (uint8 *)&(this->alloc_buffer)), real_index(0) {}
        void setPalet(PaletConsumer* palet_cons)
        {
            this->palet_cons = palet_cons;
        }
};

#endif
