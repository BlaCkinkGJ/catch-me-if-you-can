#!/usr/bin/python3
import os, sys
import logging, argparse
import re
from multiprocessing import Process
from multiprocessing.managers import BaseManager
from queue import LifoQueue
from tqdm import tqdm
from nltk.tokenize import word_tokenize
from datasketch import MinHash

logger = logging.getLogger("global")
formatter = logging.Formatter('[%(asctime)s.%(msecs)03d][%(levelname)s:%(lineno)s] %(message)s',
        datefmt='%y-%m-%d %H:%M:%S')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.setLevel(level=logging.INFO)
logger.addHandler(stream_handler)

class data_manager(BaseManager):
    pass

def clear_indent(source):
    source = source.split('\n')
    result = []
    for line in source:
        line = line.strip()
        if line: result.append(line)
    return "\n".join(result)

def remove_comment(text, remove_pattern):
    remove_list = [(remove_pattern, '')]
    for pattern, repl in remove_list:
        text = re.sub(pattern=pattern, repl=repl, string=text)
    return text

def clear_template_code(template, text):
    text = text.split('\n')
    template = template.split('\n')
    result = []
    idx = 0
    try:
        for line in text:
            if line == template[idx]:
                idx = idx + 1
            else:
                result.append(line)
    except IndexError:
        pass
    return "\n".join(result)

def cleasing(text, remove_pattern, template=None):
    text = clear_indent(text)
    text = remove_comment(text, remove_pattern)
    text = '\n'.join(sorted(text.split('\n'), key=str.lower))
    if template != None:
        text = clear_template_code(template, text)
    return text

def load_template_text(template_file_name, remove_pattern):
    source_file = open(template_file_name, "r")
    text = cleasing(source_file.read(), remove_pattern)
    source_file.close()
    return text

def prepare_the_word(text, remove_pattern, template):
    text = cleasing(text, remove_pattern, template).replace('\n',' ').split(' ')
    text = [_word for _word in text if _word != '']
    minhash = MinHash()
    for word in text:
        minhash.update(word.encode('utf8'))
    return minhash

def compare_two_document(src, dst):
    return src.jaccard(dst)

def compare_file(current_name, remove_pattern, file_list, lifo_queue):
    csv_result_list = []
    src_file = open(current_name, "r")
    src = prepare_the_word(src_file.read(), remove_pattern, template)
    for compare_name in file_list:
        if compare_name == current_name:
            continue
        dst_file = open(compare_name, "r")
        dst = prepare_the_word(dst_file.read(), remove_pattern, template)
        current_name = current_name.split(os.path.sep)[-1]
        compare_name = compare_name.split(os.path.sep)[-1]
        csv_result_list += [(current_name, compare_name,
            compare_two_document(src, dst))]
        dst_file.close()
    src_file.close()
    lifo_queue.put(csv_result_list)

def compare_file_list(file_list, remove_pattern, template):
    data_manager.register('LifoQueue', LifoQueue)

    manager = data_manager()
    manager.start()

    lifo_queue = manager.LifoQueue()

    procs = []

    logger.info("compare files start")
    for current_name in tqdm(file_list):
        proc = Process(target=compare_file,
                args=(current_name, remove_pattern, file_list, lifo_queue))
        procs.append(proc)
        proc.start()

    for proc in procs:
        proc.join()

    result = ""
    temp_list = []

    logger.info("get data from LIFO queue")
    while not lifo_queue.empty():
        temp_list += [_row for _row in lifo_queue.get()]

    logger.info("sort the data based on source file name")
    temp_list.sort(key = lambda item : item[0])

    logger.info("make an csv format string")
    for row in temp_list:
        current_name = row[0]
        compare_name = row[1]
        similarity = row[2]
        result += "{}, {}, {}\n".format(current_name, compare_name, similarity)
    manager.shutdown()
    return result

if __name__=="__main__":
    C_COMMENT_REMOVE_PATTERN = "(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)|(//.*)"

    template_file_name = 'template.txt'
    result_file_name = 'result.csv'
    remove_pattern = C_COMMENT_REMOVE_PATTERN
    files_path = os.getcwd()

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--template', type=str, help="set template file")
    parser.add_argument('-o', '--output', type=str, help="set output file")
    parser.add_argument('-p', '--path', type=str, help="set compare files path")
    parser.add_argument('-r', '--remove', type=str, help="set remove patterns(regex) in file")

    args = parser.parse_args()
    if args.template != None:
        template_file_name = args.template
    if args.output != None:
        result_file_name = args.output
    if args.path != None:
        files_path = args.path
    if args.remove != None:
        remove_pattern = args.remove

    if files_path[-1] != '/':
        files_path += '/'


    logger.info('current template file "{}"'.format(template_file_name))
    logger.info('current output file "{}"'.format(result_file_name))
    logger.info('current files path "{}"'.format(files_path))

    current_file = os.path.split(__file__)[-1]
    exception_file_list = [current_file, template_file_name, result_file_name]

    if os.path.isfile(result_file_name):
        os.remove(result_file_name)
    file_list = [_file \
            for _file in os.listdir(files_path) \
            if os.path.isfile(os.path.join(files_path, _file))]
    file_list = [files_path+_file \
            for _file in file_list \
            if not _file in exception_file_list]

    template = ""
    if os.path.isfile(template_file_name):
        template = load_template_text(template_file_name, remove_pattern)

    csv_result_string = compare_file_list(file_list, remove_pattern, template)

    # write the csv file
    result_file = open(result_file_name, "w")
    result_file.write("file1, file2, similarity\n"+csv_result_string)
    result_file.close()
    logger.info('complete to save a file in "{}"'.format(result_file_name))
