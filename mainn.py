"""
HIT137 - Assignment 3
Image Tile Puzzle

A loaded image is cut into a grid, scrambled with swap / rotate / flip
transformations, and the player restores it using the mouse.


"""

import random
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw



# Tile

class Tile:
    """One puzzle tile.

    The orientation is stored as (rotation, mirrored) and drawn as
    "rotate first, then mirror horizontally".  Every visual orientation has
    exactly one such representation, so a tile that looks correct is always
    counted as correct, and the player's rotate/flip clicks behave exactly
    as they look on screen.
    """

    _ROTATE_CODES = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }

    def __init__(self, tile_id, image):
        self._tile_id = tile_id
        self._image = image.copy()
        self._rotation = 0
        self._mirrored = False

    # read-only state 
    @property
    def tile_id(self):
        """Index of the position where this tile belongs."""
        return self._tile_id

    @property
    def rotation(self):
        return self._rotation

    @property
    def mirrored(self):
        return self._mirrored

    @property
    def original_image(self):
        return self._image

    # visual operations (applied on top of the current look) 
    def rotate_clockwise(self):
        """Rotate the tile 90 degrees clockwise as seen on screen."""
        # Rotating a mirrored picture clockwise equals turning the
        # underlying (unmirrored) picture anticlockwise.
        step = -90 if self._mirrored else 90
        self._rotation = (self._rotation + step) % 360

    def flip_horizontal(self):
        """Mirror the tile left-to-right as seen on screen."""
        self._mirrored = not self._mirrored

    def flip_vertical(self):
        """Mirror the tile top-to-bottom (= horizontal flip + 180 turn)."""
        self._mirrored = not self._mirrored
        self._rotation = (self._rotation + 180) % 360

    def reset_orientation(self):
        self._rotation = 0
        self._mirrored = False

    def is_correct_orientation(self):
        return self._rotation == 0 and not self._mirrored

    def get_display_image(self):
        """Return the tile image with its current orientation applied."""
        image = self._image
        if self._rotation:
            image = cv2.rotate(image, self._ROTATE_CODES[self._rotation])
        if self._mirrored:
            image = cv2.flip(image, 1)
        return image



# Transformations (inheritance + polymorphism)


class Transformation:
    """Abstract scramble operation.

    ``tiles_needed`` is how many board positions the operation targets.
    """

    name = "transformation"
    tiles_needed = 1

    def apply(self, puzzle, positions):
        raise NotImplementedError("Subclasses must implement apply().")


class SwapTransformation(Transformation):
    name = "swap"
    tiles_needed = 2

    def apply(self, puzzle, positions):
        puzzle.swap_tiles(positions[0], positions[1])


class RotateTransformation(Transformation):
    name = "rotate"

    def apply(self, puzzle, positions):
        for _ in range(random.choice([1, 2, 3])):      # 90, 180 or 270
            puzzle.rotate_tile(positions[0])


class FlipTransformation(Transformation):
    name = "flip"

    def apply(self, puzzle, positions):
        if random.choice([True, False]):
            puzzle.flip_tile_horizontal(positions[0])
        else:
            puzzle.flip_tile_vertical(positions[0])



# Puzzle model


