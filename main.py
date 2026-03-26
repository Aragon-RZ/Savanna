# main.py
from engine.builder import SafariBuilder

def main():
    # Construct the simulation using Method Chaining
    builder = SafariBuilder(max_ticks=240)

    #uses SafariBuilder to create the environemnt, spawn animals and configure the simulaiton 
    
    engine = (builder.build_environment() #creates the watering hole 
                    .add_zebras(10)      # Spawn a big herd!
                    .add_elephants(2)
                    .add_lions(3)        # A pride of lions
                    .add_leopards(1)
                    .add_bushbabies(4)
                    .get_engine())

    # Run the simulation
    engine.start()
    engine.join()

if __name__ == "__main__":
    main()