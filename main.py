import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Tk
import cv2
from PIL import Image, ImageTk, ImageDraw
import random
selected_tile = None
tiles = []
original_tiles = []
tile_home = []
tile_corners = []
CORRECT_DIRECTION = (0, 1, 2, 3)

root = tk.Tk()

root.title("HIT137 Image Title Puzzle")
root.geometry("1000x700")

grid_size = tk.IntVar(value=3)
grid_frame = tk.Frame(root)
grid_frame.pack(pady=10)

grid_label = tk.Label(grid_frame, text="Grid Size:")
grid_label.pack(side=tk.LEFT)

grid_3 = tk.Radiobutton(grid_frame, text="3x3", variable=grid_size, value=3)
grid_3.pack(side=tk.LEFT)
grid_4 = tk.Radiobutton(grid_frame, text="4x4", variable=grid_size, value=4)
grid_4.pack(side=tk.LEFT)  
grid_5 = tk.Radiobutton(grid_frame, text="5x5", variable=grid_size, value=5)
grid_5.pack(side=tk.LEFT)

move_count = 0
move_label = tk.Label(root, text="Moves: 0")
move_label.pack()

images_frame = tk.Frame(root)
images_frame.pack(pady=10)

image_label = tk.Label(images_frame)
image_label.pack(side=tk.LEFT, padx=10)

puzlle_frame = tk.Frame(images_frame, highlightbackground="gray", highlightcolor="red", highlightthickness=3)
puzlle_frame.pack(side=tk.LEFT, padx=10)


def check_solved():
    return bool(tiles) and all(
        tile_home[i] == i and tile_corners[i] == CORRECT_DIRECTION
        for i in range(len(tiles))
    )

def tile_clicked(index):
    global selected_tile
    global tiles
    global move_count

    puzlle_frame.configure(bg="red", highlightbackground="red")
    print("Tile clicked", index)

    #First tile selection
    if selected_tile is None:
        selected_tile = index
        print("First tile selected:", index)
    #Second tile selection
    else:
        second_tile = index

        if second_tile == selected_tile:
            print("Deselecting Tile")
        else:
            # Swap the two tiles
            tiles[selected_tile], tiles[second_tile] = tiles[second_tile], tiles[selected_tile]        
            tile_home[selected_tile], tile_home[second_tile] = (
                tile_home[second_tile], tile_home[selected_tile]
            )
            tile_corners[selected_tile], tile_corners[second_tile] = (
                tile_corners[second_tile], tile_corners[selected_tile]
            )
            move_count += 1
            move_label.config(text=f"Moves: {move_count}")

            print("Swapping tiles:", selected_tile, "and", second_tile)

            selected_tile = None
            display_tiles()
    if check_solved():
        print("Puzzle solved!")
        messagebox.showinfo("Congratulations!", f"You solved the puzzle in {move_count} moves!")

def rotate_tile_data(index, turns):
    for _ in range(turns):
        tiles[index] = cv2.rotate(
            tiles[index], cv2.ROTATE_90_CLOCKWISE
        )
        a = tile_corners[index]
        tile_corners[index] = (a[3], a[0], a[1], a[2])

def flip_tile_data(index, horizontal):
    tiles[index] = cv2.flip(
        tiles[index], 1 if horizontal else 0
    )

    a = tile_corners[index]
    if horizontal:
        tile_corners[index] = (a[1], a[0], a[3], a[2])
    else:
        tile_corners[index] = (a[3], a[2], a[1], a[0])

def rotate_tile(index):
    global move_count, selected_tile

    rotate_tile_data(index, 1)
    selected_tile = None
    move_count += 1
    move_label.config(text=f"Moves: {move_count}")

    display_tiles()

    if check_solved():
        messagebox.showinfo(
            "Congratulations!",
            f"You solved the puzzle in {move_count} moves!"
        )

def flip_tile(index):
    global move_count, selected_tile

    flip_tile_data(index, True)  # True means horizontal flip.
    selected_tile = None
    move_count += 1
    move_label.config(text=f"Moves: {move_count}")

    display_tiles()

    if check_solved():
        messagebox.showinfo(
            "Congratulations!",
            f"You solved the puzzle in {move_count} moves!"
        )

def on_shift_left_click(event, index):
    flip_tile(index)
    return "break"

