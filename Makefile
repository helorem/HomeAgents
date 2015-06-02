OBJS = *pp
CC = g++
LINKER_FLAGS = -lSDL2 -lSDL2main
OBJ_NAME = client

all : $(OBJS)
		$(CC) $(OBJS) $(COMPILER_FLAGS) $(LINKER_FLAGS) -o $(OBJ_NAME)

