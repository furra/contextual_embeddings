#!/usr/bin/python3
import os, json, argparse, numpy
from tqdm import tqdm
from random import shuffle
from nltk import word_tokenize #spacy separates hyphenated words
from pyjarowinkler import distance
import re

from allennlp.commands.elmo import ElmoEmbedder

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates .vec file from example sentences.")

    parser.add_argument('word_file', metavar='FILE',
                        help='File in JSON format with example sentences for each word.')
    parser.add_argument('-o', type=str, dest='output_name', default='elmo', help='Name of output file.')
    parser.add_argument('-c', type=int, dest='count', default=0,
                        help='How many sentences to calculate the word vector. 0 means all.')
    #TODO: change for vector construction
    parser.add_argument('-m', choices=['avg', 'pick_one'], dest='method', default='avg',
                        help='Method to calculate the word vector.')
    parser.add_argument('-l', type=int, dest='elmo_layer', default=3, choices=range(1,4),
                        help='Elmo layer to get word embedding.')

    args = parser.parse_args()
    if not args.output_name.endswith('.vec'):
        args.output_name = args.output_name+'.vec'
    print(args)
    args.elmo_layer -= 1

    sentences_by_word = json.loads(open(args.word_file).read())
    word_pat = re.compile(r'[a-z]')
    sub_pat = re.compile(r'\[[^\n\]]+\]') #to delete this thing

    ndim = 1024
    word_vectors = {}

    elmo = ElmoEmbedder()
    for word, sentences in tqdm(list(sentences_by_word.items())):
        if not sentences:
            sentences = [word]
        shuffle(sentences)
        if args.count > 0:
            sentences = sentences[:args.count]
        word_vector = numpy.zeros(ndim)
        for sentence in sentences:
            tokens = []
            word_index = None
            min_dist = 10
            sentence = [token for token in word_tokenize(sub_pat.sub('', sentence))
                        if word_pat.search(token)]
            for index, token in enumerate(sentence):
                tokens.append(token)
                word_dist = 1 - distance.get_jaro_distance(word, token, winkler=True)
                if word_dist < min_dist:
                    min_dist = word_dist
                    word_index = index
            if word_index is None:
                print("word: {} - sentence: {}".format(word, sentence))
                continue

            vectors = elmo.embed_sentence(tokens)
            vector = vectors[args.elmo_layer][word_index]
            if args.method == 'avg':
                word_vector += vector

        if len(sentences) > 1:
            word_vector /= len(sentences)
        word_vectors[word] = word_vector

    with open(args.output_name, 'w') as wf:
        wf.write('{} {}\n'.format(len(word_vectors), ndim))
        for word, vector in tqdm(word_vectors.items()):
            wf.write('{} {}\n'.format(word, ' '.join([str(e) for e in vector])))
