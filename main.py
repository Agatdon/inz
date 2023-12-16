import tkinter as tk
from tkinter import *
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps  # Do obsługi obrazów
from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Zmienna globalna przechowująca obraz
global_image = None
global_data = []

def open_image():
    global global_image, canvas, threshold_button, number_slider, global_data
    global_data = []

    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.ppm *.pgm *.tif *.tiff")])
    if file_path:
        # Wczytaj obraz przy użyciu Pillow
        img_pillow = Image.open(file_path)
        # Przekształć obraz na format obsługiwany przez OpenCV (BGR)
        img_cv2 = cv2.cvtColor(np.array(img_pillow), cv2.COLOR_RGB2BGR)
        # Przekształć obraz na odcienie szarości
        gray_image = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)
        global_image = gray_image
        # Wyświetl obraz na płótnie
        widthx, heighty = gray_image.shape[1], gray_image.shape[0]
        photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(gray_image, cv2.COLOR_BGR2RGB)))
        canvas.create_image(0, 0, anchor="nw", image=photo, tags="current_image")  # Dodaj tag "current_image" do obrazu
        canvas.image = photo
        # Dostosuj rozmiar Canvas do rozmiaru obrazu

        if widthx <= 1366 and heighty <= 768:
            # Jeśli jest mniejszy, dostosuj Canvas do rozmiaru obrazu
            canvas.config(width=widthx, height=heighty)
        else:
            # Jeśli jest większy, dostosuj Canvas do maksymalnego rozmiaru 1000x500
            scaled_image = cv2.resize(gray_image, (1366, 768))
            global_image = scaled_image
            photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(scaled_image, cv2.COLOR_BGR2RGB)))
            canvas.create_image(0, 0, anchor="nw", image=photo, tags="current_image")  # Dodaj tag "current_image" do obrazu
            canvas.image = photo
            canvas.config(width=1366, height=768)


        rotate_left_button.configure(state=tk.NORMAL)  # Włącz przycisk "Obróć w lewo"
        rotate_left_button.configure(command=lambda: rotate_left())  # Przypisz funkcję rotate_left jako obsługę przycisku
        # Progowanie
        threshold_button.configure(state=tk.NORMAL)  # Włącz przycisk przetwarzania
        threshold_button.configure(command=lambda: threshold_image(global_image, number_slider.get()))
        distance_button.configure(command=lambda: sharpen_edges(global_image))
        edge_button.configure(command=lambda: find_and_draw_edges(global_image))
        # Ustawienia narzędziowe
        points_list = [[]]  # Rozpocznij z jedną pustą listą punktów
        distances_list = []
        start_button.configure(command=lambda: start_measurement(save_button, canvas, points_list))
        save_button.configure(command=lambda: save_distances(points_list, distances_list))
        # Dodaj zdarzenie myszy
        canvas.bind("<Button-1>", lambda event: on_click(event, canvas, points_list[-1]))

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
    global global_image, canvas
    if global_image is not None:
        # Sprawdź, czy global_image jest instancją numpy.ndarray
        if not isinstance(img, np.ndarray):
            # Jeśli nie, przekształć go do numpy array
            img = np.array(img)
            # <class 'numpy.ndarray'>

        # img = global_image
        if len(img.shape) > 2:
            gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = img

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
        #global_image=thresholded_image
        # Progowanie
        #_, thresholded_image = cv2.threshold(gray_image, average_brightness, 255, cv2.THRESH_BINARY)
        #_, thresholded_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Inicjalizuj obraz segmentacji
        segmented_image = np.zeros_like(thresholded_image)

        edges = cv2.Canny(gray_image, 100, 200)
        global_image=thresholded_image
        # Przekształć obraz na format obsługiwany przez Tkinter i Canvas
        img_pil = Image.fromarray(thresholded_image)
        img_tk = ImageTk.PhotoImage(img_pil)

        # Wyświetl obraz na płótnie
        canvas.create_image(0, 0, anchor="nw", image=img_tk)
        canvas.image = img_tk  # Ważne, aby zachować referencję, aby uniknąć problemów z zarządzaniem pamięcią

        return thresholded_image

def update_binary_image(value):
    global global_image, canvas
    threshold_value = int(value)  # Pobierz wartość suwaka i przekształć ją na liczbę całkowitą
    _, thresholded_image = cv2.threshold(global_image, threshold_value, 255, cv2.THRESH_BINARY)
    # Konwertuj obrazy do formatu obsługiwanego przez Tkinter
    img_pil = Image.fromarray(thresholded_image)
    img_tk = ImageTk.PhotoImage(img_pil)
    # Wyświetl obrazy na płótnie
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.image = img_tk  # Ważne, aby zachować referencję, aby uniknąć problemów z zarządzaniem pamięcią

