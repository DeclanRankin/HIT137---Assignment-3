import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import random
selected_tile = None
tiles = []
original_tiles = []

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

image_label = tk.Label(root)
image_label.pack()

move_count = 0
move_label = tk.Label(root, text="Moves: 0")
move_label.pack()

puzlle_frame = tk.Frame()
puzlle_frame.pack()

def check_solved():
    for i in range(len(tiles)):
        if not (tiles[i] == original_tiles[i]).all():
            return False
    return True

def tile_clicked(index):
    global selected_tile
    global tiles
    global move_count

    print("Tile clicked", index)

    #First tile selection
    if selected_tile is None:
        selected_tile = index
        print("First tile selected:", index)
    #Second tile selection
    else:
        second_tile = index
       
        # Swap the two tiles
        tiles[selected_tile], tiles[second_tile] = tiles[second_tile], tiles[selected_tile]        
        move_count += 1
        move_label.config(text=f"Moves: {move_count}")

        print("Swapping tiles:", selected_tile, "and", second_tile)

        selected_tile = None
        display_tiles()
    if check_solved():
        print("Puzzle solved!")
        messagebox.showinfo("Congratulations!", f"You solved the puzzle in {move_count} moves!")

def display_tiles():
    #Remove the old buttons
    for widget in puzlle_frame.winfo_children():
        widget.destroy()

    tile_photos = []
    for index, tile in enumerate(tiles):
        tile_image = Image.fromarray(tile)
        tile_photo = ImageTk.PhotoImage(tile_image)
        
        tile_photos.append(tile_photo)

        row = index // grid_size.get()
        column = index % grid_size.get()

        tile_button = tk.Button(puzlle_frame, image=tile_photo, borderwidth=1, relief="solid", command=lambda i=index: tile_clicked(i))
        tile_button.grid(row=row, column=column)
    #Keep reference to the images
    puzlle_frame.tile_photos = tile_photos

def load_image():
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
                                          filetypes=[("Image Files", "*.jpg;*.jpeg;*.png*.bmp")])
    if filename:
        image = cv2.imread(filename)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        display_size = 450
        tile_size = display_size // selected_grid_size
        image_size = tile_size * selected_grid_size
        image = cv2.resize(image, (image_size , image_size))

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
        random.shuffle(tiles)
        #Display the shuffled puzzle tiles
        display_tiles()
                
load_button = tk.Button(root, text="Load Image", command=load_image)
load_button.pack()

root.mainloop()
