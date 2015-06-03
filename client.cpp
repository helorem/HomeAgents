#include <stdlib.h>
#include <stdio.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_thread.h>

#include <iostream>
#include <stdexcept>

#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>

#include "WhoIsConsumer.hpp"
#include "PingConsumer.hpp"
#include "PaletConsumer.hpp"
#include "PixelConsumer.hpp"
#include "FillConsumer.hpp"
#include "RepeatXConsumer.hpp"

#include "functions.hpp"

const int SCREEN_WIDTH = 240;
const int SCREEN_HEIGHT = 320;

BaseConsumer* consumers[30];

SDL_Window* window = NULL;
SDL_Surface* screenSurface = NULL;

int sdl_thread(void *data)
{
    bool quit;
    SDL_Event event;
    bool touch_down = false;

    if (SDL_Init(SDL_INIT_VIDEO) < 0)
    {
        printf("SDL could not initialize! SDL_Error: %s\n", SDL_GetError());
    }
    else
    {
        window = SDL_CreateWindow("Client", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, SCREEN_WIDTH, SCREEN_HEIGHT, SDL_WINDOW_SHOWN);
        if (window == NULL)
        {
            printf("Window could not be created! SDL_Error: %s\n", SDL_GetError());
        }
        else
        {
            screenSurface = SDL_GetWindowSurface( window );
            SDL_FillRect(screenSurface, NULL, SDL_MapRGB(screenSurface->format, 0x00, 0x00, 0x00));
            SDL_UpdateWindowSurface(window);
            while (quit == false)
            {
                while (SDL_PollEvent(&event))
                {
                    if (event.type == SDL_QUIT)
                    {
                        quit = true;
                    }
                    else if (event.type == SDL_MOUSEBUTTONDOWN)
                    {
                        touch_down = true;
                        struct msg_touch res;
                        res.base.cmd = CMD_TOUCH_DOWN;
                        res.base.cmd_id = 50; //TODO improve
                        res.x = event.button.x;
                        res.y = event.button.y;
                        socket_send((uint8*)&res, sizeof(res));
                    }
                    else if (event.type == SDL_MOUSEBUTTONUP)
                    {
                        touch_down = false;
                        struct msg_touch res;
                        res.base.cmd = CMD_TOUCH_UP;
                        res.base.cmd_id = 50; //TODO improve
                        res.x = event.button.x;
                        res.y = event.button.y;
                        socket_send((uint8*)&res, sizeof(res));
                    }
                    else if (event.type == SDL_MOUSEMOTION)
                    {
                        if (touch_down)
                        {
                            struct msg_touch res;
                            res.base.cmd = CMD_TOUCH_MOVE;
                            res.base.cmd_id = 50; //TODO improve
                            res.x = event.button.x;
                            res.y = event.button.y;
                            socket_send((uint8*)&res, sizeof(res));
                        }
                    }
                }
            }
        }
    }

    SDL_DestroyWindow(window);
    SDL_Quit();

    return 0;
}

uint32 convert_565(uint16 color)
{
    uint8 r = (color >> 8) & 0xF8;
    uint8 g = (color >> 3) & 0xFC;
    uint8 b = (color << 3) & 0xFF;

    return r << 16 | g << 8 | b;
}

void drawPixel2(int x, int y, uint8 r, uint8 g, uint8 b)
{

    SDL_Rect rect;
    rect.x = x;
    rect.y = y;
    rect.w = 1;
    rect.h = 1;

    SDL_FillRect( screenSurface, &rect, SDL_MapRGB( screenSurface->format, r, g, b ) );
}

void drawPixel(int x, int y, uint16 color565)
{

    uint32 color = convert_565(color565);

    uint8 r = (color565 >> 8) & 0xF8;
    uint8 g = (color565 >> 3) & 0xFC;
    uint8 b = (color565 << 3) & 0xFF;

    //std::cout << std::dec << "pixel " << x << "," << y << " " << std::hex << (int)color565 << "=>" << std::dec << (int)r << " " << (int)g << " " << (int)b << std::dec << std::endl;

    drawPixel2(x, y, r, g, b);
}

void drawEnd()
{
    SDL_UpdateWindowSurface( window );
}

int sockfd = 0;

void socket_send(const uint8* data, uint16 data_size)
{
    std::cout << "SEND " << data_size << " ";
    for (uint16 i = 0; i < data_size; ++i)
    {
        std::cout << std::hex << (int)(data[i]) << ' ';
    }
    std::cout << std::endl;
    send(sockfd, data, data_size, 0);
}

int initNetwork()
{
    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        printf("\n Error : Could not create socket \n");
        return 1;
    }

    struct sockaddr_in sin;
    sin.sin_addr.s_addr = inet_addr("127.0.0.1");
    sin.sin_port = htons(7654);
    sin.sin_family = AF_INET;

    if (connect(sockfd, (struct sockaddr *)&sin, sizeof(sin)) < 0)
    {
        printf("\n Error : Connect Failed \n");
        return 1;
    }

    uint8 idx = 0;
    WhoIsConsumer cons1 = WhoIsConsumer();
    consumers[idx++] = &cons1;

    PingConsumer cons2 = PingConsumer();
    consumers[idx++] = &cons1;

    PaletConsumer cons3 = PaletConsumer();
    consumers[idx++] = &cons3;

    PixelConsumer cons4 = PixelConsumer();
    cons4.setPalet(&cons3);
    consumers[idx++] = &cons4;

    FillConsumer cons5 = FillConsumer();
    consumers[idx++] = &cons5;

    RepeatXConsumer cons6 = RepeatXConsumer();
    cons6.setPalet(&cons3);
    consumers[idx++] = &cons6;

    consumers[idx] = NULL;


    int n = 0;
    unsigned char recv;
    std::cout << "read..." << std::endl;
    while ((n = read(sockfd, &recv, sizeof(recv))) > 0)
    {
        //std::cout << ":" << std::hex << (int)recv << std::dec << std::endl;
        for (unsigned int i = 0; consumers[i] != NULL; ++i)
        {
            if (consumers[i]->consume(recv))
            {
                if (i != 0)
                {
                    BaseConsumer* tmp = consumers[0];
                    consumers[0] = consumers[i];
                    consumers[i] = tmp;
                }
                break;
            }
        }
    }
}

int main(int argc, char* args[])
{
    SDL_Thread* threadID = SDL_CreateThread(sdl_thread, NULL, NULL);
    try
    {
        initNetwork();
    }
    catch (const std::exception &e)
    {
        printf("EX");
    }
    SDL_WaitThread(threadID, NULL);

    return 0;
}
