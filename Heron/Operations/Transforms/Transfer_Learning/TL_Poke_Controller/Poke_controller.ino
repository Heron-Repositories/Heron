// This is the arduino .ino file that needs to be running on the arduino for the code in the tl_poke_controller_worker.py
// to make sense.
// It spits out a 555/r/n when pin 6 is low (i.e when the beam of beam breaker 1 breaks)
// and a 666/r/n when pin 5 is low (i.e. when the beam of the beam breaker 2 breaks).
// It turns on and off the relay at pin 4 when it receives a b'a'.
// It plays a tone if it receives any letters (in bytes) from b to l (10 different tones from 500 to 5000Hz).
// It moves the servo controlling the pellet switch either clockwise (when it receives a b'm') or counter clockwise
// (when it receives a b'n').

#include <Servo.h>

#define servo_pin 3
#define relay_1 4
# define beambreak_2_in 5
# define beambreak_1_in 6
#define relay_2 7
#define relay_3 8
#define relay_4 12
# define tone_pin 10

int incomingByte = 0;
int beambreak_1_value = 0;
int beambreak_2_value = 0;
int servo_position = 0;

Servo Pellet_Swithing_Servo;

void setup() {

  Serial.begin(9600);
  pinMode(relay_1, OUTPUT);
  pinMode(relay_2, OUTPUT);
  pinMode(relay_3, OUTPUT);
  pinMode(relay_4, OUTPUT);

  pinMode(beambreak_1_in, INPUT_PULLUP);
  pinMode(beambreak_2_in, INPUT_PULLUP);

  digitalWrite(relay_1, HIGH);

  Pellet_Swithing_Servo.attach(3);
}

void loop() {
  if (Serial.available() > 0) {
    incomingByte = Serial.read();
    Serial.println(incomingByte);

    if (incomingByte == 97){
      digitalWrite(relay_1, LOW);
      delay(200);
      digitalWrite(relay_1, HIGH);
    }

    if (incomingByte >= 98 && incomingByte <= 108){
      Serial.println(incomingByte);
      tone(tone_pin, 500 + (incomingByte-98)*500, 200);
    }

    if (incomingByte > 108){
      if (incomingByte == 109){ // n is right (the old poke)
        servo_position = 90;
      }
      if (incomingByte == 110){ // m is left (the new poke)
        servo_position = 60;
      }

      Pellet_Swithing_Servo.write(servo_position);
    }
  }

  beambreak_1_value = digitalRead(beambreak_1_in);
  if (beambreak_1_value == 0){
    Serial.println(555);
  }

  beambreak_2_value = digitalRead(beambreak_2_in);
  if (beambreak_2_value == 0){
    Serial.println(666);
  }

}