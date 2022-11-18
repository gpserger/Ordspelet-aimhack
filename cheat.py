from ppadb.client import Client as AdbClient
import time
import pytesseract
from PIL import Image
import json
from difflib import SequenceMatcher

# Connect to the server
adb = AdbClient(host="127.0.0.1", port=5037)
devices = adb.devices()

if len(devices) == 0:
    print("No device attached")
    quit()

device = devices[0]

playButtonCoords = (530,1260)

boxsize = 500

#coordinates of top left corner of word boxes
words = [
    (32,429),
    (562,429),
    (32,972),
    (562,972)
]


def pressButton(n):
    device.shell(f"input tap {words[n][0]+boxsize/2} {words[n][1]+boxsize/2}")

def tapPlayButton():
    # Press play to start playing
    device.shell(f"input tap {playButtonCoords[0]} {playButtonCoords[1]}")

def saveWordDict(words):
    with open('dict.json', 'w') as f:
        f.write(json.dumps(words))

def getWordDict():
    try:
        with open('dict.json', 'r') as f:
            return json.loads(f.read())
    except:
        return {}

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def getCurrentWordsOnScreen():
    img = device.screencap()
    with open("screen.png", "wb") as f:
        f.write(img)
    img = Image.open("screen.png")
    # word to define
    wordtodefine = pytesseract.image_to_string(img.crop((0, 180, 1080, 428)))

    # definition options
    options = []
    for i in range(len(words)):
        definition = pytesseract.image_to_string(img.crop((words[i][0], words[i][1], words[i][0]+boxsize, words[i][1]+boxsize)))
        definition = definition
        options.append(definition)

    return [wordtodefine, options]

def getCorrectAnswer():
    # return index of the correct button
    img = device.screencap()
    with open("screen.png", "wb") as f:
        f.write(img)
    img = Image.open("screen.png")
    for i in range(len(words)):
        box = img.crop((words[i][0]+200, words[i][1]+20, words[i][0]+boxsize-200, words[i][1]+boxsize-400))
        box.save(f"box{i}.png")
        colors = box.getcolors()
        for color in colors:
            r = abs(color[1][0] - 134)
            g = abs(color[1][1] - 199)
            b = abs(color[1][2] - 124)
            if r+g+b < 20:
                return i

    print("something went wrong")
    exit()

def playAgain():
    print("playing again")
    time.sleep(2)
    tapPlayButton()
    time.sleep(0.01)
    device.shell("input tap 550 2150")
    time.sleep(1)
    tapPlayButton()
    time.sleep(1)

def guess(wordtodefine, definitions, options):
    # press random word, then save word and definition
    print(f"word not found in dictionary")
    pressButton(0)
    time.sleep(0.05)
    ans = getCorrectAnswer()
    print(f"correct answer was " + options[ans])
    definitions[wordtodefine] = options[ans]
    saveWordDict(definitions)
    print(f"Now I know {len(definitions)} words")
    if(ans != 0):
        # unless we happened to guess the right answer, play again
        playAgain()
    else:
        print("We guessed correctly, continuing")
        time.sleep(0.5)

    

def play():

    definitions = getWordDict()

    # Game loop
    tapPlayButton()
    while True:
        print("######################")
        wordtodefine, options = getCurrentWordsOnScreen()
        print(f"defining word: " + wordtodefine)

        if wordtodefine in ['ResulTal\n', 'Statistik\n','']:
            playAgain()
        
        elif wordtodefine in definitions:
            definition = definitions[wordtodefine]
            print(f"definition found in dict: {definition}")
            for i, word in enumerate(options):
                if similar(word, definition) > 0.7:
                    pressButton(i)
                    break
            else:
                print("saved definition doesn't match any of the options")
                print(options)
                print(definitions[wordtodefine])
                guess(wordtodefine, definitions, options)
            time.sleep(1)
        else:
            # new word 
            guess(wordtodefine, definitions, options)

            
        
play()