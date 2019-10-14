#!/usr/bin/python3
import sys
from tqdm import tqdm

def get_embeddings(filename):
    embeddings = {}
    with open(filename) as of:
        #first line should be: <num_words> <number_dimensions>
        of.readline()
        for line in of:
            line = line.strip().split()
            embeddings[line[0]] = line[1:]
    return embeddings

if __name__ == '__main__':
    if not (2 < len(sys.argv) < 5):
        print('Usage: python3 {} <vec_file1> <vec_file2> [output_filename]'.format(sys.argv[0]))
        exit()

    embeddings1 = get_embeddings(sys.argv[1])
    embeddings2 = get_embeddings(sys.argv[2])
    swapped = False
    output_filename = sys.argv[3] if len(sys.argv) == 4 else 'merged_embeddings.vec'
    if not output_filename.endswith('.vec'):
        output_filename += '.vec'

    if len(embeddings2) < len(embeddings1):
        embeddings1, embeddings2 = embeddings2, embeddings1
        swapped = True
    # for word in embeddings1:
    for word in list(embeddings1.keys()):
        if word in embeddings2:
            if not swapped:
                embeddings1[word] = embeddings1[word] + embeddings2[word]
            else:
                embeddings1[word] = embeddings2[word] + embeddings1[word]
        else:
            del embeddings1[word]

    del embeddings2
    with open(output_filename, 'w') as wf:
        wf.write('{} {}\n'.format(len(embeddings1), len(embeddings1[next(iter(embeddings1))])))
        for word, vector in embeddings1.items():
        # for word, vector in tqdm(list(embeddings1.items())):
            wf.write('{} {}\n'.format(word, ' '.join(vector)))