def display_tiles():
    #Remove the old buttons
    global tile_frame
    for widget in puzlle_frame.winfo_children():
        widget.destroy()

    tile_photos = []
    for index, tile in enumerate(tiles):
        tile_image = Image.fromarray(tile)
        if tile_home[index] == index and tile_corners[index] == CORRECT_DIRECTION:
            draw = ImageDraw.Draw(tile_image)
            draw.ellipse((4, 4, 27, 27), fill="white", outline="green", width=2)
            draw.line(
                [(9, 15), (14, 20), (22, 10)],
                fill="green",
                width=3
            )
        tile_photo = ImageTk.PhotoImage(tile_image)
        
        tile_photos.append(tile_photo)

        row = index // grid_size.get()
        column = index % grid_size.get()

        # tile_frame = tk.Frame(puzlle_frame,
        #     highlightbackground="gray",
        #     highlightcolor="red",
        #     highlightthickness=3,
        #     bd=0)
        # tile_frame.grid(row=row,column=column)

        tile_button = tk.Button(
            puzlle_frame, 
            image=tile_photo, borderwidth=1, 
            relief="solid", 
            bg="gray",
            bd=0,
            command=lambda i=index: tile_clicked(i))
        tile_button.grid(row=row, column=column)
        tile_button.bind("<Button-3>", lambda event, i=index: rotate_tile(i))
        tile_button.bind(
            "<Shift-Button-1>",
            lambda event, i=index: on_shift_left_click(event, i)
        )
        tile_button.bind(
            "<Shift-ButtonRelease-1>",
            lambda event: "break"
        )
    #Keep reference to the images
    puzlle_frame.tile_photos = tile_photos

def load_image():
    global tile_home, tile_corners
    global tiles
    global selected_tile
    global original_tiles
    global move_count

    selected_tile = None

    move_count = 0
    move_label.config(text="Moves: 0")

    selected_grid_size = grid_size.get()
    print("Select grid size:", selected_grid_size)

    filename = filedialog.askopenfilename(title="Choose an Image", 
                                          filetypes=[("Image Files", "*.jpg;*.jpeg;*.png *.bmp")])
    if filename:
        image = cv2.imread(filename)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        display_size = 450
        tile_size = display_size // selected_grid_size
        image_size = tile_size * selected_grid_size
        image = cv2.resize(image, (image_size , image_size))
        reference_image = cv2.resize(image, (225, 225), interpolation=cv2.INTER_AREA)
        original_photo = ImageTk.PhotoImage(Image.fromarray(reference_image))
        original_photo = ImageTk.PhotoImage(Image.fromarray(image))
        image_label.config(image=original_photo)
        image_label.image = original_photo

        # Split the image into puzzle tiles
        tiles = []
        for row in range(selected_grid_size):
            for column in range(selected_grid_size):
                y1 = row * tile_size
                y2 = y1 + tile_size

                x1 = column * tile_size
                x2 = x1 + tile_size

                tile = image[y1:y2, x1:x2]
                tiles.append(tile)
        print ("number of tiles: ", len(tiles))
        # Save the corrct order of the tiles
        global original_tiles
        original_tiles = [tile.copy() for tile in tiles]
        # Shuffle the puzzle tiles
        tile_home = list(range(len(tiles)))
        tile_corners = [CORRECT_DIRECTION for _ in tiles]

        transformation_count = {
            3: 6,
            4: 12,
            5: 20
        }[selected_grid_size]

        # Ensure every puzzle includes a swap, rotation, and flip.
        kinds = ["swap", "rotate", "flip"]
        kinds += random.choices(
            ["swap", "rotate", "flip"],
            k=transformation_count - 3
        )
        random.shuffle(kinds)

        # Generate all transformations before applying them.
        transformations = []
        for kind in kinds:
            if kind == "swap":
                first, second = random.sample(range(len(tiles)), 2)
                transformations.append(("swap", first, second))

            elif kind == "rotate":
                index = random.randrange(len(tiles))
                turns = random.choice((1, 2, 3))
                transformations.append(("rotate", index, turns))

            else:
                index = random.randrange(len(tiles))
                horizontal = random.choice((True, False))
                transformations.append(("flip", index, horizontal))

        # Apply the generated transformations to the puzzle.
        for kind, first, second in transformations:
            if kind == "swap":
                tiles[first], tiles[second] = tiles[second], tiles[first]
                tile_home[first], tile_home[second] = (
                    tile_home[second], tile_home[first]
                )
                tile_corners[first], tile_corners[second] = (
                    tile_corners[second], tile_corners[first]
                )

            elif kind == "rotate":
                rotate_tile_data(first, second)

            else:
                flip_tile_data(first, second)
        #Display the shuffled puzzle tiles
        display_tiles()
        
                
load_button = tk.Button(root, text="Load Image", command=load_image)
load_button.pack()

root.mainloop()