const int chipSelectPin = 15;
const byte flag_read_single = 0x80;
const byte flag_write_single = 0x00;
const byte flag_read_burst = 0xC0;
const byte flag_write_burst = 0x40;
const byte flag_strobe = 0x00;

byte reg_inits[] = {   0x29,  // IOCFG2
                0x2E,  // IOCFG1
                0x06,  // IOCFG0
                0x47,  // FIFOTHR
                0xD3,  // SYNC1
                0x91,  // SYNC0
                0x0D,  // PKTLEN
                0x00,  // PKTCTRL1
                0x00,  // PKTCTRL0
                0x00,  // ADDR
                0x00,  // CHANNR
                0x06,  // FSCTRL1
                0x00,  // FSCTRL0
                0x10,  // FREQ2
                0xB1,  // FREQ1
                0xB1,  // FREQ0
                0xC6,  // MDMCFG4
                0x75,  // MDMCFG3
                0xB0,  // MDMCFG2
                0x02,  // MDMCFG1
                0xF8,  // MDMCFG0
                0x15,  // DEVIATN
                0x07,  // MCSM2
                0x30,  // MCSM1
                0x18,  // MCSM0
                0x14,  // FOCCFG
                0x6C,  // BSCFG
                0x03,  // AGCCTRL2
                0x00,  // AGCCTRL1
                0x92,  // AGCCTRL0
                0x87,  // WOREVT1
                0x6B,  // WOREVT0
                0xFB,  // WORCTRL
                0xB6,  // FREND1
                0x11,  // FREND0
                0xE9,  // FSCAL3
                0x2A,  // FSCAL2
                0x00,  // FSCAL1
                0x1F,  // FSCAL0
                0x41,  // RCCTRL1
                0x00,  // RCCTRL0
                0x59,  // FSTEST
                0x7F,  // PTEST
                0x3F,  // AGCTEST
                0x88,  // TEST2
                0x31,  // TEST1
                0x09};  // TEST0

void write_register(byte reg_addy, byte valToWrite){
  reg_addy = (reg_addy | flag_write_burst);
  digitalWrite(chipSelectPin, LOW);
  SPI.transfer(reg_addy);
  SPI.transfer(valToWrite);
  digitalWrite(chipSelectPin, HIGH);
}

byte cc1101_strobe(byte reg_addy){
  reg_addy = (reg_addy | flag_strobe);
  digitalWrite(chipSelectPin, LOW);
  SPI.transfer(reg_addy);
  byte inByte = SPI.transfer(0x00);
  digitalWrite(chipSelectPin, HIGH);  
  return (inByte);
}

byte read_register(byte reg_addy){
  reg_addy = (reg_addy | flag_read_burst);
  digitalWrite(chipSelectPin, LOW);
  SPI.transfer(reg_addy);
  byte inByte = SPI.transfer(0x00);
  digitalWrite(chipSelectPin, HIGH);  
  return (inByte);
}

byte cc1101_state(){
  digitalWrite(chipSelectPin, LOW);
  SPI.transfer(0xF5 | flag_read_burst);
  byte inByte = SPI.transfer(0x00);
  digitalWrite(chipSelectPin, HIGH);  
  return (inByte);
}

bool cc1101_alive() {
  return (read_register(0xf1) == 20 and read_register(0xf0) == 0);
}

void cc1101_init() {
  pinMode(chipSelectPin, OUTPUT);
  SPI.begin();
  Serial.print("Connecting to CC1101...");
  while(!cc1101_alive()){
    Serial.print(".");
    delay(100);
  }
  Serial.println(" Connected!");
  Serial.print("Configuring CC1101.");
  for (byte i = 0; i < 0x2F; i = i + 1) {
    write_register(i, reg_inits[i]);
  }
  digitalWrite(chipSelectPin, LOW);
  SPI.transfer(0x7E); // burst write to PATABLE
  SPI.transfer(0x00);
  SPI.transfer(0xC0);
  digitalWrite(chipSelectPin, HIGH);
  if(read_register(0x0F) != reg_inits[0x0F]){
    Serial.println(" failed!");
  } else {
    Serial.println(" success!");
  }
}

struct packet {
  byte address = 0x7F; // burst write to TX FIFO
  byte preamble[10] = { 0xE8, 0xEE, 0xE8, 0xE8, 0x88, 0x8E, 0x8E, 0xEE, 0x88, 0x88 };
  byte data[2] = { 0x8E, 0x8E };  //initialize to ON, 1st byte 0x8E -> 0xEE is OFF
  byte tail = 0x80;
} test_packet;

void send_packet(struct packet p) {
  cc1101_strobe(0x36); // change state to idle
  cc1101_strobe(0x3B); // flush TX FIFO
  cc1101_strobe(0x31); // calibrate frequency generator
  while(cc1101_state() != 18);
  digitalWrite(chipSelectPin, LOW);
  SPI.transfer(p.address);
  byte i = 0;
  while(p.preamble[i]){
//    Serial.print("Preamble byte ");
//    Serial.print(i);
//    Serial.print(":\t");
//    Serial.println(p.preamble[i]);
    SPI.transfer(p.preamble[i]);
    i = i + 1;
  }
  SPI.transfer(p.data[0]);
  SPI.transfer(p.data[1]);
  SPI.transfer(p.tail);
  digitalWrite(chipSelectPin, HIGH);
  cc1101_strobe(0x35); // change state to TX mode!
  while(cc1101_state() != 1);  
}

void set_switch(byte switch_num, bool state){
  switch (switch_num){
    case 1:
      test_packet.data[1] = 0x8E;
      if(state){
        test_packet.data[0] = 0x8E;
      } else{
        test_packet.data[0] = 0xEE;
      }
      break;
    case 2:
      test_packet.data[1] = 0xEE;
      if(state){
        test_packet.data[0] = 0x88;
      } else{
        test_packet.data[0] = 0xE8;
      }
      break;
    case 3:
      test_packet.data[1] = 0x8E;
      if(state){
        test_packet.data[0] = 0xE8;
      } else{
        test_packet.data[0] = 0x88;
      }
      break;
  }
  for(int i = 0; i < 3; i = i + 1){
    send_packet(test_packet);
    delay(10);
  }
}
