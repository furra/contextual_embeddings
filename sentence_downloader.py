#!/usr/bin/python3
import sys, os, json, argparse
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
    elif key == 'yourdict':
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
    return [sent.text.strip() for sent in sentences[:10] if sent.text]

def get_sentences_oxf(content):
    tree = etree.HTML(content)
    sentences = tree.xpath('//li[@class="ex"]')
    for i in range(len(sentences)):
        etree.strip_tags(sentences[i], '*')
    return [sub(r'[‘’]', '', sent.text).strip() for sent in sentences if sent.text]


browser_headers = {
    'User-Agent': 'Mozilla/5.0'
}

#add list of proxies
proxy_list = ['127.0.0.1:80']
shuffle(proxy_list)
proxy_pool = cycle(proxy_list)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Downloads example sentences from online websites for a list of words and creates a JSON file.")

    parser.add_argument('word_file', metavar='FILE',
                        help='File with words to look sentences for.')
    parser.add_argument('-o', type=str, dest='output_name', help='Name of output file.')
    parser.add_argument('-w', choices=['dict', 'yourdict'], dest='websites', default='dict',
                        help='Website to download the sentences from.\ndict: Oxford, Collins and Cambridge dictionaries.\nyourdict: yourdict.com website')

    args = parser.parse_args()

    #TODO: add parameters for each dictionary
    if args.websites == 'dict':
        urls = {
            'cam': 'https://dictionary.cambridge.org/dictionary/english/',
            'col': 'https://www.collinsdictionary.com/dictionary/english/',
            'oxf': 'https://www.lexico.com/en/definition/'
        }
    else:
        urls  = {
            'yourdict': 'https://sentence.yourdictionary.com/'
        }

    sentences_by_word = {}
    num_words = 0
    print('Reading words file {}'.format(args.word_file))
    with open(args.word_file) as infile:
        for line in infile:
            num_words += 1

    print('Found {} words.'.format(num_words))
    print('Downloading sentences...')
    with open(args.word_file) as infile:
        for i in tqdm(range(num_words)):
            word = infile.readline().strip()
            sentences_by_word[word] = []

            for website in urls.values():
                website = random.choice(list(urls.keys()))
                base_url = urls[website]
                url = base_url+word
                proxy = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(proxy)
                urllib.request.install_opener(opener)
                retries = 0
                downloaded = False

                while not downloaded:
                    try:
                        req = urllib.request.Request(url, headers=browser_headers)
                        page = urllib.request.urlopen(req).read().decode()
                        downloaded = True
                    except KeyboardInterrupt as e:
                        raise e
                    except (urllib.error.HTTPError, urllib.error.URLError) as e:
                        retries += 1
                        if retries > 5:
                            break
                        proxy_addr = next(proxy_pool)
                        proxy = urllib.request.ProxyHandler({'http': proxy_addr, 'https': proxy_addr})
                        opener = urllib.request.build_opener(proxy)
                        urllib.request.install_opener(opener)

                if not downloaded:
                    print('Error downloading \'{}\''.format(url))
                    continue

                sentences = set(get_sentences(page, website))
                sentences_by_word[word] += list(sentences)

    with open('{}.json'.format(args.output_name), 'w') as wf:
        json.dump(sentences_by_word, wf, ensure_ascii=False, indent=4)
