import fasttext

def identify_language(text):
    text = text.replace("\n", " ")
    model = fasttext.load_model("/home/azureuser/localfiles/cs336-assignment4-data-mine/cs336_data/lid.176.bin")
    lang, score = model.predict(text)
    lang = lang[0].replace("__label__", "")
    return lang, score.item()
