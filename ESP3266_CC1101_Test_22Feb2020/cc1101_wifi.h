#include <ESP8266WiFi.h>

#ifndef STASSID
#define STASSID "blerg"
#define STAPSK  "VUrocks00!!"
#endif

const char* ssid = STASSID;
const char* password = STAPSK;

// Create an instance of the server
// specify the port to listen on as an argument
WiFiServer server(80);

void wifi_setup() {
  // Connect to WiFi network
  Serial.println();
  Serial.println();
  Serial.print(F("Connecting to "));
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(F("."));
  }
  Serial.println();
  Serial.println(F("WiFi connected"));

  // Start the server
  server.begin();
  Serial.println(F("Server started"));

  // Print the IP address
  Serial.println(WiFi.localIP());
}

void process_http_req() {
  // Check if a client has connected
  WiFiClient client = server.available();
  if (!client) {
    return;
  }
  //Serial.println(F("new client"));

  client.setTimeout(1000); // default is 1000

  // Read the first line of the request
  String req = client.readStringUntil('\r');
  //Serial.println(F("request: "));
  //Serial.println(req);

  // Match the request
  if (req.indexOf(F("/1/0")) != -1) {
    set_switch(1, false); 
  } else if (req.indexOf(F("/1/1")) != -1) {
    set_switch(1, true); 
  } else if (req.indexOf(F("/2/0")) != -1) {
    set_switch(2, false); 
  } else if (req.indexOf(F("/2/1")) != -1) {
    set_switch(2, true); 
  } else if (req.indexOf(F("/3/0")) != -1) {
    set_switch(3, false); 
  } else if (req.indexOf(F("/3/1")) != -1) {
    set_switch(3, true); 
  }
  // read/ignore the rest of the request
  // do not client.flush(): it is for output only, see below
  while (client.available()) {
    // byte by byte is not very efficient
    client.read();
  }

  client.print(F("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<!DOCTYPE HTML>\r\n<html>blerg</html>"));

}
