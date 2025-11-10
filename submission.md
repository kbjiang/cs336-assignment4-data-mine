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