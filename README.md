# Ordspelet-aimhack

This is a simple cheat I made for the app [ORD-Spelet](https://play.google.com/store/apps/details?id=se.teoriappar.hp.words.game&hl=sv&gl=US), a word definition game.

The game involves correctly guessing the definition of a swedish word or phrase to get points.

The app is run on a real android phone via pure-python-adb.

The cheat basically takes a screenshot of the word to define and all options and uses google's Tesseract OCR engine to look up the word in a dictionary.
If the word is not already in the dictionary, it will guess the first option and remember what the indicated correct choice was and start over.

Over time it learns enough words to get a streak and post a high-score.

I have chosen to not include the dictionary file to limit unfair use, because building it takes quite a long time.
