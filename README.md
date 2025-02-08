# Accurate stepper motor control, based on micropython and  PIO 

This code is for RP2040 or RP2350 microprocessors, as it leverages on the PIO feature; Boards with these micros are Raspberry Pi Pico, Pico2, RP2040-Zero, RP2350-Zero, and many others.

I'm working on a project with stepper motors and RP2040 microprocessor and I realized this stepper motor's control (Class) might be useful to other makers.


The overall concept is to predefine the speed and the steps for the stepper, and let it running in open loop ... by trusting it stops once those steps are made!

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


## Showcasing video
Showcase objective: Having the stepper motor stopping at the start position, with:
 - 52800 steps in total.
 - 126 direction changes.
 - relatively high motor speed (> 2 revs/s).
 - stop position at 360 degrees (1600 pulses) away from the start position.


[![Watch the Demo](https://img.youtube.com/vi/ZdNAM-4AH98/0.jpg)](https://www.youtube.com/watch?v=ZdNAM-4AH98)
![Track](/images/chart_image.png)

Test setup:
 - 3 NEMA 17 stepper motors
 - Motors are 200 pulses/rev set to 1/8 microstep: 1600 pulses/rev.
 - Each motor controlled by an RP2040-Zero board.
 - Commands (speed, steps) sent via I2C from a Raspberry Pi to the 3 RP2040-Zero boards.
 - Direction calculated at RP2040-Zero, if below/above a threshold (2^16 // 2).
 - Effective speed calculated at RP2040-Zero, as absolute difference from threshold (2^16 // 2).




## PIO counter accuracy
PIO counter accuracy (as implemented):
  - RP2350: does not miss any step for stepper frequency between 10Hz and 15KHz.
  - RP2040: does not miss any step for stepper frequency between 50Hz and 5KHz.
  - RP2040: up to 1% missed steps for frequency between 5KHz and 10KHz.
  
RP2350 is clearly more accurate than RP2040.

In below chart, each datapoint is the error % out of of 200 motor activation runs, wherein each activation run had a random number of pulses between 5 and 20; In other words each point reppresents about 2500 stepper'steps:
 
  ![title image](/images/accuracy.jpg)
 


## Installation
1. Copy `\src\stepper.py` to your Raspberry Pi Pico.
2. Copy one of the exaples to your Raspberry Pi Pico folder.
2. Run the script in MicroPython.


## Notes
In the examples provided, in case of Raspbeery Pi Pico board (not the W or Pico 2 versions), the onboard led blinks at the steps frequency as visual feedback. On the other boards the onboard led is not directly connected to a 'normal' GPIO pin.

Feel free to use this code, to mdify it according to your need, and to feedback in case of improvements proposals.

Of course, using this code is at your own risk :-)

