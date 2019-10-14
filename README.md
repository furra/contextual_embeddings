# contextual_embeddings

## Modules required
```sh
$ pip3 install torch pytorch_pretrained_bert pyjarowinkler lxml nltk tqdm allennlp
```

## Download sentences
```sh
$ python3 sentence_downloader.py <word_list_file> <output_json_filename>
```

word_list_file is a plain text file with a word per line
the output json file should be normalized because some sentences can have unicode characters or meta information.

## Create word embedding files
examples:

```sh
$ python3 sentence2word_bert.py sentences.json -u -m avg -o bert_out
$ python3 sentence2word_elmo.py sentences.json -c 0 -m avg -o elmo_out
```
both scripts have a help flag (-h) for description of the arguments

## Additional tools
This script merges two word embedding files:

```sh
$ python3 merge_embeddings.py <vec_file1> <vec_file2> [output_filename]
```
Both word embedding files should have their first line with two numbers: number of words in the file and dimension of the vectors.