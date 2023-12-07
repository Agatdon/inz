import tkinter as tk
from tkinter import *
import cv2
import numpy as np

import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps  # Do obsługi obrazów

import cv2
from PIL import Image

# Zmienna globalna przechowująca obraz
global_image = None


def open_image():
    global global_image, canvas
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.ppm *.pgm *.tif *.tiff")])
    if file_path:
        # Wczytaj obraz przy użyciu Pillow
        img_pillow = Image.open(file_path)
        # Przekształć obraz na format obsługiwany przez OpenCV (BGR)
        img_cv2 = cv2.cvtColor(np.array(img_pillow), cv2.COLOR_RGB2BGR)
        global_image = img_cv2
        # Wyświetl obraz na płótnie
        widthx, heighty = img_cv2.shape[1], img_cv2.shape[0]
        photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)))
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo
        # Dostosuj rozmiar Canvas do rozmiaru obrazu

        if widthx <= 1366 and heighty <= 768:
            # Jeśli jest mniejszy, dostosuj Canvas do rozmiaru obrazu
            canvas.config(width=widthx, height=heighty)
        else:
            # Jeśli jest większy, dostosuj Canvas do maksymalnego rozmiaru 1000x500
            scaled_image = cv2.resize(img_cv2, (1366, 768))
            photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(scaled_image, cv2.COLOR_BGR2RGB)))
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.image = photo
            canvas.config(width=1366, height=768)
            img_cv2 = scaled_image

        rotate_left_button.configure(state=tk.NORMAL)  # Włącz przycisk "Obróć w lewo"
        x= rotate_left_button.configure(command=lambda: rotate_left)  # Przypisz funkcję rotate_left jako obsługę przycisku
        # Progowanie
        threshold_button.configure(state=tk.NORMAL)  # Włącz przycisk przetwarzania
        threshold_button.configure(command=lambda: threshold_image(x, number_slider.get()))  # Przypisz funkcję threshold_image jako obsługę przycisku


def rotate_left():
    global global_image, canvas
    if global_image is not None:
        # Obróć obraz o 90 stopni w lewo
        rotated_image = cv2.rotate(global_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        global_image = rotated_image
        # Wyświetl obrócony obraz na płótnie
        rotated_photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(rotated_image, cv2.COLOR_BGR2RGB)))
        canvas.create_image(0, 0, anchor="nw", image=rotated_photo)
        canvas.image = rotated_photo
        canvas.config(width=rotated_image.shape[1], height=rotated_image.shape[0])
        return rotated_photo

def rotate_right():
    global global_image, canvas
    if global_image is not None:
        # Obróć obraz o 90 stopni w lewo
        rotated_image = cv2.rotate(global_image, cv2.ROTATE_90_CLOCKWISE)
        global_image = rotated_image
        # Wyświetl obrócony obraz na płótnie
        rotated_photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(rotated_image, cv2.COLOR_BGR2RGB)))
        canvas.create_image(0, 0, anchor="nw", image=rotated_photo)
        canvas.image = rotated_photo
        canvas.config(width=rotated_image.shape[1], height=rotated_image.shape[0])
        return rotated_photo


def threshold_image(img, threshold):
    global global_image  # Użyj zmiennej globalnej, aby uzyskać dostęp do obrazu
    # img = global_image

    # Przekształć obraz na odcienie szarości
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    # Oblicz histogram obrazu
    histogram = cv2.calcHist([gray_image], [0], None, [256], [0, 256])

    # Normalizacja histogramu
    histogram = histogram / (gray_image.shape[0] * gray_image.shape[1])

    # Metoda Otsu do automatycznego wyznaczenia progu
    variance = []
    for t in range(256):
        w0 = sum(histogram[0:t])
        w1 = sum(histogram[t:255])
        m0 = sum([i * histogram[i] for i in range(0, t)]) / (w0 + 1e-10)
        m1 = sum([i * histogram[i] for i in range(t, 256)]) / (w1 + 1e-10)
        variance.append(w0 * w1 * (m0 - m1) ** 2)

    optimal_threshold = np.argmax(variance)
    print(f"Próg "+str(optimal_threshold))

    # Progowanie obrazu na podstawie wybranego progu
    thresholded_image = cv2.threshold(gray_image, threshold, 255, cv2.ADAPTIVE_THRESH_MEAN_C)[1]

    # Progowanie
    #_, thresholded_image = cv2.threshold(gray_image, average_brightness, 255, cv2.THRESH_BINARY)
    #_, thresholded_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Inicjalizuj obraz segmentacji
    segmented_image = np.zeros_like(thresholded_image)

    edges = cv2.Canny(gray_image, 100, 200)

    # Przekształć obraz na format obsługiwany przez Tkinter i Canvas
    img_pil = Image.fromarray(thresholded_image)
    img_tk = ImageTk.PhotoImage(img_pil)

    # Wyświetl obraz na płótnie
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.image = img_tk  # Ważne, aby zachować referencję, aby uniknąć problemów z zarządzaniem pamięcią
    global_image=img_tk

