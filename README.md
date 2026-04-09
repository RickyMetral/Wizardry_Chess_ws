# Wizardry_Chess_ws

To get virtual environments in this docker container run:
```sudo apt install python3.10-venv```

To set up the virutal environment use the command:
```python3 -m venv .venv --system-site-packages```

Then run this command to get all necessary packages:
```pip install -r requirements.txt```

To get into the virtual environemnt use the command:
```source ./path/to/venv/bin/activate```

*************Notes***************
- MENTION TO ADD PROPER ENV VARIABLES(LICHESS_TOKEN, STOCKFISH PATH)
- Maybe get rid of virtual environments if using docker
- explain how to build using colcon
- write summary of what each package does 


