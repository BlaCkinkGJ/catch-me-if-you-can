# Catch Me If You Can

## Why this program was born?

When I did the assistant of the lecture. Some students highly disagreed with his homework was plagiarism. And this made me so mad. So, I think that if I make the program that collects the evidence of plagiarism and runs it then students will agree on his plagiarism. And I created this.

## Dependencies

This program was made by `python3`. So, you must be installed `python3`. And you have to install below packages by using `pip3`

```bash
tqdm == 4.40.2
nltk == 3.4.5
datasketch == 1.5.0
matplotlib == 3.1.2
networkx == 2.4
```

## Details

This program finds the plagiarism by using the MinHash algorithms.

## How to use?

You can use this program like below(also can see this document with `./plagiarism.py -h`)

```bash
usage: plagiarism.py [-h] [-t <template file name>] [-o <output file name>]
                     [-p <working path>] [-r <remove regex pattern>]
                     [-s <summary file name>] [-g <graph weight0.0 ~ 1.0>]

optional arguments:
  -h, --help            show this help message and exit
  -t <template file name>, --template <template file name>
                        set template file
  -o <output file name>, --output <output file name>
                        set output file
  -p <working path>, --path <working path>
                        set compare files path
  -r <remove regex pattern>, --remove <remove regex pattern>
                        set remove patterns(regex) in file
  -s <summary file name>, --summary <summary file name>
                        set summary file
  -g <graph weight(0.0 ~ 1.0)>, --graph <graph weight(0.0 ~ 1.0)>
                        show associativity graph and set weight(0.0 ~ 1.0)
```

## TODO

```
- [x] Support a feature of creating the graph
- [ ] Add the function which has the cosine similarity analyzes
- [ ] Add the feature of plagiarism detect which based on c functions
```
