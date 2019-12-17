# Catch Me If You Can

## Why this program was born?

When I did the assistant of the lecture. Some students highly disagreed with his homework was plagiarism. And this made me so mad. So, I think that if I make the program that collects the evidence of plagiarism and runs it then students will agree on his plagiarism. And I created this.

## Dependencies

This program was made by `python3`. So, you must be installed `python3`. And you have to install below packages by using `pip3`

```bash
tqdm == 4.40.2
nltk == 3.4.5
datasketch == 1.5.0
```

## Details

This program finds the plagiarism by using the MinHash algorithms.

## How to use?

You can use this program like below(also can see this document with `./plagiarism.py -h`)

```bash
usage: plagiarism.py [-h] [-t TEMPLATE] [-o OUTPUT] [-p PATH] [-r REMOVE]
                     [-s SUMMARY]

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATE, --template TEMPLATE
                        set template file
  -o OUTPUT, --output OUTPUT
                        set output file
  -p PATH, --path PATH  set compare files path
  -r REMOVE, --remove REMOVE
                        set remove patterns(regex) in file
  -s SUMMARY, --summary SUMMARY
                        set summary file
```

## TODO

```
- [ ] Support a feature of creating the graph
```
