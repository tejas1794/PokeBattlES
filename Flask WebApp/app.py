from flask import Flask, render_template, request, redirect, url_for
import pokemon_battles

# model_pipeline = load("model.joblib")
# import numpy as np

# model_pipeline = load_model("reviewCheck_V1.h5")

result = ""
player_hp = 1000
ai_hp = 1000
console = ''
ucards = []
ccards = []
strategy = 0
round_num = 1
card = 'static\card.png'

img_dict = {1: 'static\Bulbasaur.JPG',
            2: 'static\Ivysaur.JPG',
            3: 'static\Venusaur.JPG',
            151: 'static\Mega Venusaur.JPG',
            4: 'static\Charmander.JPG',
            5: 'static\Charmeleon.JPG',
            6: 'static\Charizard.JPG',
            152: 'static\Mega Charizard X.JPG',
            153: 'static\Mega Charizard Y.JPG',
            7: 'static\Squirtle.JPG',
            8: 'static\Wartortle.JPG',
            9: 'static\Blastoise.JPG',
            154: 'static\Mega Blastoise.JPG',
            25: 'static\pikachu.png',
            26: 'static\Raichu.JPG',
            37: 'static\Vulpix.JPG',
            38: 'static\\Ninetales.JPG',
            43: 'static\Oddish.JPG',
            44: 'static\Gloom.JPG',
            45: 'static\Vileplume.JPG',
            54: 'static\Psyduck.JPG',
            55: 'static\Golduck.JPG',
            58: 'static\Growlithe.JPG',
            59: 'static\Arcanine.JPG',
            60: 'static\Poliwag.JPG',
            61: 'static\Poliwhirl.JPG',
            62: 'static\Poliwrath.JPG',
            69: 'static\Bellsprout.JPG',
            70: 'static\Weepinbell.JPG',
            71: 'static\Victreebel.JPG',
            72: 'static\Tentacool.JPG',
            73: 'static\Tentacruel.JPG',
            74: 'static\Geodude.JPG',
            75: 'static\Graveler.JPG',
            76: 'static\Golem.JPG',
            77: 'static\Ponyta.JPG',
            78: 'static\Rapidash.JPG',
            79: 'static\Slowpoke.JPG',
            80: 'static\Slowbro.JPG',
            155: 'static\Mega Slowbro.JPG',
            81: 'static\Magnemite.JPG',
            82: 'static\Magneton.JPG',
            86: 'static\Seel.JPG',
            87: 'static\Dewgong.JPG',
            90: 'static\Shellder.JPG',
            91: 'static\Cloyster.JPG',
            95: 'static\Onix.JPG',
            98: 'static\Krabby.JPG',
            99: 'static\Kingler.JPG',
            100: 'static\Voltorb.JPG',
            101: 'static\Electrode.JPG',
            102: 'static\Exeggcute.JPG',
            103: 'static\Exeggutor.JPG',
            114: 'static\Tangela.JPG',
            116: 'static\Horsea.JPG',
            117: 'static\Seadra.JPG',
            118: 'static\Goldeen.JPG',
            119: 'static\Seaking.JPG',
            120: 'static\Staryu.JPG',
            121: 'static\Starmie.JPG',
            125: 'static\Electabuzz.JPG',
            126: 'static\Magmar.JPG',
            129: 'static\Magikarp.JPG',
            130: 'static\Gyarados.JPG',
            156: 'static\Mega Gyarados.JPG',
            131: 'static\Lapras.JPG',
            134: 'static\Vaporeon.JPG',
            135: 'static\Jolteon.JPG',
            136: 'static\Flareon.JPG',
            138: 'static\Omanyte.JPG',
            139: 'static\Omastar.JPG',
            140: 'static\Kabuto.JPG',
            141: 'static\Kabutops.JPG',
            142: 'static\Aerodactyl.JPG',
            157: 'static\Mega Aerodactyl.JPG',
            144: 'static\Articuno.JPG',
            145: 'static\Zapdos.JPG',
            146: 'static\Moltres.JPG',
            150: 'static\Mewtwo.JPG',
            158: 'static\Mega Mewtwo X.JPG',
            159: 'static\Mega Mewtwo Y.JPG',
            200: 'static\energy1.JPG',
            201: 'static\energy1.JPG',
            202: 'static\energy1.JPG',
            203: 'static\energy1.JPG',
            204: 'static\energy2.JPG',
            205: 'static\energy2.JPG',
            206: 'static\energy2.JPG',
            207: 'static\energy3.JPG',
            208: 'static\energy3.JPG',
            209: 'static\energy3.JPG',
            210: 'static\energy3.JPG'}

