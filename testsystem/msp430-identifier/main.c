/*
 * Copyright 2023 EAS Group
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy 
 * of this software and associated documentation files (the “Software”), to deal 
 * in the Software without restriction, including without limitation the rights 
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
 * copies of the Software, and to permit persons to whom the Software is 
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in 
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
 * SOFTWARE.
 */
#include <msp430f5529.h>

#define CLK_FREQ 1048576 // ~1 MHz
#define BAUD_RATE 1200
#define BYTE_DURATION_IN_CLK_TICKS 24 // 1 Start bit + 8 Data bits + 1 Stop bit + 14 Ticks pause
#define TX_PAUSE_IN_CLK_TICKS 128     // Pause between broadcasts (~100ms)

#ifdef __RTS_GEN
#define DEVICE_ID <DEVICE_ID>
#else
#define DEVICE_ID 0xDEADBEAF
#endif

#define SET_PORTS(func, val) \
    P1##func = val;          \
    P2##func = val;          \
    P3##func = val;          \
    P5##func = val;          \
    P6##func = val;          \
    P7##func = val;          \
    P8##func = val;

unsigned char _uart_data;
unsigned int _uart_state_index;
unsigned int _byte_index;

unsigned const char _pin_id_lookup[8][8] = {
    {0xAA, 0xCC, 0xF0, 0x00, 0xFF, 0x00, 0x00, 0x00},
    {0xAA, 0xCC, 0xF0, 0x00, 0x00, 0xFF, 0x00, 0x00},
    {0xAA, 0xCC, 0xF0, 0x00, 0xFF, 0xFF, 0x00, 0x00},
    {0xAA, 0xCC, 0xF0, 0x00, 0x00, 0x00, 0xFF, 0x00},
    {0xAA, 0xCC, 0xF0, 0x00, 0xFF, 0x00, 0xFF, 0x00},
    {0xAA, 0xCC, 0xF0, 0x00, 0x00, 0xFF, 0xFF, 0x00},
    {0xAA, 0xCC, 0xF0, 0x00, 0xFF, 0xFF, 0xFF, 0x00},
    {0xAA, 0xCC, 0xF0, 0x00, 0x00, 0x00, 0x00, 0xFF}};

void uart_output(int send_bit_id, int index)
{
    if (index == 0) // Start
    {
        SET_PORTS(OUT, 0)
    }
    else if (index >= 1 && index < (1 + 8)) // Data
    {
        if (send_bit_id)
        {
            P1OUT = _pin_id_lookup[0][index - 1];
            P2OUT = _pin_id_lookup[1][index - 1];
            P3OUT = _pin_id_lookup[2][index - 1];
            P4OUT = _pin_id_lookup[3][index - 1];
            P5OUT = _pin_id_lookup[4][index - 1];
            P6OUT = _pin_id_lookup[5][index - 1];
            P7OUT = _pin_id_lookup[6][index - 1];
            P8OUT = _pin_id_lookup[7][index - 1];
        }
        else
        {
            int bit = (_uart_data >> (index - 1)) & 0x1;
            if (bit)
            {
                SET_PORTS(OUT, 0xFF)
            }
            else
            {
                SET_PORTS(OUT, 0)
            }
        }
    }
    else // Stop & Idle
    {
        SET_PORTS(OUT, 0xFF)
    }
}

void uart_send(unsigned char data)
{
    _uart_state_index = 0;
    _uart_data = data;
}

void init()
{
    // Configure output
    SET_PORTS(SEL, 0)
    SET_PORTS(DIR, 0xFF)

    // Configure timer
    TA0CCR0 = (int)(CLK_FREQ / BAUD_RATE);
    TA0CTL = MC_1 + TASSEL_2 + TACLR + ID_0;
    TA0CCTL0 = CCIE;

    __enable_interrupt();
}

void run()
{
    uart_output(_byte_index == 0, _uart_state_index);

    // Identify msp430 board with 32-bit board id and 8-bit pin id
    if (_uart_state_index > BYTE_DURATION_IN_CLK_TICKS && _byte_index > 0)
    {
        // Send 32-bit board id
        _byte_index--;
        if (_byte_index > 0)
        {
            uart_send((unsigned char)((DEVICE_ID >> (_byte_index - 1) * 8) & 0xFF));
        }
        // Send 8-pin pin id
        else
        {
            // We don't care about data, each pin has its own data
            uart_send(0x00);
        }
    }
    // Restart sending after some timeout
    else if (_uart_state_index > TX_PAUSE_IN_CLK_TICKS && _byte_index == 0)
    {
        // Restart sending
        _byte_index = 5;
    }
}

int main(int argc, char **argv)
{
    WDTCTL = WDTPW + WDTHOLD; // Stop watchdog timer

    init();

    for (;;)
    {
        run();
    }

    return 0;
}

__attribute__((interrupt(TIMER0_A0_VECTOR))) void TIMERA0_ISR(void)
{
    _uart_state_index++;
}