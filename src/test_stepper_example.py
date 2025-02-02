"""
Andrea Favero 02/02/2025

Micropython code for Raspberry Pi Pico (RP2040 and RP2350)
It demonstrates how to use PIO functions to control a stepper motor:
  - implementation for steppers running with steps frequency between 50Hz and 5KHz.
  - min and max stepper frequency can be defined upfront: Suitable PIO frequency is calculated
    according to the min and max stepper frequency.
  - the 'speed' for the stepper is passed to the PIO, that generates the pulses at GPIO Pin.
  - the 'steps' for the stepper is passed to the PIO, and meant to be the predefined steps
    after that the stepper stops.
  - a PIO based counter counts the steps at the GPIO Pin.
  - once the steps are made, a PIO interrupt stops the step generator (therefore the stepper motor).
  - counted steps (effectively made) are retrieved by the main program from the PIO ISR register.
  - stepper rotation time is (precisely) calculated in the main loop, upfront the stepper activation.
  - pre-encoded istructions to the PIO (>100 times faster)

Notes:
  - 5KHz determines >3 revs/s for a stepper set at 1600 steps/rev.
  - 1600 steps/rev is a common Nema 17 stepper (200 steps/rev) with 1/8 microstepping.

PIO counter accuracy, as implemented (RP2350 is more accurate than RP2040):
  - RP2350 no missed steps for stepper frequency from 10Hz to 15KHz.
  - RP2040 no missed steps for stepper frequency from 50Hz to 5KHz.
  - RP2040 up to 1% missed steps for frequency 5KHz to 10KHz and below 50Hz.
  
For demo purposes the RP2040 LED pin is used, by blinking it at the stepper frequency.



MIT License

Copyright (c) 2025 Andrea Favero

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from stepper import Stepper
import sys, os, time, random

if __name__ == "__main__":
    """
    This example tests the counter accuracy on random frequencies within a give frequency range.
    Each random frequency is tested for a number of tests (RUNS)
    """
    

    # defining the range of frequency for steps counter accuracy test
    MIN_STEPPER_FREQUENCY = 200             # minimum stepper frequency to test
    MAX_STEPPER_FREQUENCY = 15000           # maximum stepper frequency to test
    
    
    # defining the number of steps per each of the test run
    MIN_PIO_STEPS = 5                       # min number of steps to test at each run (random pick between min and max)
    MAX_PIO_STEPS = 20                      # max number of steps to test at each run (random pick between min and max)
    
    # defining the number of runs per each of the test frequency
    RUNS = int(200)                         # number of test runs per each frequency
    PAUSE_BETWEEN_RUNS = 0.4                # sleep time (s) between each run
    
    # defining the visual feedback 
    SLOW_INIT = True                        # enables onboard (RP2040) led blinking to feedback the PIO initialization
    RUN_PRINTOUT = False                    # prints consitions and results at each run
    PRINT_SUMMARY = True                    # prints the summary of each run
    PRINT_LISTS = True                      # prints the list with most relevant test data
    print_once = True                       # flags for one time printing
    
    # parameters based on the implemented StateMachine0 (sm0), responsable for the steps generation
    PIO_FIX = 37                            # number of PIO commands that are always done
    PIO_VAR = 2                             # number of PIO commands that are repeated the times of value passed to the PIO
    
    
    # lists for main data storage
    freq_list = []                          # list to store the test stepper frequency
    error_list = []                         # list to store the errors
    
        
    # sanity check
    if MIN_STEPPER_FREQUENCY > MAX_STEPPER_FREQUENCY:
        print("\nThe MIN_STEPPER_FREQUENCY must be <= MAX_STEPPER_FREQUENCY\n")
        sys.exit(1)          # exit with a non-zero status to indicate an error
    
    
    try:
    
        # determining wich board_type is used
        board_info = os.uname()
        
        # assigning max PIO frequency
        if '2040' in board_info.machine:
            if 'W' in board_info.machine:
                board_type = 'RP2040 W'
            else:
                board_type = 'RP2040'
            max_pio_frequency = 125_000_000
            
        elif '2350' in board_info.machine.lower():
            if 'W' in board_info.machine:
                board_type = 'RP2350 W'
            else:
                board_type = 'RP2350'
            max_pio_frequency = 150_000_000
        else:
            board_type = '???'
            max_pio_frequency = 125_000_000
        
        print("\nCode running in {} board".format(board_type))
        
        
        # PIO frequency, for the steps generator function, is calculated
        # With 5MHz the passed value of 16bits works great for Nema17, as the value to pass to sm0 fits a 16bits
        pio_frequency = min(5000000,max(2500*MIN_STEPPER_FREQUENCY, 1000*MAX_STEPPER_FREQUENCY))
        pio_frequency = max(2000, pio_frequency)
        
        
        # calculating the values to pass to the PIO to test up to the max Pin frequency requested
        min_step_period_ms = 1000 / MAX_STEPPER_FREQUENCY
        min_pio_val = int(round((min_step_period_ms * pio_frequency - 1000 * PIO_FIX) / (1000 * PIO_VAR)))
        max_generator_frequency_hz = int(1000 / min_step_period_ms)
        
        
        # calculating the values to pass to the PIO to test up to the min Pin frequency requested 
        max_step_period_ms = 1000 / MIN_STEPPER_FREQUENCY
        max_pio_val = int(round((max_step_period_ms * pio_frequency - 1000 * PIO_FIX) / (1000 * PIO_VAR)))
        min_generator_frequency_hz = int(1000 / max_step_period_ms)
        
   
        # shell printouts for the initializaion part
        if SLOW_INIT:
            print("\nInitializing the stepper Class ...")
            print("PIO steps generator initialized at {:d} Hz:".format(pio_frequency))
            if print_once:
                print_once = False   
                print("Onboard led blinks slowly for a few times during initialization")
                if board_type == 'RP2040':
                    print("\nDuring testing the led visibility and blinking depends on test parameters\n\n")   
        else:
            if print_once:
                print("\nTest started ...")
                print_once = False
        
        
        # stepper Class instantiatiation
        stepper = Stepper(max_freq = max_pio_frequency,
                          freq = pio_frequency,
                          slow_init = SLOW_INIT)
        
        
        # variables to be reset at every test run
        stepper_pos = 0                           # reset the counted stepper steps, after each run
        expected_pos = 0                          # reset the total of the counted stepper steps (all runs)
        max_tested_f = 0                          # reset the max frequency (tested) at the stepper steps Pin 
        min_tested_f = max_generator_frequency_hz # reset the min frequency (tested) at the stepper steps Pin
        max_pio_val_passed = 0                    # reset the max value passed to the PIO
        min_pio_val_passed = 10 * min_pio_val     # reset the min value passed to the PIO
        
        
        t_start = time.ticks_ms()                 # time reference for all runs
        
        
        # iteration over the test RUNS for the set frequency
        for run in range(RUNS):
            
            if RUN_PRINTOUT:
                print("Run {:d} of {:d}".format(run+1, RUNS))
            
            
            # speed and steps parameters for the stepper activation are randomly generated (as example)
            speed = random.randint(min_pio_val, max_pio_val)      # stepper speed. This parameter is a delay between pulses ...
            steps = random.randint(MIN_PIO_STEPS, MAX_PIO_STEPS)  # number of steps for the stepper. Low values for fast testing ...
            
            
            # stepper motor activation time is calculated
            # PIO_VAR = instructions that repeat per each of the passed (speed) value to the PIO function
            # PIO_FIX = fix instructions at PIO function
            step_time_ms = 1000 * (speed * PIO_VAR + PIO_FIX) / pio_frequency
            generator_frequency_hz = int(1000 / step_time_ms)
            stepper_moving_time_ms = int(steps * step_time_ms)
            
            
            if RUN_PRINTOUT:
                print("Stepper speed:             {:d} ({:d} Hz)".format(speed, generator_frequency_hz))
                print("Number of steps:           {:d}".format(steps))
            
            
            # interaction with the stepper Class (based on PIO)
            stepper.reset_pulses_counter()     # reset motor steps counter
            stepper.set_pulses_to_do(steps-1)  # number of steps to execute
            stepper.sm0.put(speed)             # the stepper speed is passed
            time.sleep_ms(2)                   # little delay to get PIOs set
            stepper.sm0.active(1)              # state machine sm0 activated (stepper pulses generator starts)
            

            # sleep time until the stepper is moving
            t_ref = time.ticks_ms()
            while time.ticks_ms()-t_ref < stepper_moving_time_ms + 1:
                time.sleep(0.1)
            if RUN_PRINTOUT:
                print("Stepper rotation time:     {:d} ms".format(stepper_moving_time_ms))
            
            
            # retrives the PIO counted steps made on the current test run
            pulses = stepper.get_pulses_count()
            
            
            # check if error (return is -1) at the PIO counted steps
            if pulses >= 0:
                if RUN_PRINTOUT:
                    if pulses == steps:
                        print("Steps counted on last run:", pulses)
                    else:
                        print("Steps counted on last run:", pulses, "\t\t\tNOT OK")
            else:
                print("\nError on retrieving the IRS value")
                break

            
            # update the total steps made
            # use -= in case the stepper is set to of opposite rotation (when implementin the final stepper control)
            stepper_pos += pulses                     # totale PIO counted stepper steps, updated after each test run
            expected_pos += steps                     # total expected stepper steps sent to the PIO, updated after each test run
            
            
            if RUN_PRINTOUT:
                print("Expected total steps:     ", expected_pos)
            
            
            # stats on min and max frequency sent to the PIO (it has more sense when testing via random picked frequency)
            max_tested_f = max(max_tested_f, generator_frequency_hz)
            min_tested_f = min(min_tested_f, generator_frequency_hz)
            max_pio_val_passed = max(max_pio_val_passed, speed)
            min_pio_val_passed = min(min_pio_val_passed, speed)
            
            
            # sleep time for runs separation time
            t_ref2 = time.ticks_ms()
            while 1000 * (time.ticks_ms()-t_ref2) < PAUSE_BETWEEN_RUNS:
                time.sleep(0.02)
            if RUN_PRINTOUT:
                print("\n")
        
            
            # results resuming
            counter_error = stepper_pos - expected_pos     # error is calculated for all the test RUNS
            if expected_pos != 0:                          # preventing zero dovision ...
                counter_error_perc = round(100*counter_error/expected_pos, 2)   # error percentage
            else:
                print("\nEnsure RUNS>0 or steps>0 to prevent zero divison.")
                break
            
            
            # lists are updated
            error_list.append(counter_error_perc)
            freq_list.append(generator_frequency_hz)
            
            
            # runt test time is measured
            run_test_time = round(0.001 * (time.ticks_ms()-t_start), 1)
        
        
        # printing out the results
        if PRINT_SUMMARY:
            print()
            print("#"*40)
            print("  PIO steps generator at:   {:d} Hz".format(pio_frequency))
            print()
            print("  Stepper max freq. tested:", max_tested_f,"Hz")
            print("  Stepper min freq. tested:", min_tested_f,"Hz")
            print()
            print("  Min pio value passed:    ", min_pio_val_passed)
            print("  Max pio value passed:    ", max_pio_val_passed)
            print()
            print("  Total generated steps:   ", expected_pos)
            print("  Total counted steps:     ", stepper_pos)
            print("  Counter errors:           {} ({}%)".format(counter_error, counter_error_perc))
            print()
            print("  Total test time:          {} secs".format(run_test_time))
            print("#"*40)
            print("\n"*2)
        
        
        # printing out the results
        if PRINT_LISTS:
            print("Frequency list:", freq_list)
            print("Error list:", error_list)
            print()
            
            
    # handling exceptiond
    except KeyboardInterrupt:              # keyboard interrupts
        print("\nCtrl+C detected! ...")
        
    except Exception as e:                 # case of error 
        print(f"\nAn error occured: {e}")
    
    # handling closure
    finally:                               # deactivating the PIO
        if "stepper" in locals():
            stepper.deactivate_pio()
        print("\nTest concluded")


