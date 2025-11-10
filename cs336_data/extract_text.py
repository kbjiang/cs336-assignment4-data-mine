from fastwarc.warc import ArchiveIterator, WarcRecordType
import resiliparse
from resiliparse.extract.html2text import extract_plain_text
from resiliparse.parse.encoding import detect_encoding

def extract_text(byte_string):
    encoding = detect_encoding(byte_string)
    html_content = byte_string.decode(encoding=encoding)
    return extract_plain_text(html_content)

if __name__ == "__main__":
    # warc_file = "/home/azureuser/localfiles/cs336-assignment4-data-mine/cs336_data/CC-MAIN-20250417135010-20250417165010-00065.warc.gz"
    # iterator = ArchiveIterator(open(warc_file, "rb"), func_filter=lambda r: r.headers.get('WARC-Identified-Payload-Type') == 'text/html')

    # record = next(iterator)
    # byte_string = record.reader.read()
    with open("/home/azureuser/localfiles/cs336-assignment4-data-mine/tests/fixtures/moby.html", "rb") as f:
        byte_string = f.read()
    extract_text(byte_string)