#ifndef __BASE_CONSUMER_H__
#define __BASE_CONSUMER_H__

#include "types.h"
#include "define.h"

class BaseConsumer
{
    private:
        uint16 remaining;
        uint8  header_size;
        uint8  state;
        uint8  buffer_size;
        uint8  buffer_index;
        uint8* buffer;
        uint16 index;

        struct msg_base base_header_allocated;

    protected:
        uint8* header;

    protected:
        virtual void end() = 0;
        virtual uint16 parseHeader();
        virtual void proceed_item(uint8* buffer, uint16 index);

    public:
        BaseConsumer(uint8 cmd);
        BaseConsumer(uint8 cmd, uint8 header_size, uint8* header, uint8 buffer_size, uint8* buffer);
        bool consume(uint8 data);
};

#endif
