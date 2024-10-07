# PiRover Simulator



## Install

To clone this project run `git clone git@github.com:legorovers/pirover_simulator.git`

To install the required packages run `pip install -r requirements.txt`

To run the project on Linux and Windows run `python3 pysim.py` and for MacOS run `python3 pysimosx.py`


## Development

### Current issues

- Sort out syntax issues when running the simulator
- Fix `pi2go.py` depreciated functions
- Fix developer documentation
- Update interface for editing the environments for robots
- Keep editor window in view when maximising window view
- Replace licensing for images
- 4tronix robots should be added to the simulator
- Make physics more realistic
- Make new workbooks targeted at half hour visits for about 15 children (ages 11-14)

### Testing

To run the docker image, first install docker and then run `sudo docker build pirover .; sudo docker run pirover`. This will not spawn the application but serves as a good basis to ensure the code works in different environments or which packages could break it

TODO: Add instructions for windows and MacOS