def threshold_image_1(img, threshold):
    global global_image  # Użyj zmiennej globalnej, aby uzyskać dostęp do obrazu
    # Przekształć obraz na odcienie szarości
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Znajdź kontury elementów na obrazie
    contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Inicjalizuj listę intensywności pikseli dla wszystkich elementów
    intensities = []

    # Dla każdego znalezionego elementu
    for contour in contours:
        # Twórz maskę tylko z aktualnym elementem
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

        # Wyodrębnij tylko piksele z elementu
        pixels_in_contour = gray.copy()
        pixels_in_contour[mask == 0] = 0

        # Oblicz średnią intensywność pikseli w elemencie i dodaj ją do listy
        intensity = np.mean(pixels_in_contour)
        intensities.append(intensity)

    # Oblicz średnią intensywność dla wszystkich elementów
    common_threshold = np.mean(intensities)

    # Binaryzacja całego obrazu na podstawie wspólnego progu
    _, binary_image = cv2.threshold(gray, common_threshold, 255, cv2.THRESH_BINARY)

    # Przekształć obraz na format obsługiwany przez Tkinter i Canvas
    img_pil = Image.fromarray(binary_image)
    img_tk = ImageTk.PhotoImage(img_pil)

    # Wyświetl obraz na płótnie
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.image = img_tk  # Ważne, aby zachować referencję, aby uniknąć problemów z zarządzaniem pamięcią
    global_image = img_tk


window = ctk.CTk()
window.title("Narzędzie do analizy")
ctk.set_appearance_mode("dark")

# Lewy panel
left_frame = ctk.CTkFrame(window)
left_frame.pack(side="left", expand=True, padx=20, pady=20)

# Przyciski "obróć w lewo" i "obróć w prawo"
rotate_left_button = ctk.CTkButton(left_frame, text="Obróć w lewo", command=rotate_left)
rotate_left_button.grid(row=0, column=0, padx=10, pady=10)

rotate_right_button = ctk.CTkButton(left_frame, text="Obróć w prawo", command=rotate_right)
rotate_right_button.grid(row=0, column=1, padx=10, pady=10)

# Suwak
slider_label = ctk.CTkLabel(left_frame, text="Suwak")
slider_label.grid(row=1, column=0, padx=10, pady=10)
number_slider = ctk.CTkSlider(left_frame, from_=0, to=255)
number_slider.grid(row=1, column=1, padx=10, pady=10)

# Przycisk "binaryzuj"
threshold_button = ctk.CTkButton(left_frame, text="Binaryzuj")
threshold_button.grid(row=2, column=0, columnspan=2, pady=10)

# Przycisk "oblicz odległość"
distance_button = ctk.CTkButton(left_frame, text="Oblicz odległość")
distance_button.grid(row=3, column=0, columnspan=2, pady=10)

# Przycisk "wczytaj inne zdjęcie"
load_button = ctk.CTkButton(left_frame, text="Wczytaj zdjęcie", command=open_image)
load_button.grid(row=4, column=0, columnspan=2, pady=10)

# Prawy panel
right_frame = ctk.CTkFrame(window)
right_frame.pack(side="left")


# Obraz
canvas = ctk.CTkCanvas(right_frame)
canvas.grid(row=0, column=0)

window.mainloop()
