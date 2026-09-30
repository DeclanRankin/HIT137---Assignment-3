import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk

root = tk.Tk()

root.title("HIT137 Image Title Puzzle")
root.geometry("1000x700")
image_label = tk.Label(root)
image_label.pack()

def load_image():
    print("Load button clicked")
    filename = filedialog.askopenfilename(title="Choose an Image", 
                                          filetypes=[("Image Files", "*.jpg;*.jpeg;*.png*.bmp")])
    if filename:
        image = cv2.imread(filename)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (400, 400))
        image = Image.fromarray(image)
        photo = ImageTk.PhotoImage(image)
        image_label.config(image=photo)
        image_label.image = photo

                
load_button = tk.Button(root, text="Load Image", command=load_image)
load_button.pack()

root.mainloop()