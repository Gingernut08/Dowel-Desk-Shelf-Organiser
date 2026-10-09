#include <Keyboard.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// GPIO
const int BUTTON_COUNT = 5;
const int BUTTON_PINS[BUTTON_COUNT] = {26, 27, 28, 29, 0};

// Shortcuts
struct KeyCombo {
    const uint8_t* keys;
    size_t count;
};

// Button states
int buttonStates[BUTTON_COUNT];
int lastButtonStates[BUTTON_COUNT];

// Debounce
unsigned long lastDebounceTime[BUTTON_COUNT] = {0};
const unsigned long DEBOUNCE_DELAY = 30;

// OLED settings
#define SCREEN_HEIGHT = 32
#define SCREEN_WIDTH = 128
#define OLED_RESET = -1
#define OLED_ADDRESS = 0x3C

Adafruit_SSD1306 display(
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    &Wire,
    OLED_RESET
)


// Set up buttons
void setup(){
    for (int i = 0; i < BUTTON_COUNT; i++){
        pinMode(BUTTON_PINS[i], INPUT_PULLUP);
        
        buttonStates[i] = HIGH;
        lastButtonStates[i] = HIGH;
    }

    Keyboard.begin();
}

// Send keypress when button is pressed
void press_shortcut(int button){
    switch (button){
        case 0:
            // Shortcut 1
            break;
        case 1:
            // Shortcut 2
            break;
        case 2:
            // Shortcut 3
            break;
        case 3:
            // Shortcut 4
            break;
        case 4:
            // Shortcut 5
            break;
    }
}

void loop(){
    for (int i = 0; i < BUTTON_COUNT; i++){
        int reading = digitalRead(BUTTON_PINS[i]);
        
        if (reading != lastButtonStates[i]){
            lastDebounceTime[i] = millis();
        }
        
        if ((millis() - lastDebounceTime[i]) > DEBOUNCE_DELAY){
            if (reading != buttonStates[i]){
                buttonStates[i] = reading;
                
                // Trigger only on press
                if (buttonStates[i] == LOW){
                    press_shortcut(i);
                    Keyboard.releaseAll();
                }
            }
        }
        
        lastButtonStates[i] = reading;
    }
}