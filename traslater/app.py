from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pytesseract
from googletrans import Translator

# Se estiver no Windows, configure assim:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
translator = Translator()


def baixar_imagem(url):
    response = requests.get(url, stream=True)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    return img


def extrair_texto(img):
    return pytesseract.image_to_string(img)


def traduzir_texto(texto, idioma_destino):
    result = translator.translate(texto, dest=idioma_destino)
    return result.text


def escrever_texto_na_imagem(original_img, texto_traduzido):
    nova = original_img.copy()
    draw = ImageDraw.Draw(nova)
    width, height = nova.size
    
    # fonte padrão
    font = ImageFont.load_default()
    
    draw.text((10, 10), texto_traduzido, fill="white", font=font)
    return nova


@app.route("/traduzir_imagens", methods=["POST"])
def traduzir_imagens():
    data = request.json
    url = data.get("url")
    idioma = data.get("idioma", "pt")   # destino: pt, en ou es

    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")

    imagens = []

    for img in soup.find_all("img"):
        src = img.get("src")

        if not src:
            continue

        # Resolve links relativos
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            base = url.split("/")[0] + "//" + url.split("/")[2]
            src = base + src

        try:
            original = baixar_imagem(src)
            texto = extrair_texto(original)
            traducao = traduzir_texto(texto, idioma)

            nova_imagem = escrever_texto_na_imagem(original, traducao)

            buffer = BytesIO()
            nova_imagem.save(buffer, format="JPEG", quality=100)
            buffer.seek(0)

            imagens.append({
                "url_original": src,
                "texto_original": texto,
                "texto_traduzido": traducao
            })

        except Exception as e:
            print("Erro ao processar:", src, e)

    return jsonify({"resultado": imagens})


if __name__ == "__main__":
    app.run(debug=True)
