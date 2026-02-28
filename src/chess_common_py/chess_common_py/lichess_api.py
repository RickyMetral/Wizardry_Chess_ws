"""
This file is where all Lichess api wrappers will be written. Check out https://lichess.org/api#description/introduction for docs on the entire api.
Everything will be wrapped under the lichess class and be called as methods of said class. 
 """
import requests
import json
from chess_common_py.config import LICHESS_TOKEN

class LichessApi:
    bot_username = "maia9"
    move_count = 0
    _game_id = None
    _player_color = None

    def __init__(self, bot_username = ""):
        self.header = {"Authorization": f"Bearer {LICHESS_TOKEN}"}

        if(bot_username != ""):
            self.bot_username = bot_username

    """clock timer are in seconds. Timers will be invalid if not in specifc intervals. Look in lichess what those intervals are.""" 
    def start_game(self, player_color="random", clock_limit = 600, clock_increment = 5) -> bool:
        req_body = {
            "rated": False,
            "clock.limit": clock_limit ,     #Each players total time
            "clock.increment": clock_increment,   # Time each player gains when making a move
            "color": player_color,      # "white", "black", or "random"
            "variant": "standard",
        }

        response = requests.post(
            f"https://lichess.org/api/challenge/{self.bot_username}",
            headers=self.header,
            json = req_body        
        )

        data = response.json()

        if data.get("error") :
            print("Something went wrong!")
            print(data["error"])
            return False

        LichessApi._game_id = data["id"]
        LichessApi._player_color = data["finalColor"]

        if data.get("status") == "declined":
            print("Game was declined")
            print(f"View why here: https://lichess.org/{LichessApi._game_id}")
            return False

        print(f"Game started! https://lichess.org/{LichessApi._game_id}")
        return True

    def abort_game(self):
        r = requests.post(
            f"https://lichess.org/api/board/game/{LichessApi._game_id}/abort",
            headers=self.header
        )

        return r.json()

    def resign_game(self):
        r = requests.post(
            f"https://lichess.org/api/board/game/{LichessApi._game_id}/resign",
            headers=self.header
        )

        return r.json()

    def make_move(self, move: str):
        headers = {"Authorization": f"Bearer {LICHESS_TOKEN}"}
        r = requests.post(
            f"https://lichess.org/api/board/game/{LichessApi._game_id}/move/{move}",
            headers=headers
        )

        return r.json()

    def show_available_bots(self):
        print("maia1")
        print("maia5")
        print("maia9")
        print("Visit: lichess.org/player/bots for community bots!")
    
    #Returns json object of newest board event. Will return 'finished' if game is over
    #Blocks program until at least one response is received
    def wait_for_board_event(self):
        response = requests.get(
            f"https://lichess.org/api/board/game/stream/{LichessApi._game_id}",
            headers=self.header,
            stream=True
        )

        return response

    #Will return a list of all moves made in a game from a json response. 
    #If no new moves it will return an empty list
    def parse_moves_from_events(self, response):
        #Each line is a new event that has been appended to the NDJSON
        for line in response.iter_lines():
            #Some lines may be empty for keep alive
            if line:
                event = json.loads(line)
                
                #If there is an event error
                if event.get("error"):
                    continue

                # First event, contains full game info and current moves
                if event["type"] == "gameFull":
                    moves = event["state"]["moves"]

                elif event["type"] == "gameState":
                    moves = event["moves"]

                elif event["type"] == "gameFinish":
                    print("Game is over!")
                    return None

                else:
                    continue

                moves_list = moves.split()
                if len(moves_list) > LichessApi.move_count:
                    return moves_list
                else:
                    continue
        return []

    #Gets the most recent white move in a list of moves
    def get_white_move(self, moves: list[str]) -> str:
        if len(moves) == 1:
            return moves[0]
            
        elif len(moves) % 2 == 1:
            return moves[-1]

        else:
            return moves[-2]

    #Gets the most recent black move in a list of moves
    def get_black_move(self, moves: list[str]) -> str:
        if len(moves) <= 1:
            return "none"

        elif len(moves) % 2  == 0:
            return moves[-1]

        else:
            return moves[-2]
    
    def set_game_id(self, game_id: str):
        LichessApi._game_id = game_id

    def update_move_count(self, move_count: int):
        LichessApi.move_count = move_count


if __name__ == "__main__":
    lichess = LichessApi()
    if lichess.start_game(clock_limit = 600, clock_increment = 5):

        if lichess._player_color == "white":
            lichess.make_move("e2e4")

            black_move = "none"
            while(black_move == "none"):
                moves = lichess.wait_for_board_event()
                black_move = lichess.get_black_move(moves)
            
            print(f"Bot made move: {black_move}")

        else:
            black_move = "none"
            while(black_move == "none"):
                moves = lichess.wait_for_board_event()
                black_move = lichess.get_black_move(moves)

            lichess.make_move("e4")
            
            print(f"Bot made move: {black_move}")


        lichess.resign_game()