app = Flask(__name__, template_folder="pages")


def is_deceptive(query):
    # if str(model_pipeline.predict([query])[0]) == "0":
    #     return "Real"
    return "Deceptive"


@app.route('/', methods=['GET', 'POST'])
def initialize():
    if request.method == 'POST':
        return render_template('forms/GameSetup.html')
    return render_template('forms/Home.html')


@app.route('/end', methods=['GET', 'POST'])
def endgame():
    return render_template('forms/EndGame.html')


@app.route('/startgame', methods=['GET', 'POST'])
def setup_game():
    console_output = "Initializing game - click Draw button to begin!"
    if request.method == 'POST':
        ai_hp = request.form['totalhp']
        player_hp = request.form['totalhp']
        total_hp = request.form['totalhp']
        strategy = 'Optimal' if request.form['strategy'] == '1' else 'Random'
        return render_template('forms/DrawScreen.html', playerHP=player_hp, aiHP=ai_hp, strategy=strategy,
                               console=console_output, rnum=0, totalHP=total_hp)
    return render_template('forms/GameSetup.html')


@app.route('/draw', methods=['GET', 'POST'])
def draw():
    if request.method == 'POST':
        php = int(request.form["playerhp"])
        ahp = int(request.form["aihp"])
        rn = int(request.form["rnum"])
        total_hp = int(request.form["totalhp"])
        uc = []
        ac = []
        console, computerhp, userhp, user_cards, computer_cards, rnum = pokemon_battles.runIt(php, ahp, uc, ac, rn, 0,
                                                                                              "Draw", total_hp)
        return render_template('forms/PlayScreen.html', playerHP=userhp, aiHP=computerhp, console=console,
                               usercards=user_cards, aicards=computer_cards, card=card, rnum=rnum,
                               image1=img_dict[user_cards[0]], val1=user_cards[0],
                               image2=img_dict[user_cards[1]], val2=user_cards[1],
                               image3=img_dict[user_cards[2]], val3=user_cards[2],
                               image4=img_dict[user_cards[3]], val4=user_cards[3],
                               image5=img_dict[user_cards[4]], val5=user_cards[4], totalHP=total_hp)
    return render_template('forms/DrawScreen.html', playerHP=player_hp, aiHP=ai_hp, console='',
                           usercards=ucards, aicards=ccards, card=card, rnum=round_num, totalHP=1000)


@app.route('/play', methods=['GET', 'POST'])
def play():
    if request.method == 'POST':
        selected_card = request.form['btn']
        php = int(request.form["playerhp"])
        ahp = int(request.form["aihp"])
        rn = int(request.form["rnum"])
        total_hp = int(request.form["totalhp"])
        uc = list(map(int, request.form["ucards"][1:len(request.form["ucards"])-1].split(',')))
        ac = list(map(int, request.form["ccards"][1:len(request.form["ccards"])-1].split(',')))
        console, computerhp, userhp, user_cards, computer_cards, rnum = pokemon_battles.runIt(php, ahp, uc, ac, rn,
                                                                                        selected_card, "", total_hp)
        return render_template('forms/DrawScreen.html', playerHP=userhp, aiHP=computerhp, console=console,
                               usercards=user_cards, aicards=computer_cards, card=card, rnum=rnum, totalHP=total_hp)
    return render_template('forms/PlayScreen.html', playerHP=player_hp, aiHP=ai_hp, console='',
                           usercards=ucards, aicards=ccards, card=card, rnum=round_num, totalHP=1000)


if __name__ == '__main__':
    app.run(debug=True)
