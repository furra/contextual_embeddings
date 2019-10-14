#!/usr/bin/python3
import sys, os, json
import urllib.request, urllib.error
import random #for random times
import time #for sleep
from itertools import cycle
from random import shuffle
from re import sub
from tqdm import tqdm
#yourdictionary.com
#https://sentence.yourdictionary.com/<word>

#cambridge:
#https://dictionary.cambridge.org/dictionary/english/<word> #dataset-american-english?

#collins:
#https://www.collinsdictionary.com/dictionary/english/<word>

#oxford:
#https://en.oxforddictionaries.com/definition/<word>
#https://www.lexico.com/en/definition/<word> NEW

#TODO
# Maybe reduce all of them
from lxml import etree
from lxml.etree import tostring

def get_sentences(content, key):
    if key == 'cam':
        return get_sentences_cam(content)
    elif key == 'col':
        return get_sentences_col(content)
    elif key == 'yourdic':
        return get_sentences_yourdic(content)
    elif key == 'oxf':
        return get_sentences_oxf(content)
    else:
        return None

def get_sentences_cam(content):
    tree = etree.HTML(content)
    sentences = tree.xpath('//span[@class="eg"]')
    for i in range(len(sentences)):
        etree.strip_tags(sentences[i], '*')
    return [sent.text.strip() for sent in sentences if sent.text]

def get_sentences_col(content):
    tree = etree.HTML(content)
    sentences = tree.xpath('//div[contains(@class,"type-example")]')
    for i in range(len(sentences)):
        etree.strip_tags(sentences[i], '*')
    sentences = [sent.text.strip() for sent in sentences if sent.text]
    # return sentences[:-1] if len(sentences) > 1 else sentences
    return sentences

def get_sentences_yourdic(content):
    tree = etree.HTML(content)
    sentences = tree.xpath('//div[contains(@class, "sentence")]')
    for i in range(len(sentences)):
        etree.strip_tags(sentences[i], '*')
    shuffle(sentences)
    return [sent.text.strip() for sent in sentences[:10] if sent.text]
def get_sentences_oxf(content):
    tree = etree.HTML(content)
    sentences = tree.xpath('//li[@class="ex"]')
    for i in range(len(sentences)):
        etree.strip_tags(sentences[i], '*')
    return [sub(r'[‘’]', '', sent.text).strip() for sent in sentences if sent.text]

urls = {
    # 'yourdic': 'https://sentence.yourdictionary.com/'#,
    'cam': 'https://dictionary.cambridge.org/dictionary/english/',
    'col': 'https://www.collinsdictionary.com/dictionary/english/',
    'oxf': 'https://www.lexico.com/en/definition/'
}

browser_headers = {
    'User-Agent': 'Mozilla/5.0'
}

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: {} <word_filename> <output_json_filename>'.format(sys.argv[0]))
        exit()

    word_file = sys.argv[1]
    output_filename = sys.argv[2]

    sentences_by_word = {}

    lines = 0
    with open(word_file) as infile:
        for line in infile:
            lines += 1

    print('Word file has {} lines.'.format(lines))

    with open(word_file) as infile:
        for i in tqdm(range(lines)):
            word = infile.readline().strip()
            sentences_by_word[word] = []
            # sentences_by_word[word] = {}

            for website in urls.values():
                website = random.choice(list(urls.keys()))
                base_url = urls[website]

                url = base_url+word
                req = urllib.request.Request(url, headers=browser_headers)
                page = urllib.request.urlopen(req).read().decode()
                sentences = get_sentences(page, website)
                sentences_by_word[word] += sentences
                # sentences_by_word[word][website] = sentences

    with open('{}.json'.format(output_filename), 'w') as wf:
        wf.write(json.dumps(sentences_by_word, indent=4))
