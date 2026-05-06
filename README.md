# Wizardry Chess

A ROS2-based robotic chess system that physically moves pieces on a real chessboard using a 2D cartesian gantry hidden under a chess table. Players can interact via voice commands (speech-to-text) or through the Lichess online platform. The system also features a "loyalty" mechanic — if a player makes consistently bad moves, the robot may override their input with a random move like in Harry Potter!

## How It Works

The project is split into several ROS2 packages that communicate over topics and services:

- **`chess_board_state`** — Maintains the internal board state using the `python-chess` library. Validates moves, tracks captures, and interfaces with Stockfish for board evaluation.
- **`chess_planner`** — The central orchestrator. Manages turn order, requests moves from the input service, tracks player loyalty scores, and publishes moves to the `player_move` topic.
- **`chess_player_input`** — Provides a ROS2 service that supplies moves for each side. Supports two backends: speech-to-text (Vosk) with a physical button, and Lichess API streaming.
- **`chess_nav`** — Subscribes to `player_move` and handles all physical movement. Uses BFS pathfinding to navigate pieces around occupied squares on the board.
- **`chess_motor_schema`** — Low-level stepper motor and servo control for the XY gantry and Z-axis arm via Raspberry Pi GPIO.
- **`chess_interfaces`** — Custom ROS2 service and message definitions shared across packages.
- **`chess_common_py`** / **`chess_common_cpp`** — Shared utilities, configuration constants, and the Lichess API wrapper.

Two launch modes are supported:
- `stt_chess.launch.py` — Voice-controlled local game
- `lichess_chess.launch.py` — Play against a Lichess bot

---

## Getting Started

### Prerequisites

- [ ] ROS2 (Humble or newer)
- [ ] Python 3.10+
- [ ] Raspberry Pi (for hardware control) or a machine with GPIO simulation
- [ ] Stockfish chess engine installed
- [ ] A Lichess account and API token (for Lichess mode)
- [ ] Vosk speech model downloaded (for STT mode)

## Environment Variables

 Run the following command to export necessary environment variables
 1. **Download Stockfish**
    ```bash
    #Download stockfish https://stockfishchess.org/download/
    #Unzip downloaded file
    #Output path to stockfish
    which stockfish
    ```
    
  2. **Get Lichess API Token**
     - Download your token at [Lichess Token Generator](https://lichess.org/account/oauth/token/create)
       
  3. **Add Environment Variables**
     ```bash
     echo "export STOCKFISH_PATH=/path/to/stockfish" > ~/.bashrc
     echo "export LICHESS_TOKEN=your_lichess_api_token_here" > ~/.bashrc
     ```

## Installation

To set up the docker environment manually do the following:

1. **Download the base ROS2 container**
    - Follow the instructions in the file below to download the base image:

    [Getting Started with ROS2 in Docker](https://docs.google.com/document/d/18rpQyCBjzm2WsNtz2WmJEUn3cp52JED8hbf0TEfT4p4/edit?usp=sharing)

2. **Clone the repository**
   ```bash
   git clone https://github.com/RickyMetral/Wizardry_Chess_ws.git
   cd Wizardry_Chess_ws
   ```

3. **Set up a Python virtual environment**
   ```bash
   sudo apt install python3.10-venv
   python3 -m venv .venv --system-site-packages
   source .venv/bin/activate
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Download the Vosk speech model** (STT mode only)
   ```bash
   # Download from https://alphacephei.com/vosk/models
   # Extract to the project root as: vosk-model-small-en-us/
   ```

6. **Update dependencies**
   ```bash
   # Update missing dependencies
   sudo apt get update
   sudo apt install <missing dependency>
   ```

7. **Build with colcon**
   ```bash
   colcon build
   source install/setup.bash
   ```

OR to download the fully working image:

 1. **Download the image with all dependencies installed**
    **Write instructions to pull from docker hub here**

## Running the Project

**Start the Docker Container**
  - To start the container use the following docs:
    [Getting Started with ROS2 in Docker](https://docs.google.com/document/d/18rpQyCBjzm2WsNtz2WmJEUn3cp52JED8hbf0TEfT4p4/edit?usp=sharing)

  - After building and sourcing with colcon use the following comamnds to run the project:
**Voice-controlled (STT) mode:**
```bash
ros2 launch chess_common_py stt_chess.launch.py
```

**Lichess bot mode:**
```bash
ros2 launch chess_common_py lichess_chess.launch.py
```
  *Note: The lichess version does not include loyalty

---

## Hardware Setup

- [ ] Add wiring diagram here
- [ ] Add list of required components (stepper drivers, motors, electromagnet, etc.)

---

## Configuration

All tunable parameters live in `src/chess_common_py/chess_common_py/config.py`, including motor step sizes, board dimensions, GPIO pin assignments, gantry speed, and player color selection.

---

## Links

- [Getting Started with ROS2 in Docker](https://docs.google.com/document/d/18rpQyCBjzm2WsNtz2WmJEUn3cp52JED8hbf0TEfT4p4/edit?usp=sharing)
- [Fully Detailed Report](docs/Wizardry_Chess_Final_Report.pdf)
- [Demo Video](https://drive.google.com/file/d/1FdIVNJVsC7M01BdKD7TQzL181ZxDv5et/view?usp=sharing)







