#ifndef __functions_h__
#define __functions_h__

#include "types.h"

void drawEnd();
void drawPixel(int x, int y, uint16 color565);
void socket_send(const uint8* data, uint16 data_size);

void m_strcpy(char* dest, const char* source, uint8 size)
{
    uint16 i = 0;
    for (;source[i] != 0 && i < size - 1; ++i)
    {
        dest[i] = source[i];
    }
    for (; i < size; ++i)
    {
        dest[i] = 0;
    }
}

#endif