class Puzzle:
    """Game state and rules (no GUI code)."""

    DISPLAY_SIZE = 450
    MAX_HINTS = 3
    TRANSFORMATION_COUNTS = {3: 6, 4: 12, 5: 20}
    DIFFICULTY_MULTIPLIER = {"Easy": 0.75, "Standard": 1.0, "Hard": 1.25}
    SECONDS_PER_TILE = {"Easy": 30, "Standard": 20, "Hard": 12}

    def __init__(self, image, grid_size, difficulty="Standard"):
        if grid_size not in self.TRANSFORMATION_COUNTS:
            raise ValueError("Grid size must be 3, 4 or 5.")
        self._grid_size = grid_size
        self._difficulty = difficulty
        self._image = self._prepare_image(image)
        self._tiles = self._create_tiles()
        self._move_count = 0
        self._hints_used = 0
        self._completed = False
        self._timed_out = False
        self._transformations = [
            SwapTransformation(),
            RotateTransformation(),
            FlipTransformation(),
        ]
        self.applied_transformations = 0
        self.scramble()

    # read-only state 
    @property
    def grid_size(self):
        return self._grid_size

    @property
    def tile_size(self):
        return self.DISPLAY_SIZE // self._grid_size

    @property
    def image(self):
        return self._image

    @property
    def tiles(self):
        return tuple(self._tiles)

    @property
    def move_count(self):
        return self._move_count

    @property
    def hints_used(self):
        return self._hints_used

    @property
    def completed(self):
        return self._completed

    @property
    def timed_out(self):
        return self._timed_out

    @property
    def is_active(self):
        """True while the puzzle accepts player input."""
        return not self._completed and not self._timed_out

    @property
    def time_limit(self):
        """Seconds allowed for this puzzle (depends on difficulty and grid)."""
        per_tile = self.SECONDS_PER_TILE.get(self._difficulty, 20)
        return per_tile * self._grid_size ** 2

    # -- image preparation --------------------------------------------------
    def _prepare_image(self, image):
        """Resize without distortion, then centre-crop so the grid divides evenly."""
        final_size = (self.DISPLAY_SIZE // self._grid_size) * self._grid_size

        height, width = image.shape[:2]
        if height == 0 or width == 0:
            raise ValueError("Image has invalid dimensions.")

        scale = max(final_size / width, final_size / height)
        new_width = max(final_size, int(round(width * scale)))
        new_height = max(final_size, int(round(height * scale)))
        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR,
        )

        x1 = (new_width - final_size) // 2
        y1 = (new_height - final_size) // 2
        return resized[y1:y1 + final_size, x1:x1 + final_size].copy()

    def _create_tiles(self):
        size = self._image.shape[0] // self._grid_size
        tiles = []
        for row in range(self._grid_size):
            for column in range(self._grid_size):
                y1, x1 = row * size, column * size
                tile_image = self._image[y1:y1 + size, x1:x1 + size]
                tiles.append(Tile(row * self._grid_size + column, tile_image))
        return tiles

    # scrambling 
    def scramble(self):
        """Apply the full set of transformations at once.

        The number of operations scales with grid size and difficulty.  Every
        board position is targeted by at most one operation, and all three
        transformation types always appear.
        """
        base = self.TRANSFORMATION_COUNTS[self._grid_size]
        multiplier = self.DIFFICULTY_MULTIPLIER.get(self._difficulty, 1.0)
        # A swap needs two tiles, so at most (tiles - 1) operations can fit.
        count = min(max(3, int(round(base * multiplier))), len(self._tiles) - 1)

        # Plan: one of each type, then random extras that still fit the board.
        plan = list(self._transformations)
        budget = len(self._tiles) - sum(t.tiles_needed for t in plan)
        while len(plan) < count:
            still_needed = count - len(plan) - 1      # ops left after this one
            options = [
                t for t in self._transformations
                if budget - t.tiles_needed >= still_needed
            ]
            if not options:
                break
            choice = random.choice(options)
            plan.append(choice)
            budget -= choice.tiles_needed
        random.shuffle(plan)

        available = list(range(len(self._tiles)))
        random.shuffle(available)
        for transformation in plan:
            positions = [available.pop() for _ in range(transformation.tiles_needed)]
            transformation.apply(self, positions)    # polymorphic call
        self.applied_transformations = len(plan)

        if self.is_solved():                         # safety net
            self.swap_tiles(0, 1)

    # tile operations (do not count as moves)
    def swap_tiles(self, first, second):
        self._tiles[first], self._tiles[second] = (
            self._tiles[second],
            self._tiles[first],
        )

    def rotate_tile(self, index):
        self._tiles[index].rotate_clockwise()

    def flip_tile_horizontal(self, index):
        self._tiles[index].flip_horizontal()

    def flip_tile_vertical(self, index):
        self._tiles[index].flip_vertical()

    #  rules 
    def tile_is_correct(self, position):
        tile = self._tiles[position]
        return tile.tile_id == position and tile.is_correct_orientation()

    def incorrect_positions(self):
        return [p for p in range(len(self._tiles)) if not self.tile_is_correct(p)]

    def incorrect_count(self):
        return len(self.incorrect_positions())

    def is_solved(self):
        return self.incorrect_count() == 0

    def register_move(self):
        """Count one player move and detect completion."""
        self._move_count += 1
        if self.is_solved():
            self._completed = True

    def expire(self):
        """Called when the time limit runs out."""
        if not self._completed:
            self._timed_out = True

    def use_hint(self):
        """Return (current_position, home_position) of an incorrect tile."""
        if self._hints_used >= self.MAX_HINTS or not self.is_active:
            return None
        incorrect = self.incorrect_positions()
        if not incorrect:
            return None
        current = random.choice(incorrect)
        self._hints_used += 1
        return current, self._tiles[current].tile_id

    def solve(self):
        """Undo every transformation and clear the move count."""
        self._tiles.sort(key=lambda tile: tile.tile_id)
        for tile in self._tiles:
            tile.reset_orientation()
        self._move_count = 0
        self._completed = True



