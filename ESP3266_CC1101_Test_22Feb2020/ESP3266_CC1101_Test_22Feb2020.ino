/*

*/
#include <SPI.h>
#include "CC1101.h"
#include "CC1101_wifi.h"

void setup() {
  //pinMode(LED_BUILTIN, OUTPUT);     // Initialize the LED_BUILTIN pin as an output
  Serial.begin(9600);
  cc1101_init();
  wifi_setup();
}

void loop() {
  process_http_req();
}
