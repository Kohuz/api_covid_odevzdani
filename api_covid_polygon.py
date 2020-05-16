import requests
import json

from flask import Flask, request, jsonify, send_from_directory, render_template

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True

#Vytvoření třídy Kraj
class Kraj:
    pocet_muzu = 0
    pocet_zen = 0
    celkovy_vek_muzi = 0
    celkovy_vek_zeny = 0

    def __init__(self, name, code, type, coordinates):
        self.name = name
        self.code = code
        self.type = type
        self.coordinates = coordinates

#Metoda přidáhní
    def pridat_infikovane(self, pohlavi, vek):
        if pohlavi == "M":
            self.pocet_muzu += 1
            self.celkovy_vek_muzi += vek

        elif pohlavi == "Z":
            self.pocet_zen += 1
            self.celkovy_vek_zeny += vek
#Vypsání parametrů
    def get_json(self):
        pocet_nakazenych = self.pocet_muzu + self.pocet_zen
        prumer_vek = (self.celkovy_vek_zeny + self.celkovy_vek_muzi)/pocet_nakazenych
        prumer_vek_zeny = self.celkovy_vek_zeny / self.pocet_zen
        prumer_vek_muzi = self.celkovy_vek_muzi / self.pocet_muzu
        podil_muzu = self.pocet_muzu / pocet_nakazenych * 100
        vysledek = {"total_infected": pocet_nakazenych,
                    "avg_age": round(prumer_vek,2),
                    "avg_age_women": round(prumer_vek_zeny, 2),
                    "avg_age_men": round(prumer_vek_muzi,2),
                    "men": round(podil_muzu, 2),
                    "women": round(100-podil_muzu, 2),
                    "code": self.code, "name": self.name}
        return vysledek
    def get_coordinates(self):
        result = {"type": self.type, "coordinates": self.coordinates}
        return result
kraje=list()

#zpracovani jsonu kraje
r = requests.get("http://arccr-arcdata.opendata.arcgis.com/datasets/6475ee085a0d498fb9075fd6320d16f2_8.geojson")
r = r.json()
j = 0


#načtení krajů
for i in range(len(r["features"])):
    kraje.append(Kraj(r["features"][i]["properties"]['NAZ_CZNUTS3'],r["features"][i]["properties"]['KOD_CZNUTS3'],
                      r["features"][i]["geometry"]["type"],r["features"][i]["geometry"]["coordinates"]))



# Načteni nemocných
r = requests.get("https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/osoby.json")
r = r.json()
for osoba in r["data"]:
    k=0
    for kody in kraje:
        if kraje[k].code == osoba["KHS"]:
            index = k
            break
        else:
            k += 1

    kraje[index].pridat_infikovane(osoba["Pohlavi"], int(osoba["Vek"]))


#------------------FLASK--------------

#Jednotlivá cesta pro každý kraj
@app.route("/covid_kraje", methods=["GET"])
def covid_kraje():
    kraj = request.args.get("kraj", "0")
    k = 0
    for kody in kraje:
        if kraje[k].code == kraj:
            index = k
            nenalezeno = False
            break
        else:
            k += 1
            nenalezeno = True

    if nenalezeno:
        return "Chyba, požadovaný tvar /covid_kraje?kraj=CZ(NUTS ČÍSLO KRAJE)"
    else:
        result = kraje[index].get_json()
        result = jsonify(result)
        return result

#Json všech krajů
@app.route("/covid_kraje_json", methods=["GET"])
def covid_kraje_json():
    features = []
    i = 0
    for x in kraje:
        features.append({"type" : "Feature", "properties": kraje[i].get_json(), "geometry": kraje[i].get_coordinates()})
        i += 1
    results = {"type": "FeaturesCollection","features": features}
    return jsonify(results)

#úvodní stránka index.html
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")
#
@app.route('/leaflet', methods=['GET'])
def leaflet():
   return send_from_directory('.', 'leaflet.html')


if __name__ == '__main__':
    app.run(debug=True)