def find_and_draw_edges(edges_image):
    global global_image, canvas
    # Znajdź kontury na obrazie krawędzi
    contours, _ = cv2.findContours(edges_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(contours)
    # Narysuj kontury na oryginalnym obrazie
    edges_drawn = edges_image.copy()
    edge_img = cv2.cvtColor(edges_drawn, cv2.COLOR_BGR2RGB)
    edge_img=cv2.drawContours(edge_img, contours, -1, (255, 0, 0), 2)

    # Przekształć obraz na format obsługiwany przez Tkinter i Canvas
    img_pil = Image.fromarray(edge_img)
    img_tk = ImageTk.PhotoImage(img_pil)

    # Wyświetl obraz na płótnie
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.image = img_tk  # Ważne, aby zachować referencję, aby uniknąć problemów z zarządzaniem pamięcią

    return edges_drawn

def detect_oval_edges(img):
    # Przekształć obraz na odcienie szarości
    if len(img.shape) > 2:
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray_image = img

    # Wykryj krawędzie za pomocą operatora Sobela (możesz użyć wcześniej wyostrzonego obrazu)
    edges = cv2.Canny(gray_image, 50, 150)

    # Zastosuj morfologiczną operację otwarcia, aby pozbyć się drobnych zakłóceń
    kernel = np.ones((5, 5), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel)

    # Wykryj okręgi za pomocą transformacji Hougha
    circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=50, param2=30, minRadius=5, maxRadius=50)

    # Rysuj znalezione okręgi na obrazie oryginalnym
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2)  # Rysuj okrąg
            cv2.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)  # Rysuj środek okręgu

    global_image=img
    # Przekształć obraz na format obsługiwany przez Tkinter i Canvas
    img_pil = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(img_pil)

    # Wyświetl obraz na płótnie
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.image = img_tk  # Ważne, aby zachować referencję, aby uniknąć problemów z zarządzaniem pamięcią

    return img


def sharpen_edges(image):
    global global_image  # Użyj zmiennej globalnej, aby uzyskać dostęp do obrazu
    # Przekształć obraz na odcienie szarości, jeśli nie jest jeszcze w takim formacie
    if len(image.shape) > 2:
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray_image = image

    # Zastosuj operator Sobela w poziomie i pionie
    sobel_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=5)
    sobel_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=5)

    # Oblicz moduł gradientu
    gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
    print("The magnitude, name is of type:", type(gradient_magnitude.shape))
    print("The img, name is of type:", type(gray_image.shape))

    gradient_magnitude = cv2.resize(gradient_magnitude, (gray_image.shape[1],gray_image.shape[0]))
    # Konwertuj gray_image do typu danych gradient_magnitude
    gray_image = cv2.convertScaleAbs(image)
    # Konwertuj gradient_magnitude do typu danych gray_image
    gradient_magnitude = gradient_magnitude.astype(np.uint8)

    # Wyostrz krawędzie poprzez dodanie obrazu oryginalnego do obrazu gradientu
    sharpened_image = cv2.addWeighted(gray_image, 1.5, gradient_magnitude, -0.5, 0)
    global_image=sharpened_image

    # Przekształć obraz na format obsługiwany przez Tkinter i Canvas
    img_pil = Image.fromarray(sharpened_image)
    img_tk = ImageTk.PhotoImage(img_pil)

    # Wyświetl obraz na płótnie
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.image = img_tk  # Ważne, aby zachować referencję, aby uniknąć problemów z zarządzaniem pamięcią

    return sharpened_image

def on_click(event, canvas, points):
    # Dodaj punkt do listy
    points.append((event.x, event.y))

    # Rysuj punkt na Canvas
    canvas.create_oval(event.x - 2, event.y - 2, event.x + 2, event.y + 2, fill="red")

    # Połącz punkty linią
    if len(points) > 1:
        last_point = points[-2]
        line_id = canvas.create_line(last_point[0], last_point[1], event.x, event.y, fill="blue")


def start_measurement(save_button, canvas, points_list):
    # Odblokuj przycisk zapisu
    save_button['state'] = 'normal'

    # Rozpocznij nowy pomiar - utwórz nową listę punktów
    points_list.append([])


def save_distances(points_list, distances_list):
    global global_data
    if len(points_list[-1]) > 1:
        y0 = points_list[-1][0][1]  # Pierwszy punkt jako punkt odniesienia po y
        print("Points are:", points_list)
        distances_list.append([point[1] - y0 for point in points_list[-1]])

        print("Distances from y0:", distances_list[-1])
    global_data.append((len(global_data), distances_list[-1]))
    # Wyświetl aktualną globalną listę
    print("Global Data:", global_data)

