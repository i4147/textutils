def invertir(texto):
    return texto[::-1]


def alternar_mayusculas(texto):
    resultado = ""
    mayus = True
    for letra in texto:
        if letra.isalpha():
            resultado += letra.upper() if mayus else letra.lower()
            mayus = not mayus
        else:
            resultado += letra
    return resultado


def contar_vocales(texto):
    contador = 0
    for letra in texto.lower():
        if letra in "aeiou":
            contador += 1
    return contador


def es_palindromo(texto):
    limpio = "".join(c.lower() for c in texto if c.isalnum())
    return limpio == limpio[::-1]


def vocales_por_numeros(texto):
    resultado = ""
    texto = texto.upper()
    for letra in texto:
        match letra:
            case "A":
                resultado += "4"
            case "E":
                resultado += "3"
            case "I":
                resultado += "1"
            case "O":
                resultado += "0"
            case _:
                resultado += letra
    return resultado
