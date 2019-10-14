#!/usr/bin/python3
import json, argparse, torch
from tqdm import tqdm
from random import shuffle
from nltk import word_tokenize #spacy separates hyphenated words
from pyjarowinkler import distance
from pytorch_pretrained_bert import BertTokenizer, BertModel#, BertForMaskedLM

#returns the word index of the most similar word, based on the lowest edit distance
def most_similar_word(sentence: str, word: str) -> str:
    msw = ''
    min_dist = 1000
    for token in word_tokenize(sentence):
        word_dist = 1-distance.get_jaro_distance(word, token, winkler=True)
        if word_dist < min_dist:
            min_dist = word_dist
            msw = token
    return msw

#TODO: implement one random? for word vector (besides average)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates .vec file from example sentences.")

    parser.add_argument('word_file', metavar='FILE',
                        help='File in JSON format with example sentences for each word.')
    parser.add_argument('-o', type=str, dest='output_name', default='bert', help='Name of output file.')
    parser.add_argument('-c', type=int, dest='count', default=0,
                        help='How many sentences to calculate the word vector. 0 means all.')
    parser.add_argument('-m', choices=['avg', 'pick'], dest='method', default='avg',
                        help='Method to calculate the word vector.')
    parser.add_argument('-u', dest='uncased', action='store_true', help='Bert uncased model (default cased).')

    args = parser.parse_args()
    print(args)

    sentences_by_word = json.loads(open(args.word_file).read())
    ndim = 768 #bert dimensions

    if args.uncased:
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertModel.from_pretrained('bert-base-uncased')
    else:
        tokenizer = BertTokenizer.from_pretrained('bert-base-cased', do_lower_case=False)
        model = BertModel.from_pretrained('bert-base-cased')

    model.eval()
    sentences_by_word = list(sentences_by_word.items())

    #TODO: layer(s) by params
    wf1 = open(args.output_name+'_first.vec', 'w')
    wf1.write('{} {}\n'.format(len(sentences_by_word), ndim))
    wf2 = open(args.output_name+'_last.vec', 'w')
    wf2.write('{} {}\n'.format(len(sentences_by_word), ndim))
    wf3 = open(args.output_name+'_sum_all_12.vec', 'w')
    wf3.write('{} {}\n'.format(len(sentences_by_word), ndim))
    wf4 = open(args.output_name+'_2nd_to_last.vec', 'w')
    wf4.write('{} {}\n'.format(len(sentences_by_word), ndim))
    wf5 = open(args.output_name+'_sum_last_four.vec', 'w')
    wf5.write('{} {}\n'.format(len(sentences_by_word), ndim))

    for word, sentences in tqdm(sentences_by_word):
        if args.uncased:
            word = word.lower()
        if not sentences:
            sentences = [word]
        shuffle(sentences)
        if args.count > 0:
            sentences = sentences[:args.count]

        word_vector = {
            'first': torch.zeros(ndim),
            'last': torch.zeros(ndim),
            'sum_all_12': torch.zeros(ndim),
            '2nd_to_last': torch.zeros(ndim),
            'sum_last_four': torch.zeros(ndim)
        }
        vector = {}
        for sentence in sentences:
            if args.uncased:
                sentence = sentence.lower()
            sentence_word = most_similar_word(sentence, word)
            tokenized_word = tokenizer.tokenize(sentence_word)

            tokenized_sentence = tokenizer.tokenize('[CLS] {} [SEP]'.format(sentence))
            tsw_indices = [index for index, token in enumerate(tokenized_sentence)
                           if tokenized_word[0] == token]

            found = False
            for index in tsw_indices:
                found = True
                for i in range(len(tokenized_word)):
                    if tokenized_word[i] != tokenized_sentence[index+i]:
                        found = False
                        break
                if found:
                    tsw_index = index
                    break
            if not found:
                continue
            tsw_end = tsw_index + len(tokenized_word)

            #bert format
            indexed_sentence = tokenizer.convert_tokens_to_ids(tokenized_sentence)
            segments_ids = [1] * len(tokenized_sentence)
            sentence_tensor = torch.tensor([indexed_sentence])
            segments_tensors = torch.tensor([segments_ids])

            with torch.no_grad():
                vectors, _ = model(sentence_tensor, segments_tensors)

            vectors = torch.stack(vectors)

            #merge them?
            try:
                if tsw_index+1 != tsw_end:
                    vector['first'] = vectors[0][0][tsw_index:tsw_end].sum(dim=0)/len(tokenized_word)
                    vector['last'] = vectors[-1][0][tsw_index:tsw_end].sum(dim=0)/len(tokenized_word)
                    vector['sum_all_12'] = vectors.sum(dim=0)[0][tsw_index:tsw_end].sum(dim=0)/len(tokenized_word)
                    vector['2nd_to_last'] = vectors[-2][0][tsw_index:tsw_end].sum(dim=0)/len(tokenized_word)
                    vector['sum_last_four'] = vectors[-4].sum(dim=0)[0][tsw_index:tsw_end].sum(dim=0)/len(tokenized_word)
                else:
                    vector['first'] = vectors[0][0][tsw_index]
                    vector['last'] = vectors[-1][0][tsw_index]
                    vector['sum_all_12'] = vectors.sum(dim=0)[0][tsw_index]
                    vector['2nd_to_last'] = vectors[-2][0][tsw_index]
                    vector['sum_last_four'] = vectors[-4:].sum(dim=0)[0][tsw_index]
            except Exception as e:
                print("==============\nword: {}\nindex:{} - end: {}".format(word, tsw_index, tsw_end))
                print("{}\n==============".format(sentence))
                import pdb; pdb.set_trace()
                raise e

            if args.method == 'avg':
                for layer, vec in vector.items():
                    word_vector[layer] += vec
            #TODO: implement pick

        if len(sentences) > 1:
            for layer in word_vector:
                word_vector[layer] /= len(sentences)

        wf1.write('{} {}\n'.format(word, ' '.join([str(float(n)) for n in word_vector['first']])))
        wf2.write('{} {}\n'.format(word, ' '.join([str(float(n)) for n in word_vector['last']])))
        wf3.write('{} {}\n'.format(word, ' '.join([str(float(n)) for n in word_vector['sum_all_12']])))
        wf4.write('{} {}\n'.format(word, ' '.join([str(float(n)) for n in word_vector['2nd_to_last']])))
        wf5.write('{} {}\n'.format(word, ' '.join([str(float(n)) for n in word_vector['sum_last_four']])))

    wf1.close()
    wf2.close()
    wf3.close()
    wf4.close()
    wf5.close()
