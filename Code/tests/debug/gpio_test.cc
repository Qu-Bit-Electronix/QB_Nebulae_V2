#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <wiringPi.h>
#include <time.h>

using namespace std;

#define RESET_LED 26
#define DATA_PIN 21
#define CLK_PIN 15
#define LATCH_PIN 16

#define GATE_NEXT 4
#define GATE_RECORD 5
#define GATE_RESET 6
#define GATE_FREEZE 11
uint8_t update_sr();

int main(void) {
  wiringPiSetup();
  pinMode(RESET_LED, OUTPUT);
  pinMode(DATA_PIN, INPUT);
  pinMode(CLK_PIN, OUTPUT);
  pinMode(LATCH_PIN, OUTPUT);
  pinMode(GATE_NEXT, INPUT);
  pinMode(GATE_RECORD, INPUT);
  pinMode(GATE_RESET, INPUT);
  pinMode(GATE_FREEZE, INPUT);
  uint8_t shift_status = 0xff;
  uint8_t gate_pins[] = { GATE_NEXT, GATE_RECORD, GATE_RESET, GATE_FREEZE };
  uint8_t gate_states[] = { 0, 0, 0, 0 };

  while(1) {
 	shift_status = update_sr();
	printf("shift in: %x\n", shift_status);
	for (uint8_t i = 0; i < 4; i++) {
		gate_states[i] = digitalRead(gate_pins[i]);		
	}
	printf("next: %d\trecord: %d\treset: %d\tfreeze: %d\n", gate_states[0], gate_states[1], gate_states[2], gate_states[3]);



  }
  return 0;
}

uint8_t update_sr()
{
	uint8_t states = 0x00;
	digitalWrite(LATCH_PIN, 1);
	delay(3);
   	digitalWrite(LATCH_PIN, 0);
	delay(3);
    for(int8_t i = 0; i < 8; i++){
    	digitalWrite(CLK_PIN, 0);
    	delay(3);
    	digitalRead(DATA_PIN) ? states |= (1 << i) : states &= ~(1 << i);
    	digitalWrite(CLK_PIN, 1);
    	delay(3);
    }
    return states;
}
