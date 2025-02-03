# Accurate stepper motor control, based on micropython and  PIO 

Suitable for RP2040 or RP2350 (Raspberry Pi Pico, Pico2, RP2040-Zero, RP2350-Zero, etc).

I'm working on a project with stepper motors and RP2040 microprocessor and I realized this stepper motor's control (Class) might be useful to other makers.


Overall concept is to predefine the speed and the steps for the stepper, and let it running in open loop ... by trusting it stops once those steps are made!

The precise spinning time is calculated, upfront the stepper activation, allowing to be ready with a new set of instructions for the following run.

Depending on the microprocess used, this implementation is accurate for pulses frequency between 50Hz and 5KHz (RP2040) or between 10Hz and 15KHz (RP2350). The common Nema 17 steppers, with 200 pulses per revolution and controlled with 1/8 microsteps, very likely do not require more than 5KHz in most of the applications.


## Features
  - min and max stepper frequency can be defined upfront: Suitable PIO frequency is calculated according to the min and max stepper frequency.
  - the 'speed' for the stepper is passed to the PIO, that generates the pulses at GPIO Pin.
  - the 'steps' for the stepper is passed to the PIO, and meant to be the  predefined steps after that the stepper stops.
  - a PIO based counter counts the steps at the GPIO Pin.
  - once the steps are made, a PIO interrupt stops the step generator (therefore the stepper motor).
  - counted steps (effectively made) are retrieved by the main program from the PIO ISR register.
  - stepper rotation time is (precisely) calculated in the main loop, upfront the stepper activation.
  - pre-encoded istructions to the PIO (>100 times faster)


## Accuracy
PIO counter accuracy (as implemented):
  - RP2350: does not miss any step for stepper frequency between 10Hz and 15KHz.
  - RP2040: does not miss any step for stepper frequency between 50Hz and 5KHz.
  - RP2040: up to 1% missed steps for frequency between 5KHz and 10KHz.
  
RP2350 is clearly more accurate than RP2040.

Each datapoint in below chart is the error % out of of 200 runs, each of them with a number of pulses randomly picked between 5 and 20:
 
  ![title image](/images/accuracy.jpg)
 


## Installation
1. Copy `\src\stepper.py` to your Raspberry Pi Pico.
2. Copy one of the exaples to your Raspberry Pi Pico folder.
2. Run the script in MicroPython.


## Notes
In case of Raspbeery Pi Pico board (not the W or Pico 2 versions), the onboard led blinks at the steps frequency as vsual feedback.

Feel free to use this code.
Of course, using this code is at your own risk :-)