# Tkinter application


class ImagePuzzleApp:
    BLUE = (0, 90, 255)

    def __init__(self, root):
        self.root = root
        self.root.title("HIT137 Image Tile Puzzle")
        self.root.geometry("1050x760")
        self.root.minsize(950, 700)

        self.grid_size = tk.IntVar(value=3)
        self.difficulty = tk.StringVar(value="Standard")
        self.puzzle = None
        self.selected_tile = None
        self.hint_current = None
        self.hint_home = None
        self.time_left = 0
        self._timer_id = None

        self.original_photo = None
        self.puzzle_photo = None

        self._build_interface()

    # layout 
    def _build_interface(self):
        tk.Label(
            self.root, text="Image Tile Puzzle", font=("Arial", 18, "bold")
        ).pack(pady=(12, 5))

        controls = tk.Frame(self.root)
        controls.pack(pady=5)

        tk.Label(controls, text="Grid Size:").pack(side=tk.LEFT, padx=(0, 5))
        for size in (3, 4, 5):
            tk.Radiobutton(
                controls, text=f"{size}x{size}",
                variable=self.grid_size, value=size,
            ).pack(side=tk.LEFT)

        tk.Label(controls, text="Difficulty:").pack(side=tk.LEFT, padx=(15, 5))
        tk.OptionMenu(
            controls, self.difficulty, "Easy", "Standard", "Hard"
        ).pack(side=tk.LEFT)

        self.load_button = tk.Button(
            controls, text="Load Image", command=self.load_image, width=12
        )
        self.load_button.pack(side=tk.LEFT, padx=(15, 5))

        self.hint_button = tk.Button(
            controls, text="Hint", command=self.show_hint,
            state=tk.DISABLED, width=8,
        )
        self.hint_button.pack(side=tk.LEFT, padx=5)

        self.solve_button = tk.Button(
            controls, text="Solve", command=self.solve_puzzle,
            state=tk.DISABLED, width=8,
        )
        self.solve_button.pack(side=tk.LEFT, padx=5)

        status = tk.Frame(self.root)
        status.pack(pady=5)
        self.move_label = tk.Label(status, text="Moves: 0", width=14)
        self.move_label.pack(side=tk.LEFT)
        self.incorrect_label = tk.Label(status, text="Incorrect tiles: 0", width=18)
        self.incorrect_label.pack(side=tk.LEFT)
        self.hint_label = tk.Label(status, text="Hints: 0/3", width=14)
        self.hint_label.pack(side=tk.LEFT)
        self.timer_label = tk.Label(status, text="Time: --:--", width=14)
        self.timer_label.pack(side=tk.LEFT)

        headings = tk.Frame(self.root)
        headings.pack()
        for text in ("Original Image", "Puzzle"):
            tk.Label(
                headings, text=text, font=("Arial", 11, "bold"), width=48
            ).pack(side=tk.LEFT)

        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        size = Puzzle.DISPLAY_SIZE
        self.original_canvas = self._make_canvas(frame, size)
        self.puzzle_canvas = self._make_canvas(frame, size)

        self.puzzle_canvas.bind("<Button-1>", self.left_click)
        self.puzzle_canvas.bind("<Button-3>", self.right_click)
        self.puzzle_canvas.bind("<Button-2>", self.right_click)   # macOS
        self.puzzle_canvas.bind("<Shift-Button-1>", self.shift_left_click)

        tk.Label(
            self.root,
            text=("Left click: select/swap   |   Right click: rotate 90°   |   "
                  "Shift + left click: flip horizontally"),
        ).pack(pady=(5, 0))

    @staticmethod
    def _make_canvas(parent, size):
        canvas = tk.Canvas(
            parent, width=size, height=size, bg="white",
            highlightthickness=1, highlightbackground="gray",
        )
        canvas.pack(side=tk.LEFT, padx=10)
        return canvas

    # loading 
    def load_image(self):
        filename = filedialog.askopenfilename(
            title="Choose an Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("BMP files", "*.bmp"),
            ],
        )
        if not filename:                       # dialog cancelled
            return

        try:
            # imdecode also copes with non-ASCII paths on Windows
            data = np.fromfile(filename, dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except OSError:
            image = None

        if image is None:
            messagebox.showerror(
                "Image Error", "The selected file is not a readable image."
            )
            return

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        try:
            puzzle = Puzzle(image, self.grid_size.get(), self.difficulty.get())
        except (ValueError, cv2.error) as error:
            messagebox.showerror("Image Error", f"Could not build puzzle: {error}")
            return

        # Full reset for the new round
        self._stop_timer()
        self.puzzle = puzzle
        self.selected_tile = None
        self.hint_current = None
        self.hint_home = None
        self.time_left = puzzle.time_limit

        self.update_display()
        self._tick()

    # timer 
    def _stop_timer(self):
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None

    def _tick(self):
        self._timer_id = None
        if self.puzzle is None or not self.puzzle.is_active:
            return
        minutes, seconds = divmod(self.time_left, 60)
        self.timer_label.config(text=f"Time: {minutes}:{seconds:02d}")
        if self.time_left <= 0:
            self.puzzle.expire()
            self.selected_tile = None
            self.hint_current = None
            self.hint_home = None
            self.update_display()
            messagebox.showinfo(
                "Time's up!", "You ran out of time. Press Solve to see the answer."
            )
            return
        self.time_left -= 1
        self._timer_id = self.root.after(1000, self._tick)

    # mouse handling 
    def _event_to_index(self, event):
        if self.puzzle is None:
            return None
        size = self.puzzle.grid_size
        tile_size = self.puzzle.tile_size
        if event.x < 0 or event.y < 0:
            return None
        column, row = event.x // tile_size, event.y // tile_size
        if row >= size or column >= size:      # click outside the image
            return None
        return row * size + column

    def _accepts_input(self):
        return self.puzzle is not None and self.puzzle.is_active

    def left_click(self, event):
        if not self._accepts_input():
            return
        index = self._event_to_index(event)
        if index is None:
            return

        if self.selected_tile is None:
            self.selected_tile = index
            self.update_display()
        elif self.selected_tile == index:
            self.selected_tile = None
            self.update_display()
        else:
            self.puzzle.swap_tiles(self.selected_tile, index)
            self.selected_tile = None
            self._after_player_move()

    def right_click(self, event):
        if not self._accepts_input():
            return
        index = self._event_to_index(event)
        if index is None:
            return
        self.puzzle.rotate_tile(index)
        self.selected_tile = None
        self._after_player_move()

    def shift_left_click(self, event):
        if self._accepts_input():
            index = self._event_to_index(event)
            if index is not None:
                self.puzzle.flip_tile_horizontal(index)
                self.selected_tile = None
                self._after_player_move()
        return "break"

    def _after_player_move(self):
        self.puzzle.register_move()
        self.hint_current = None               # hints vanish after a move
        self.hint_home = None
        self.update_display()
        if self.puzzle.completed:
            self._stop_timer()
            messagebox.showinfo(
                "Congratulations!",
                f"You solved the puzzle in {self.puzzle.move_count} moves!",
            )

    #  buttons 
    def show_hint(self):
        if not self._accepts_input():
            return
        result = self.puzzle.use_hint()
        if result is None:
            return
        self.hint_current, self.hint_home = result
        self.update_display()

    def solve_puzzle(self):
        if self.puzzle is None or self.puzzle.completed:
            return
        self._stop_timer()
        self.puzzle.solve()
        self.selected_tile = None
        self.hint_current = None
        self.hint_home = None
        self.update_display()
        messagebox.showinfo("Puzzle Solved", "The puzzle has been restored.")

    #  drawing 
    def update_display(self):
        if self.puzzle is None:
            return
        self._draw_original()
        self._draw_puzzle()
        self._update_status()

    def _draw_grid(self, draw, size, tile_size, extent, colour):
        for i in range(1, size):
            p = i * tile_size
            draw.line([(p, 0), (p, extent)], fill=colour, width=1)
            draw.line([(0, p), (extent, p)], fill=colour, width=1)

    def _draw_circle(self, draw, position, size, tile_size):
        row, column = divmod(position, size)
        cx = column * tile_size + tile_size // 2
        cy = row * tile_size + tile_size // 2
        r = max(12, tile_size // 6)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=self.BLUE, width=5)

    def _draw_original(self):
        size = self.puzzle.grid_size
        tile_size = self.puzzle.tile_size
        image = Image.fromarray(self.puzzle.image.copy())
        draw = ImageDraw.Draw(image)
        self._draw_grid(draw, size, tile_size, image.width, (190, 190, 190))
        if self.hint_home is not None:
            self._draw_circle(draw, self.hint_home, size, tile_size)

        self.original_photo = ImageTk.PhotoImage(image)
        self.original_canvas.delete("all")
        self.original_canvas.create_image(0, 0, anchor=tk.NW, image=self.original_photo)

    def _draw_puzzle(self):
        puzzle = self.puzzle
        size = puzzle.grid_size
        tile_size = puzzle.tile_size
        board_size = Puzzle.DISPLAY_SIZE

        board = Image.new("RGB", (board_size, board_size), "white")
        for position, tile in enumerate(puzzle.tiles):
            row, column = divmod(position, size)
            board.paste(
                Image.fromarray(tile.get_display_image()),
                (column * tile_size, row * tile_size),
            )

        draw = ImageDraw.Draw(board)
        self._draw_grid(draw, size, tile_size, board_size, (170, 170, 170))

        for position in range(len(puzzle.tiles)):         # green ticks
            if puzzle.tile_is_correct(position):
                row, column = divmod(position, size)
                x = column * tile_size + tile_size - 25
                y = row * tile_size + 8
                draw.line(
                    [(x, y + 8), (x + 6, y + 14), (x + 17, y)],
                    fill=(0, 180, 0), width=4,
                )

        if self.selected_tile is not None:                # selection border
            row, column = divmod(self.selected_tile, size)
            draw.rectangle(
                [column * tile_size + 2, row * tile_size + 2,
                 (column + 1) * tile_size - 3, (row + 1) * tile_size - 3],
                outline=(255, 140, 0), width=5,
            )

        if self.hint_current is not None:
            self._draw_circle(draw, self.hint_current, size, tile_size)

        self.puzzle_photo = ImageTk.PhotoImage(board)
        self.puzzle_canvas.delete("all")
        self.puzzle_canvas.create_image(0, 0, anchor=tk.NW, image=self.puzzle_photo)

    def _update_status(self):
        puzzle = self.puzzle
        self.move_label.config(text=f"Moves: {puzzle.move_count}")
        self.incorrect_label.config(text=f"Incorrect tiles: {puzzle.incorrect_count()}")
        self.hint_label.config(text=f"Hints: {puzzle.hints_used}/{Puzzle.MAX_HINTS}")

        can_hint = puzzle.is_active and puzzle.hints_used < Puzzle.MAX_HINTS
        self.hint_button.config(state=tk.NORMAL if can_hint else tk.DISABLED)
        self.solve_button.config(
            state=tk.DISABLED if puzzle.completed else tk.NORMAL
        )
        if puzzle.completed:
            self.timer_label.config(text="Time: --:--")


def main():
    root = tk.Tk()
    ImagePuzzleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
