# main.py
import time
from engine.builder import create_mvp_safari

def main():
    # 1. Build the world
    safari_engine = create_mvp_safari()

    # 2. Start the simulation on a background thread
    safari_engine.start() 

    # 3. Keep the main program alive and listen for exit commands
    try:
        while True:
            # The main thread just sleeps while the background thread does all the work
            time.sleep(1) 
    except KeyboardInterrupt:
        # If the user presses Ctrl+C, gracefully stop the engine thread
        safari_engine.stop()
        safari_engine.join() # Wait for the thread to finish its last tick
        print("Simulation terminated successfully.")

if __name__ == "__main__":
    main()


    #did i create a branch properly hihi? 