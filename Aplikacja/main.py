from PIL import Image
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import cv2

#przypisanie stalych kolorow na podstawie wartosci RGB wymaganej w zadaniu
WHITE = (255, 255, 255)
RED = (255, 0, 0)

app = Flask(__name__)


#funkcja sprawdzajaca poprawnosc wyrwanego paska pixeli z obrazu
#poprawne sa dwie kombinacje bialo - czerwona i na odwrot w kolejnosci poziomej lub pionowej
def check_bar(bar: list) -> int:
    """
    Funkcja sprawdza czy podany pasek jest bialo - czerwony lub na odwrot i zwraca odpowiedni status
    :param bar: lista skladajaca sie z 6 tupli, reprezentujacych kolor pixela w formacie RGB
    :return: status 1 - pasek bialo - czerwony 2 - pasek czerwono - bialy, 0 - niepoprawny pasek
    """
    correct_white_red = [WHITE, WHITE, WHITE, RED, RED, RED]
    correct_red_white = [RED, RED, RED, WHITE, WHITE, WHITE]
    if bar == correct_white_red:
        return 1

    elif bar == correct_red_white:
        return 2

    else:
        return 0


#funckja przeszukujaca obraz pixel po pixelu oraz tworzaca paski wysylane do funkcji sprawdzajacej
#funckja zwraca odpowiedni status w zaleznosci od odnalezionego paska
def solve_problem(image: Image) -> int:
    """
    Funkcja przeszukuje poziomo i pionowo obraz w celu znalezienia paska skladajacego sie z trzech pixeli
    koloru bialego i trzech czerwonego, przeszukiwanie dziala na zasadzie tworzenia 6-cio pixelowych paskow,
    ktore sa wysylane do innej funkcji sprawdzajacej poprawnosc, funkcja konczy sie, gdy znajdzie pierwszy napotkany pasek
    lub zwraca -1, gdy takowego nie znajdzie
    Najpierw przeszukiwanie jest poziome, wiec w przypadku wielu paskow poziomych i pionowych na obrazku,
    obrot wykona sie wedlug pierwszego napotkanego poziomego paska
    Opis statusow:
    1 - obrot o 90 stopni zgodnie z zegarem
    2 - obrot o 90 stopni przeciwnie do zegara
    3 - pasek ustawiony zgodnie z celem, brak obrotu
    4 - obrot o 180 stopni
    -1 - brak paska na obrazku
    :param image: argumentem jest obraz jako obiekt Image z biblioteki PIL
    :return: zwracany jest status, ktory mowi jak zrotowac obrazek lub -1, w przypadku niepowodzenia
    """
    pix = image.load()
    image_width = image.size[0]
    image_height = image.size[1]
    #przeszukiwanie poziomo
    #mozliwe tylko gdy szerokosc obrazka jest nie mniejsza niz dlugosc paska
    if image_width >= 6:
        for i in range(image_height):
            for j in range(image_width - 5):
                current_bar = []
                for k in range(j, j + 6):
                    current_bar.append(pix[k, i])
                status = check_bar(current_bar)
                if status == 1 or status == 2:
                    return status

    #przeszukiwanie pionowo
    #mozliwe tylko gdy wysokosc obrazka jest nie mniejsza niz dlugosc paska
    if image_height >= 6:
        for i in range(image_width):
            for j in range(image_height - 5):
                current_bar = []
                for k in range(j, j + 6):
                    current_bar.append(pix[i, k])
                status = check_bar(current_bar)
                if status == 1:
                    return 3
                if status == 2:
                    return 4

    #w przypadku niepowodzenia
    return -1


def valid_file(filename: str) -> int:
    """
    funkcja sprawdzajaca czy przeslany plik jest poprawny, to znaczy czy jego format to zgodnie z wymaganiami
    zadania jest png oraz czy nazwa nie jest pusta
    :param filename: nazwa pliku wraz z rozszerzeniem
    :return: status oznaczajacy rezultat walidacji, 0 - pusty nazwa, 1 - poprawny format png oraz 2 - niepoprawny format
    """
    if filename == "":
        return 0
    else:
        file_name = filename.split(".")
        if file_name[1] == "png":
            return 1
        else:
            return 2


#sciezka /rotate odbiera przekazany plik i wykonuje zadanie
@app.route("/rotate", methods=["POST", "GET"])
def upload():

    if request.method == "POST":
        #wylapywanie ewentualnych bledow, niepowodzen za pomoca try, except
        try:
            f = request.files['file']
            f.save(secure_filename(f.filename))
            validate_file = valid_file(f.filename)
            if validate_file == 1:
                image = Image.open(f.filename)
                image = image.convert("RGB")
                #wywolanie funkcji przeszukiwania
                answer = solve_problem(image)

                if answer == -1:
                    #jezeli na obrazie nie wystepuje szukany pasek zwracamy status 204 No content
                    return "No content", 204

                else:
                    img = cv2.imread(f.filename)
                    #obluga odpowiedniej rotacji za pomoca bilbioteki cv2
                    #odpowiednia rotacja dobierana jest na podstawie polozenia paska
                    #zrotowany obraz zapisywany jest do folderu static
                    if answer == 1:
                        rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                        cv2.imwrite(f"static/{f.filename}", rotated)

                    elif answer == 2:
                        rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        cv2.imwrite(f"static/{f.filename}", rotated)

                    elif answer == 3:
                        cv2.imwrite(f"static/{f.filename}", img)

                    else:
                        rotated = cv2.rotate(img, cv2.ROTATE_180)
                        cv2.imwrite(f"static/{f.filename}", rotated)

                    return send_file(f"static/{f.filename}", as_attachment=True), 200

            elif validate_file == 2:
                return "Invalid format", 400

            else:
                return "Invalid input", 400

        except Exception as e:
            return str(e), 400

    if request.method == "GET":
        return render_template("upload.html")


if __name__ == "__main__":
    app.run()

