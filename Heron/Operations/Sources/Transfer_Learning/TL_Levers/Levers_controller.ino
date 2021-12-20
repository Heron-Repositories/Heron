
#define beambreak_in 4
#define beambreak_out 8  // This is to push the beambreak value to another board (here a Touch Board)
#define left_lever 5
#define right_lever 7

int beambreak_value = 0;
int left_lever_value = 0;
int right_lever_value = 0;

unsigned long currentTime = 0;
unsigned long leftLeverStartTime = 0;
unsigned long rightLeverStartTime = 0;
unsigned long leftLeverPressedTime = 0;
unsigned long rightLeverPressedTime = 0;

void setup() {
  Serial.begin(9600);
  pinMode(left_lever, INPUT);
  pinMode(right_lever, INPUT);
  pinMode(beambreak_in, INPUT_PULLUP);
  pinMode(beambreak_out, OUTPUT);
}

void loop() {

  beambreak_value = digitalRead(beambreak_in);
  digitalWrite(beambreak_out, beambreak_value);

  if (beambreak_value == 0)
  {
    left_lever_value = digitalRead(left_lever);
    right_lever_value = digitalRead(right_lever);

    if (right_lever_value == 1 && left_lever_value == 1){
      leftLeverStartTime = 0;
      rightLeverStartTime = 0;
      leftLeverPressedTime = 0;
      rightLeverPressedTime = 0;
    }else{
      if (left_lever_value == 1){
      if (leftLeverStartTime == 0){
        leftLeverStartTime = millis();
      }
      leftLeverPressedTime = millis() - leftLeverStartTime;
    }else{
      leftLeverStartTime = 0;
      leftLeverPressedTime = 0;
    }

    if (right_lever_value == 1){
      if (rightLeverStartTime == 0){
        rightLeverStartTime = millis();
      }
      rightLeverPressedTime = millis() - rightLeverStartTime;
    }else{
        rightLeverStartTime =0;
        rightLeverPressedTime = 0;
      }
    }
  }

  if (beambreak_value == 1){
    leftLeverStartTime = 0;
    rightLeverStartTime = 0;
    leftLeverPressedTime = 0;
    rightLeverPressedTime = 0;
  }

  String string_out = "Poke=";
    string_out.concat(beambreak_value);
    string_out.concat("#Left=");
    string_out.concat(leftLeverPressedTime);
    string_out.concat("#Right=");
    string_out.concat(rightLeverPressedTime);
    Serial.println(string_out);

  delay(100);

}