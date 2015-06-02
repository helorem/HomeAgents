#ifndef __PaletConsumer_h__
#define __PaletConsumer_h__

#include "BaseConsumer.h"
#include  "functions.hpp"

class PaletConsumer : public BaseConsumer
{
    private:
        struct msg_palet alloc_header;
        uint16 alloc_buffer;
        uint16 palet[256];

    protected:
        virtual void end()
        {
            struct msg_base res;
            res.cmd = CMD_ACK;
            res.cmd_id = ((struct msg_base *)this->header)->cmd_id;
            socket_send((uint8*)&res, sizeof(res));
        }

        virtual uint32 parseHeader()
        {
            return this->alloc_header.size * sizeof(this->alloc_buffer);
        }

        virtual void proceed_item(uint8* buffer, uint32 index)
        {
            this->palet[index] = *((uint16*)buffer);
        }

    public:
        PaletConsumer() : BaseConsumer(CMD_SET_PALET, sizeof(this->alloc_header), (uint8 *)&(this->alloc_header), sizeof(this->alloc_buffer), (uint8 *)&(this->alloc_buffer)) {}
        uint16 getColor(uint8 index) const
        {
            return this->palet[index];
        }
};

#endif
