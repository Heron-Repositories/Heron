// This is the arduino .ino file that needs to be running on the arduino for the code in the tl_poke_controller_worker.py
// to make sense.
// It spits out a 0/r/n when pin 6 is low (i.e when the beam breaks).
// It turns on and off the relay at pin 4 when it receives a b'a' and plays a tone if it receives any letters
// (in bytes) from b to l (10 different tones from 500 to 5000Hz)

#define relay_1 4
#define relay_2 7
#define relay_3 8
#define relay_4 12

# define beambreak_in 6

# define tone_pin 10

int incomingByte = 0;
int beambreak_value = 0;

void setup() {

  Serial.begin(9600);
  pinMode(relay_1, OUTPUT);
  pinMode(relay_2, OUTPUT);
  pinMode(relay_3, OUTPUT);
  pinMode(relay_4, OUTPUT);

  pinMode(beambreak_in, INPUT_PULLUP);

  digitalWrite(relay_1, HIGH);
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
  }

  beambreak_value = digitalRead(beambreak_in);
  if (beambreak_value == 0){
    Serial.println(beambreak_value);
  }

}