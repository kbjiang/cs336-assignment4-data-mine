import fasttext

def classify_nsfw(text):
    text = text.replace("\n", " ")
    model = fasttext.load_model("/home/azureuser/localfiles/cs336-assignment4-data-mine/cs336_data/jigsaw_fasttext_bigrams_nsfw_final.bin")
    pred, score = model.predict(text)
    pred = pred[0].replace("__label__", "")
    return pred, score.item()

def classify_toxic_speech(text):
    text = text.replace("\n", " ")
    model = fasttext.load_model("/home/azureuser/localfiles/cs336-assignment4-data-mine/cs336_data/jigsaw_fasttext_bigrams_hatespeech_final.bin")
    pred, score = model.predict(text)
    pred = pred[0].replace("__label__", "")
    return pred, score.item()