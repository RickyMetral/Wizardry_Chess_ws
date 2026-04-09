"""Orchestrates how to return what move each side makes using Lichess API or stt model."""
import rclpy
from rclpy.node import Node
import sounddevice as sd
from chess_interfaces.srv import PlayerInput, CheckMoveValid
import json
import queue
import threading
from chess_player_input.keyboard_input import KeyListener
from vosk import Model, KaldiRecognizer  # Fix: was KalidexRecognizer
from chess_board_state.board_state import BoardState
from std_msgs.msg import String


class STTPlayerInputSrvNode(Node):
    board = BoardState(use_ros = False)

    def __init__(self, activation_key="q"):
        super().__init__("chess_input_service_node")
        self.srv = self.create_service(PlayerInput, "player_input", self.get_next_move_callback)
        self.move_sub = self.create_subscription(String, "player_move", self.board.update_board_state, 10)
        self.model = Model("vosk-model-small-en-us")
        self.q = queue.Queue()
        self.grammar = ["a", "b", "c", "d", "e", "f", "g", "h",
                        "1", "2", "3", "4", "5", "6", "7", "8", "move"]
        self.recognizer = KaldiRecognizer(self.model, 16000, json.dumps(self.grammar))
        self.stream = sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype='int16',
            channels=1, callback=self.audio_callback  # Fix: implemented below
        )
        self.stream.start()

        # Fix: use threading.Event instead of a bare bool to eliminate the race condition.
        # Event.set/clear/is_set are all thread-safe by design, no external lock needed.
        self._listening_event = threading.Event()

        self.listener = KeyListener(self.listen_callback, self.stop_listening, activation_key)
        self.listener.start()  # Fix: was never called

        self.move_count = 0
        self.moves = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

        self.get_logger().info("Chess player input service node ready!")

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.get_logger().warn(f"Audio stream status: {status}")
        self.q.put(bytes(indata))

    def stop_listening(self):
        self._listening_event.clear()

    def get_next_move_callback(self, request, response):
        self.get_logger().info(f'Received request for color: {request.player_color}')
        self.update_move_count(request.move_count)
        self.get_logger().debug(f"Current list of moves:\n {self.moves}")

        if request.player_color == "w":
            response.move = self.get_white_move()
            return response
        elif request.player_color == "b":
            response.move = self.get_black_move()
            return response
        else:
            response.move = "error"
            return response

    def listen_callback(self):
        self.get_logger().info("Listening for move...")
        self._listening_event.set()  # Fix: thread-safe set

        # Clear stale audio
        while not self.q.empty():
            self.q.get()

        while self._listening_event.is_set():  
            data = self.q.get()
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")

                if len(text) == 4:
                    self.get_logger().info(f"Move Captured: {text}")
                    if self.append_to_move_buffer(text, validate=True):
                        self._listening_event.clear()  
                        return text
                    else:
                        while not self.q.empty():
                            self.q.get()

                elif len(text) > 4:
                    while not self.q.empty():
                        self.q.get()

    def get_white_move(self) -> str:
        with self.condition:
            self.condition.wait_for(lambda: len(self.moves) > self.move_count)
            if self.move_count % 2 == 0:
                return self.moves[self.move_count]
            else:
                self.get_logger().warn("Move count was not even")
                return "error"

    def get_black_move(self) -> str:
        with self.condition:
            self.condition.wait_for(lambda: len(self.moves) > self.move_count)
            if self.move_count % 2 == 1:
                return self.moves[self.move_count]
            else:
                self.get_logger().warn("Move count was not odd")
                return "error"

    def update_move_count(self, move_count: int):
        self.move_count = move_count

    def append_to_move_buffer(self, move: str, validate=True):
        if not validate:
            with self.condition:
                self.moves.append(move)
                self.condition.notify_all()
            self.get_logger().info(f"Valid move received: {move}")
            return True

        is_valid_move = self.board.check_move_valid(move)
        if is_valid_move or move in ("end", "error"):
            with self.condition:
                self.moves.append(move)
                self.condition.notify_all()
            self.get_logger().info(f"Valid move received: {move}")
            return True
        else:
            self.get_logger().warn(f"Invalid move received: {move}")
            return False


def main(args=None):
    rclpy.init(args=args)
    node = STTPlayerInputSrvNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()