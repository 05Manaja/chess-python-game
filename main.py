import tkinter as tk
import copy
from tkinter import messagebox, simpledialog



SIZE = 80
ANIMATION_STEPS = 8
ANIMATION_DELAY = 15

class ChessGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Échecs Pro")

        self.player_names = {"white": "Joueur 1", "black": "Joueur 2"}
        self.initial_time = 600
        
        self.blink_state = False
 
        self.setup_menu()

    def setup_menu(self):
        self.menu_frame = tk.Frame(self.root, bg="#2c3e50", padx=50, pady=50)
        self.menu_frame.pack(fill="both", expand=True)

        tk.Label(self.menu_frame, text="CHESS PRO", font=("Helvetica", 24, "bold"), fg="#ecf0f1", bg="#2c3e50").pack(pady=20)

     
        tk.Label(self.menu_frame, text="Nom Joueur Blanc :", fg="white", bg="#2c3e50").pack()
        self.ent_white = tk.Entry(self.menu_frame)
        self.ent_white.insert(0, "Blanc")
        self.ent_white.pack(pady=5)

        tk.Label(self.menu_frame, text="Nom Joueur Noir :", fg="white", bg="#2c3e50").pack()
        self.ent_black = tk.Entry(self.menu_frame)
        self.ent_black.insert(0, "Noir")
        self.ent_black.pack(pady=5)
  

        tk.Label(self.menu_frame, text="Cadence (minutes) :", fg="white", bg="#2c3e50").pack()
        self.time_var = tk.IntVar(value=10)
        tk.Scale(self.menu_frame, from_=1, to=60, orient="horizontal", variable=self.time_var, bg="#2c3e50", fg="white").pack(pady=10)

        tk.Button(self.menu_frame, text="COMMENCER LE MATCH", command=self.start_game, bg="#27ae60", fg="white", font=("bold")).pack(pady=20)

    def start_game(self):
        self.player_names["white"] = self.ent_white.get()
        self.player_names["black"] = self.ent_black.get()
        self.initial_time = self.time_var.get() * 60
        self.menu_frame.destroy()
        self.init_game_ui()

    def init_game_ui(self):
        self.main_frame = tk.Frame(self.root, bg="#2c3e50")
        self.main_frame.pack(fill="both", expand=True)

        self.timers = {"white": self.initial_time, "black": self.initial_time}
        self.label_black = tk.Label(self.main_frame, text="", font=("Consolas", 20, "bold"), fg="white", bg="#2c3e50")
        self.label_black.pack(pady=5)

        self.canvas = tk.Canvas(self.main_frame, width=640, height=640, highlightthickness=0)
        self.canvas.pack(pady=5)

        self.label_white = tk.Label(self.main_frame, text="", font=("Consolas", 20, "bold"), fg="white", bg="#2c3e50")
        self.label_white.pack(pady=5)

        self.board = self.create_board()
        self.images = {}
        self.load_images()
        
        self.turn = "white"
        self.selected = None
        self.en_passant = None
        self.game_over = False
        self.animating = False

        self.king_moved = {"white": False, "black": False}
        self.rook_moved = {"white_left": False, "white_right": False, "black_left": False, "black_right": False}

        self.canvas.bind("<Button-1>", self.click)
        self.update_clock()
        self.blink_king()  
        self.draw()

    def create_board(self):
        return [
            ["br","bn","bb","bq","bk","bb","bn","br"],
            ["bp","bp","bp","bp","bp","bp","bp","bp"],
            ["","","","","","","",""], ["","","","","","","",""],
            ["","","","","","","",""], ["","","","","","","",""],
            ["wp","wp","wp","wp","wp","wp","wp","wp"],
            ["wr","wn","wb","wq","wk","wb","wn","wr"]
        ]

    def load_images(self):
        pieces = ["wp","wr","wn","wb","wq","wk","bp","br","bn","bb","bq","bk"]
        for p in pieces:
            try: self.images[p] = tk.PhotoImage(file=f"images/{p}.png")
            except: pass

    def blink_king(self):
        """ Gère l'alternance de couleur pour le roi en échec """
        if not self.game_over:
            self.blink_state = not self.blink_state
            self.draw()


            self.root.after(500, self.blink_king)

    def draw(self, moving_piece=None, anim_pos=None):
        self.canvas.delete("all")

        king_in_check_pos = None
        if self.in_check(self.board, self.turn):
            for r in range(8):
                for c in range(8):
                    if self.board[r][c] == self.turn[0] + "k":
                        king_in_check_pos = (r, c)

        for r in range(8):
            for c in range(8):
                color = "#EEEED2" if (r+c)%2==0 else "#769656"
                

                if king_in_check_pos == (r, c) and self.blink_state:
                    color = "#e74c3c"
                
                self.canvas.create_rectangle(c*SIZE, r*SIZE, (c+1)*SIZE, (r+1)*SIZE, fill=color, outline="")
                
                if moving_piece and (r, c) == moving_piece['start']: continue
                p = self.board[r][c]
                if p in self.images:
                    self.canvas.create_image(c*SIZE, r*SIZE, anchor="nw", image=self.images[p])

        if self.selected:
            r, c = self.selected
            self.canvas.create_rectangle(c*SIZE, r*SIZE, (c+1)*SIZE, (r+1)*SIZE, outline="#3498db", width=4)

        if moving_piece and anim_pos:
            self.canvas.create_image(anim_pos[0], anim_pos[1], anchor="nw", image=self.images[moving_piece['p']])

    def animate(self, start, end, p_type):
        self.animating = True
        x1, y1 = start[1]*SIZE, start[0]*SIZE
        x2, y2 = end[1]*SIZE, end[0]*SIZE
        dx, dy = (x2-x1)/ANIMATION_STEPS, (y2-y1)/ANIMATION_STEPS
        def step(i):
            if i <= ANIMATION_STEPS:
                self.draw(moving_piece={'start': start, 'p': p_type}, anim_pos=(x1+dx*i, y1+dy*i))
                self.root.after(ANIMATION_DELAY, lambda: step(i+1))
            else:
                self.animating = False
                self.finalize_move(start, end)
        step(0)

    def click(self, event):
        if self.game_over or self.animating: return
        c, r = event.x // SIZE, event.y // SIZE
        if not (0 <= r < 8 and 0 <= c < 8): return
        if self.selected:
            if self.is_legal(self.selected, (r, c)):
                self.animate(self.selected, (r, c), self.board[self.selected[0]][self.selected[1]])
            self.selected = None
        else:
            if self.board[r][c] and self.board[r][c][0] == self.turn[0]:
                self.selected = (r, c)
        self.draw()

    def is_legal(self, start, end):
        if not self.valid_rules(self.board, start, end): return False
        temp_board = copy.deepcopy(self.board)
        self.apply_logic(temp_board, start, end)
        if self.in_check(temp_board, self.turn): return False
        return True

    def valid_rules(self, board, start, end):
        r1, c1 = start
        r2, c2 = end
        p = board[r1][c1]
        t = board[r2][c2]
        if t and t[0] == p[0]: return False
        dr, dc = r2 - r1, c2 - c1

        if p[1] == "p":
            direction = -1 if p[0] == "w" else 1
            if dc == 0 and t == "":
                if dr == direction: return True
                if dr == 2*direction and r1 == (6 if p[0] == "w" else 1):
                    return board[r1+direction][c1] == ""
            if abs(dc) == 1 and dr == direction:
                if t != "" or (r2, c2) == self.en_passant: return True
            return False

        if p[1] in "rbq":
            if p[1] == "r" and not (dr == 0 or dc == 0): return False
            if p[1] == "b" and not (abs(dr) == abs(dc)): return False
            if p[1] == "q" and not (dr == 0 or dc == 0 or abs(dr) == abs(dc)): return False
            sr = 0 if dr == 0 else (1 if dr > 0 else -1)
            sc = 0 if dc == 0 else (1 if dc > 0 else -1)
            cr, cc = r1 + sr, c1 + sc
            while (cr, cc) != (r2, c2):
                if board[cr][cc] != "": return False
                cr += sr; cc += sc
            return True

        if p[1] == "n": return (abs(dr), abs(dc)) in [(2,1), (1,2)]

        if p[1] == "k":
            if abs(dr) <= 1 and abs(dc) <= 1: return True
            if abs(dc) == 2 and dr == 0:
                if self.king_moved[self.turn] or self.in_check(board, self.turn): return False
                step_c = 1 if dc > 0 else -1
                for i in range(1, 3):
                    if board[r1][c1+i*step_c] != "" or self.square_attacked(board, (r1, c1+i*step_c), self.turn): return False
                side = "right" if dc > 0 else "left"
                if self.rook_moved[f"{self.turn}_{side}"]: return False
                return True
        return False


    def square_attacked(self, board, pos, color):
        enemy = "black" if color == "white" else "white"
        for r in range(8):
            for c in range(8):
                if board[r][c] and board[r][c][0] == enemy[0]:
                    if self.valid_rules(board, (r, c), pos): return True
        return False

    def in_check(self, board, color):
        k_pos = None
        for r in range(8):
            for c in range(8):
                if board[r][c] == color[0] + "k": k_pos = (r, c)
        return self.square_attacked(board, k_pos, color) if k_pos else False

    def apply_logic(self, board, start, end, is_real_move=False):
        r1, c1 = start
        r2, c2 = end
        p = board[r1][c1]

        if p[1] == "p" and abs(c1-c2) == 1 and board[r2][c2] == "": board[r1][c2] = ""
        board[r2][c2] = p
        board[r1][c1] = ""

        if p[1] == "p" and (r2 == 0 or r2 == 7):
            if is_real_move:
                choice = simpledialog.askstring("Promotion", "Choisissez: Q, R, B, or N", initialvalue="Q")
                choice = choice.lower()[0] if choice else "q"
                if choice not in "qrbn": choice = "q"
                board[r2][c2] = p[0] + choice
            else:
                board[r2][c2] = p[0] + "q"

        if p[1] == "k" and abs(c1-c2) == 2:
            if c2 == 6: board[r1][5], board[r1][7] = board[r1][7], ""
            else: board[r1][3], board[r1][0] = board[r1][0], ""

    def finalize_move(self, start, end):
        p = self.board[start[0]][start[1]]
        self.en_passant = ((start[0]+end[0])//2, start[1]) if p[1]=="p" and abs(start[0]-end[0])==2 else None
        
        if p == "wk": self.king_moved["white"] = True
        if p == "bk": self.king_moved["black"] = True
        if p == "wr":
            if start == (7,0): self.rook_moved["white_left"] = True
            if start == (7,7): self.rook_moved["white_right"] = True
        if p == "br":
            if start == (0,0): self.rook_moved["black_left"] = True
            if start == (0,7): self.rook_moved["black_right"] = True

        self.apply_logic(self.board, start, end, is_real_move=True)
        self.turn = "black" if self.turn == "white" else "white"


        self.blink_state = True
        self.draw()
        self.check_end_game()

    def check_end_game(self):
        moves = []
        for r in range(8):
            for c in range(8):
                if self.board[r][c] and self.board[r][c][0] == self.turn[0]:
                    for tr in range(8):
                        for tc in range(8):
                            if self.is_legal((r, c), (tr, tc)): moves.append(1)
        
        if not moves:
            self.game_over = True
            if self.in_check(self.board, self.turn):
                winner_color = "black" if self.turn == "white" else "white"
                winner_name = self.player_names[winner_color]
                messagebox.showinfo("MAT", f"Échec et Mat !\n{winner_name} a gagné !")
            else:
                messagebox.showinfo("PAT", "Match nul par Pat.")

    def update_clock(self):
        if not self.game_over:
            self.timers[self.turn] -= 1
            if self.timers[self.turn] <= 0:
                self.game_over = True
                winner = self.player_names["black" if self.turn == "white" else "white"]
                messagebox.showinfo("Temps", f"Temps écoulé ! {winner} a gagné !")
            
            for color, label in [("white", self.label_white), ("black", self.label_black)]:
                m, s = divmod(self.timers[color], 60)
                label.config(text=f"{self.player_names[color].upper()}: {m:02d}:{s:02d}")
            self.root.after(1000, self.update_clock)

if __name__ == "__main__":
    root = tk.Tk()
    ChessGame(root)
    root.mainloop()