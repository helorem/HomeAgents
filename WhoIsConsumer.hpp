#ifndef __WhoIsConsumer_h__
#define __WhoIsConsumer_h__

#include "BaseConsumer.h"
#include  "functions.hpp"

class WhoIsConsumer : public BaseConsumer
{
    protected:
        virtual void end()
        {
            struct msg_description res;
            res.base.cmd = CMD_DESCRIPTION;
            res.base.cmd_id = ((struct msg_base *)this->header)->cmd_id;
            m_strcpy(res.name, "cpp_client", sizeof(res.name));
            m_strcpy(res.version, "1.0.0", sizeof(res.version));
            socket_send((uint8*)&res, sizeof(res));
        }

    public:
        WhoIsConsumer() : BaseConsumer(CMD_WHOIS) {}
};

#endif