def calculate_mass():
    # Pobierz tekst z pola tekstowego
    dna_sequence = entry.get()

    # Convert dna_sequence to integer
    path_number = int(dna_sequence)

    # Sciezka markera
    marker = [19, 25, 34, 49, 85, 119]

    # Tutaj dodaj kod do obliczenia masy ścieżki (przetłumaczenie, obliczenia masy itp.)

    # Znajdź dane dla ścieżki 0 (referencyjnej)
    reference_data = None
    for data_point in global_data:
        if data_point[0] == 0:
            reference_data = data_point
            break

    if reference_data is not None:
        reference_distances = reference_data[1]

        # Avoid division by zero
        if reference_distances[1] != 0:
            distances = reference_distances[1:]
            log_marker = [np.log(_marker) for _marker in marker]

            # Oblicz regresję liniową
            slope, intercept = np.polyfit(np.abs(distances), log_marker, 1)

            # Oblicz masę dla punktów na wybranej ścieżce
            selected_data = None
            for data_point in global_data:
                if data_point[0] == path_number:
                    selected_data = data_point
                    break

            if selected_data is not None:
                selected_distances = selected_data[1][1:]
                masses = slope * np.abs(selected_distances) + intercept
                masses = np.exp(masses)

                # Wyświetl masę dla każdego punktu
                for distance, mass in zip(selected_distances, masses):
                    print(f'Dystans: {distance}, Obliczona masa: {mass}')

            else:
                print(f"Nie można znaleźć danych dla ścieżki {path_number}.")

        else:
            # Handle the case when reference_distances[0] is zero
            print("Cannot calculate Rf values. Distance at index 0 is zero.")

    else:
        print("Nie można znaleźć danych dla ścieżki referencyjnej.")

window = ctk.CTk()
window.title("Narzędzie do analizy")
ctk.set_appearance_mode("dark")

# Lewy panel
left_frame = ctk.CTkFrame(window)
left_frame.pack(side="left", expand=True, padx=20, pady=20)

# Przycisk "wczytaj inne zdjęcie"
load_button = ctk.CTkButton(left_frame, text="Wczytaj zdjęcie", command=open_image)
load_button.grid(row=0, column=0, columnspan=2, pady=10)

# Przyciski "obróć w lewo" i "obróć w prawo"
rotate_left_button = ctk.CTkButton(left_frame, text="Obróć w lewo", command=rotate_left)
rotate_left_button.grid(row=1, column=0, padx=10, pady=10)

rotate_right_button = ctk.CTkButton(left_frame, text="Obróć w prawo", command=rotate_right)
rotate_right_button.grid(row=1, column=1, padx=10, pady=10)

# Przycisk "Wyostrz krawędzie"
distance_button = ctk.CTkButton(left_frame, text="Wyostrz krawędzie")
distance_button.grid(row=2, column=0, columnspan=2, pady=10)

# Przycisk "Detekcja krawędzi"
edge_button = ctk.CTkButton(left_frame, text="Znajdż krawędzie")
edge_button.grid(row=3, column=0, columnspan=2, pady=10)

# Suwak
slider_label = ctk.CTkLabel(left_frame, text="Próg binaryzacji")
slider_label.grid(row=4, column=0, padx=10, pady=10)
number_slider = ctk.CTkSlider(left_frame, from_=0, to=255, command=lambda value: update_binary_image(value))
number_slider.grid(row=4, column=1, padx=10, pady=10)

# Przycisk "binaryzuj"
threshold_button = ctk.CTkButton(left_frame, text="Binaryzuj")
threshold_button.grid(row=5, column=0, columnspan=2, pady=10)

# tekst
messagebox = ctk.CTkLabel(left_frame, text="Na początku zaznacz 6 punktów na ścieżce kalibracyjnej")
messagebox.grid(row=6, column=0, columnspan=2, pady=10)

# Dodaj przycisk do rozpoczęcia zaznaczania odległości
start_button = ctk.CTkButton(left_frame, text="Start Measurement")
start_button.grid(row=7, column=0, padx=10, pady=10)

# Dodaj przycisk do zapisywania odległości
save_button = ctk.CTkButton(left_frame, text="Save Distances")
save_button.grid(row=7, column=1, padx=10, pady=10)
save_button['state'] = 'disabled'  # Zablokuj przycisk zapisu na początku

# Utwórz przycisk do obliczania masy
calculate_button = ctk.CTkButton(left_frame, text="Oblicz masę ścieżki", command=calculate_mass,
                                 width=180)
calculate_button.grid(row=8, column=0, columnspan=2, pady=10)

# Utwórz pole tekstowe do wprowadzania danych
entry = ctk.CTkEntry(calculate_button,width=30, height=25)
entry.place(relx=1.0, rely=0.0, anchor='ne')

# Utwórz etykietę wynikową
result_label = ctk.CTkLabel(left_frame, text="Masa ścieżki: 0 g")
result_label.grid(row=9, column=0, columnspan=2, pady=10)

# Prawy panel
right_frame = ctk.CTkFrame(window)
right_frame.pack(side="left")

# Obraz
canvas = ctk.CTkCanvas(right_frame)
canvas.grid(row=0, column=0)

window.mainloop()
