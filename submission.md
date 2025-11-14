## 2. Filtering Common Crawl
### 2.1 looking at data
#### look_at_cc
1. URL: http://0371rykj.com/ipfhsb/34.html; no longer accessible; it's about some aquatic equipment with description in Chinese.
1. A lot of inappropriate content and ads needs to be removed; not much full sentences on this page
1. Given the content is about some instruments, it might be useful for that domain; but it lacks complete sentences, so not for things like chatbot.
1. Last two column are `High quality` and `Why not`
    1. Chinese, instruments, summary page, N, inappropriate + no good sentences
    1. Chinese, blog on movies, post page, Y, 
    1. English, conference, front page, Y,
    1. Chinese, adualt content, front page, N, inappropriate + no good sentences
    1. Chinese, instruments, summary page, N, inappropriate
    1. Chinese, adualt content, post page, N, inappropriate
    1. Chinese, adualt content, front page, N, inappropriate + no good sentences
    1. Dutch, , front page, N, no good sentences
    1. Russian?, , ,
    1. Chinese, gambling, introduction page, Y, 
    1. ?, , , no good sentences

### 2.2 HTML to text conversion
#### extract_text
1. With `fastwarc` and `resiliparse`. https://resiliparse.chatnoir.eu/en/stable/index.html
1. `resiliparse` extraction keeps more layout of the text therefore I like it better.

### 2.3 Language identification
#### language_identification
1. done
1. there are several possible issues
    1. when little text present, the model is less certain
        1. when empty, the model defaults to `en`.
    1. when mixed with numbers/symbols, the model is less certain
    1. when mixed languages present, the model is less certain
1. about 9/20 are `en`. I think the model is quite accurate, so I would accept its prediction with confidence score as low as `0.4`.

### 2.4 PII
#### Learning
1. See `regex.md` for learnings about `regex`.
#### mask_pii
1. Done
1. Done
1. Done
1. With masking the model won't be able to learn about what Email address, Phone number and IP address look like. Maybe consider shuffling instead of masking.
1. Did well on emails; apparently it misses a lot of non-us phone numbers; not much IP addresses showed up.

### 2.5 Harmful content
#### harmful_content
1. Done
1. Done
1. Issues
    1. the model does not work on non-english languages, needs multi-lingual models
    <!-- 1. false negatives when only small part of the webpage is harmful -->
1. Not many NSFW or Toxic pages in English (a lot in Chinese)

### 2.6 Quality Rules
#### gopher_quality_filters
1. Done
1. Does not work on non-latin language like Chinese.

### 2.7 Quality Classifier
#### quality_classifier
1. Done. See `submission.ipynb`.