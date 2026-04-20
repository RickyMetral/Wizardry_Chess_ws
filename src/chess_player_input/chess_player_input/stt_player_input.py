"""Orchestrates how to return what move each side makes using Lichess API or stt model."""
import rclpy
from rclpy.node import Node
import sounddevice as sd
from gpiozero import Button
from chess_interfaces.srv import PlayerInput 
import json
import queue
import threading
from vosk import Model, KaldiRecognizer  
from chess_common_py.config import VOSK_PATH, VOICE_ACTIVATION_PIN
from chess_board_state.board_state import BoardState
from std_msgs.msg import String


class STTPlayerInputSrvNode(Node):
    board = BoardState(use_ros = False)

    def __init__(self, button_pin):
        super().__init__("stt_chess_input_service_node")
        self.srv = self.create_service(PlayerInput, "player_input", self.get_next_move_callback)
        self.move_sub = self.create_subscription(String, "player_move", self.board.update_board_state, 10)
        self.model = Model(VOSK_PATH)
        self.q = queue.Queue()
        self.grammar = ["one", "two", "three", "four", "five", "six", "seven", "eight", 
               "a", "b", "c", "d", "e", "f", "g", "h", "[unkown]"]
        self.WORD_TO_DIGIT = {
            "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8"
        }
        self.recognizer = KaldiRecognizer(self.model, 16000, json.dumps(self.grammar))
        self.stream = sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype='int16',
            channels=1, callback=self.audio_callback  
        )
        self.stream.start()
        self.button = Button(button_pin, pull_up = True, hold_time = 0.3)
        self.button.when_held = self.listen_for_audio
        self.button.when_released= self.stop_listening_audio

        self._listening = threading.Event()

        self.move_count = 0
        self.moves = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

        self.get_logger().info("Chess player input service node ready!")

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.get_logger().warn(f"Audio stream status: {status}")
        self.q.put(bytes(indata))

    def stop_listening_audio(self):
        self._listening.clear()
        #Empty the queue 
        while not self.q.empty():
            self.q.get()

        self.get_logger().info("Stopped Listening")

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

    def process_vosk_result(self, text):
        text = text.split()
        converted_words = [self.WORD_TO_DIGIT.get(w, w) for w in text]
        return "".join(converted_words)

    def listen_for_audio(self):
        self.get_logger().info("Listening for move...")
        self._listening.set()
        # self._listening_event.set()  

        while self._listening.is_set():  
            data = self.q.get()
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                text = self.process_vosk_result(text)

                self.get_logger().info(f"Move Captured: {text}")
                if len(text) == 4 and self.append_to_move_buffer(text, validate=True):
                    self.get_logger().info(f"Move validated!")
                    # self._listening_event.clear()  
                    return text
                self.get_logger().info(f"Given move invalid")


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
    node = STTPlayerInputSrvNode(VOICE_ACTIVATION_PIN)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()