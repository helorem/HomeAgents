#include "BaseConsumer.h"

BaseConsumer::BaseConsumer(uint8 cmd) :
    header_size(sizeof(this->base_header_allocated)),
    header((uint8 *)&(this->base_header_allocated)),
    state(CONSUMER_STATE_WAITING),
    remaining(0),
    buffer_size(0),
    buffer(NULL),
    buffer_index(0),
    base_header_allocated(),
    index(0)
{
    base_header_allocated.cmd = cmd;
}

BaseConsumer::BaseConsumer(uint8 cmd, uint8 header_size, uint8* header) :
    header_size(header_size),
    header(header),
    state(CONSUMER_STATE_WAITING),
    remaining(0),
    buffer_size(0),
    buffer(NULL),
    buffer_index(0),
    base_header_allocated(),
    index(0)
{
    base_header_allocated.cmd = cmd;
}

BaseConsumer::BaseConsumer(uint8 cmd, uint8 header_size, uint8* header, uint8 buffer_size, uint8* buffer) :
    header_size(header_size),
    header(header),
    state(CONSUMER_STATE_WAITING),
    remaining(0),
    buffer_size(buffer_size),
    buffer(buffer),
    buffer_index(0),
    base_header_allocated(),
    index(0)
{
    base_header_allocated.cmd = cmd;
}

uint32 BaseConsumer::parseHeader()
{
    return 0;
}

void BaseConsumer::proceed_item(uint8* buffer, uint32 index)
{
}

bool BaseConsumer::consume(uint8 data)
{
    if (this->remaining > 0)
    {
        switch (this->state)
        {
            case CONSUMER_STATE_READ_HEADER:
                this->header[this->header_size - this->remaining] = data;
                --(this->remaining);
                if (this->remaining == 0)
                {
                    this->remaining = this->parseHeader();
                    if (this->remaining > 0)
                    {
                        this->state = CONSUMER_STATE_READ_DATA;
                    }
                    else
                    {
                        this->state = CONSUMER_STATE_WAITING;
                        this->end();
                    }
                }
                break;

            case CONSUMER_STATE_READ_DATA:
                this->buffer[this->buffer_index] = data;
                --(this->remaining);
                ++(this->buffer_index);
                if (this->buffer_index == this->buffer_size)
                {
                    this->proceed_item(this->buffer, this->index);
                    this->buffer_index = 0;
                    ++this->index;
                }
                if (this->remaining == 0)
                {
                    this->state = CONSUMER_STATE_WAITING;
                    this->end();
                }
                break;
        }
        return true;
    }
    else if (data == this->base_header_allocated.cmd)
    {
        this->remaining = this->header_size - 1;
        this->index = 0;
        if (this->remaining > 0)
        {
            this->state = CONSUMER_STATE_READ_HEADER;
        }
        else
        {
            this->remaining = 0;
        }
        return true;
    }

    return false;
}


