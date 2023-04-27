# Copied and modified from https://gist.github.com/chanil1218/2632048

# Makefile for msp430
#
# 'make' builds everything
# 'make clean' deletes everything except source files and Makefile
# You need to set TARGET, MCU and SOURCES for your project.
# TARGET is the name of the executable file to be produced 
# $(TARGET).elf $(TARGET).hex and $(TARGET).txt nad $(TARGET).map are all generated.
# The TXT file is used for BSL loading, the ELF can be used for JTAG use
# 
TIMEOUT    = 30
TARGET     = main
MCU        = msp430f5529
# List all the source files here
# eg if you have a source file foo.c then list it here
SOURCES = main.c
# Include are located in the Include directory
# INCLUDES = -I/root/ti/msp430-gcc/include/
# Add or subtract whatever MSPGCC flags you want. There are plenty more
#######################################################################################
CFLAGS   = -mmcu=$(MCU) -g -Os -Wall -Wunused $(INCLUDES)   
ASFLAGS  = -mmcu=$(MCU) -x assembler-with-cpp -Wa,-gstabs
LDFLAGS  = -mmcu=$(MCU) -Wl,-Map=$(TARGET).map -L$(LD_LIBRARY_PATH) -L$(LINKER_SCRIPT_PATH) -T$(MCU).ld
########################################################################################
CC       = msp430-elf-gcc
LD       = msp430-elf-ld
AR       = msp430-elf-ar
AS       = msp430-elf-gcc
GASP     = msp430-elf-gasp
NM       = msp430-elf-nm
OBJCOPY  = msp430-elf-objcopy
RANLIB   = msp430-elf-ranlib
STRIP    = msp430-elf-strip
SIZE     = msp430-elf-size
READELF  = msp430-elf-readelf
MAKETXT  = srec_cat
CP       = cp -p
RM       = rm -f
MV       = mv
########################################################################################
FLASHTOOL = MSP430Flasher
########################################################################################
# the file which will include dependencies
DEPEND = $(SOURCES:.c=.d)
# all the object files
OBJECTS = $(SOURCES:.c=.o)
all: $(TARGET).elf $(TARGET).hex $(TARGET).txt 
$(TARGET).elf: $(OBJECTS)
	echo "Linking $@"
	$(CC) $(OBJECTS) $(LDFLAGS) $(LIBS) -o $@
	echo
	echo ">>>> Size of Firmware <<<<"
	$(SIZE) $(TARGET).elf
	echo
%.hex: %.elf
	$(OBJCOPY) -O ihex $< $@
%.txt: %.hex
	$(MAKETXT) -O $@ -TITXT $< -I
%.o: %.c
	echo "Compiling $<"
	$(CC) -c $(CFLAGS) -o $@ $<
# rule for making assembler source listing, to see the code
%.lst: %.c
	$(CC) -c $(CFLAGS) -Wa,-anlhd $< > $@
# include the dependencies unless we're going to clean, then forget about them.
ifneq ($(MAKECMDGOALS), clean)
-include $(DEPEND)
endif
# dependencies file
# includes also considered, since some of these are our own
# (otherwise use -MM instead of -M)
%.d: %.c
	echo "Generating dependencies $@ from $<"
	$(CC) -M ${CFLAGS} $< >$@

flash: all
	timeout ${TIMEOUT}s sh -c '$(FLASHTOOL) -g -w $(TARGET).hex -n $(MCU) -i $(COMPORT) -z "[VCC]"'

.SILENT:
.PHONY:	clean
clean:
	-$(RM) $(OBJECTS)
	-$(RM) $(TARGET).map
	-$(RM) $(TARGET).elf $(TARGET).hex $(TARGET).txt
	-$(RM) $(TARGET).lst
	-$(RM) $(SOURCES:.c=.lst)
	-$(RM) $(DEPEND)