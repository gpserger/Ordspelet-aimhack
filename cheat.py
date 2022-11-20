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

def formatString(s):
    return s.strip().replace("\n", " ").lower()

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
    wordtodefine = formatString(wordtodefine)

    # definition options
    options = []
    for i in range(len(words)):
        definition = pytesseract.image_to_string(img.crop((words[i][0], words[i][1], words[i][0]+boxsize, words[i][1]+boxsize)))
        definition = formatString(definition)
        options.append(definition)

    return [wordtodefine, options]

def getCorrectAnswer():
    # return index of the correct button
    img = device.screencap()
    with open("check.png", "wb") as f:
        f.write(img)
    img = Image.open("check.png")
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
    pressButton(0)
    time.sleep(0.05)
    ans = getCorrectAnswer()
    print(f"correct answer was " + options[ans])
    definitions[wordtodefine] = [options[ans], 1]
    saveWordDict(definitions)
    print(f"Now I know {len(definitions)} words")
    if(ans != 0):
        # unless we happened to guess the right answer, play again
        playAgain()
        return False
    else:
        print("We guessed correctly, continuing")
        time.sleep(0.5)
        return True


def getBrokenStreakLog():
    try:
        with open('brokenStreakLog.json', 'r') as f:
            return json.loads(f.read())
    except:
        return {}


def saveBrokenStreakLog(log):
    with open("brokenStreakLog.json", "w") as f:
        f.write(json.dumps(log))


def play():
    streakLog = getBrokenStreakLog()
    definitions = getWordDict()

    # Game loop
    tapPlayButton()
    time.sleep(1)
    counter = 0
    streak = 0
    while True:
        counter += 1
        if counter % 10 == 0:
            saveWordDict(definitions)
        wordtodefine, options = getCurrentWordsOnScreen()

        print(f"streak: {streak}", end="\r")
        if wordtodefine in ['resultal', 'statistik']:
            streak = 0
            playAgain()
        
        elif wordtodefine == '':
            print(f"streak of {streak} broken")
            if "empty screen" not in streakLog:
                streakLog["empty screen"] = []
            streakLog["empty screen"].append([
                streak
            ])
            saveBrokenStreakLog(streakLog)
            streak = 0
            time.sleep(2)
            playAgain()
            continue
        
        elif wordtodefine in definitions:
            freq = definitions[wordtodefine][1] + 1
            definition = definitions[wordtodefine][0]
            definitions[wordtodefine] = [definition, freq]
            similarity = [similar(definition, option) for option in options]
            if max(similarity) > 0.7:
                highest = similarity.index(max(similarity))
                pressButton(highest)
                time.sleep(0.03)
                correct = getCorrectAnswer()
                if correct != highest:
                    print(f"defining word {[wordtodefine]}")
                    print("WRONG ANSWER SAVED")
                    print(f"saved definition was {[definition]}")
                    print(f"answer pressed was {[options[highest]]} but should have been {[options[correct]]}")
                    definitions[wordtodefine] = [options[correct], 1]
                    
                    print(f"streak of {streak} broken")
                    if "saved answer wrong" not in streakLog:
                        streakLog["saved answer wrong"] = []
                    streakLog["saved answer wrong"].append([
                        f"defining word: {wordtodefine}, {[definition]}, correct was answer: {[options[correct]]}",
                        streak
                    ])
                    saveBrokenStreakLog(streakLog)
                    streak = 0
                    time.sleep(1)
                else:
                    streak += 1
            else:
                print(f"defining word: {wordtodefine}")
                print(f"saved definition {definitions[wordtodefine]} doesn't match any of the options")
                print([(option, similar(option,definition)) for option in options])
                saveddefinition = definitions[wordtodefine]
                if guess(wordtodefine, definitions, options):
                    streak += 1
                else:
                    if "no match" not in streakLog:
                        streakLog["no match"] = []
                    streakLog["no match"].append([
                        f"defining word: {wordtodefine}, {[(option, similar(option,definition)) for option in options]} does not match definition {saveddefinition}",
                        streak
                    ])
                    saveBrokenStreakLog(streakLog)
                    print(f"streak of {streak} broken")
                    streak = 0
            time.sleep(0.61)
        else:
            # new word 
            print(f"word not found in dictionary")
            if guess(wordtodefine, definitions, options):
                streak += 1
            else:
                if "new word" not in streakLog:
                    streakLog["new word"] = []
                streakLog["new word"].append([
                    f"{wordtodefine}",
                    streak
                ])
                saveBrokenStreakLog(streakLog)
                print(f"streak of {streak} broken")
                streak = 0

play()