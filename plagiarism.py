#!/usr/bin/python3
import os
import logging
import argparse
import re

import networkx as nx
import matplotlib.pyplot as plt

import multiprocessing
from multiprocessing.managers import BaseManager

from queue import LifoQueue
from tqdm import tqdm
from datasketch import MinHash

# Logger setting sequence.
logger = logging.getLogger("global")
formatter = logging.Formatter(
    "[%(asctime)s.%(msecs)03d][%(levelname)s:%(lineno)s] %(message)s",
    datefmt="%y-%m-%d %H:%M:%S",
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.setLevel(level=logging.INFO)
logger.addHandler(stream_handler)


##
# @brief This class is required to support multiprocessing LIFO communication.
class data_manager(BaseManager):
    pass


##
# @brief This removes '\r', space and splits text contents by '\n'.
#
# @param source The contents of the source file entered by the user.
#
# @return Text contents list which doesn't have '\r', space.
# and does split by '\n'
def clear_indent(source):
    source = source.replace("\r\n", "\n")
    source = source.split("\n")
    result = []
    for line in source:
        line = line.strip()
        if line:
            result.append(line)
    return "\n".join(result)


##
# @brief Text contents are removed based `remove_pattern`.
#
# @param text Text contents that want to remove the pattern.
# @param remove_pattern The pattern of removing (Rule: regex).
#
# @return Text contents which are removed based on `remove_pattern`.
def remove_comment(text, remove_pattern):
    remove_list = [(remove_pattern, "")]
    for pattern, repl in remove_list:
        text = re.sub(pattern=pattern, repl=repl, string=text)
    return text


##
# @brief Text contents are removed based template file's contents.
#
# @param template The target to remove in the text contents.
# @param text Text contents that want to remove template file's contents.
#
# @return Text contents which are removed based on template file's contents.
def clear_template_code(template, text):
    text = text.split("\n")
    template = template.split("\n")
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


##
# @brief Text contents are formatted based on some rules.
#
# @param text Text contents that want to format.
# @param remove_pattern The pattern of removing (Rule: regex)
# @param template The target to remove in the text contents
#
# @return Foratted text
def cleasing(text, remove_pattern, template=None):
    text = clear_indent(text)
    text = remove_comment(text, remove_pattern)
    text = "\n".join(sorted(text.split("\n"), key=str.lower))
    if template is not None:
        text = clear_template_code(template, text)
    return text


##
# @brief Load template text file
#
# @param template_file_name text file path
# @param remove_pattern The pattern of removing (Rule: regex)
#
# @return Formatted template text contents
def load_template_text(template_file_name, remove_pattern):
    source_file = open(template_file_name, "r")
    text = cleasing(source_file.read(), remove_pattern)
    source_file.close()
    return text


##
# @brief Generate hash value based on text contents.
#
# @param text Text contents which want to make hash value.
# @param remove_pattern The pattern of removing (Rule: regex)
# @param template The target to remove in the text contents.
#
# @return minhash value.
# @note You can get minhash information
# from [link](http://ekzhu.github.io/datasketch/minhash.html)
def prepare_the_word(text, remove_pattern, template):
    text = cleasing(text, remove_pattern, template)
    text = text.replace("\n", " ").split(" ")
    text = [_word for _word in text if _word != ""]
    minhash = MinHash()
    for word in text:
        minhash.update(word.encode("utf8"))
    return minhash


##
# @brief Compare two documents similarity
#
# @param src Comparison criteria file's MinHash
# @param dst Comparison target file's MinHash
#
# @return Similarity of two files.
def compare_two_document(src, dst):
    return src.jaccard(dst)


##
# @brief Compare on criteria file and all the other files.
#
# @param current_name Comparison criteria file.
# @param remove_pattern The pattern of removing (Rule: regex)
# @param file_list Comparison target file list.
# @param lifo_queue LIFO Queue for multiprocessing
# @param template The target to remove in the text contents.
#
# @return None
def compare_file(current_name, remove_pattern, file_list, lifo_queue, template):
    csv_result_list = []
    src_file = open(current_name, "r")
    src = prepare_the_word(src_file.read(), remove_pattern, template)
    for compare_name in file_list:
        if compare_name == current_name:
            continue
        dst_file = open(compare_name, "r")
        dst = prepare_the_word(dst_file.read(), remove_pattern, template)
        src_name = current_name.split(os.path.sep)[-1]
        dst_name = compare_name.split(os.path.sep)[-1]
        csv_result_list += [(src_name, dst_name, compare_two_document(src, dst))]
        dst_file.close()
    src_file.close()
    lifo_queue.put(csv_result_list)


##
# @brief Extract the tuple value and run `compare_file` function.
#
# @param data_set Tuple which contains the arguments of `compare_file` function.
#
# @return None
def compare_file_helper(data_set):
    compare_file(data_set[0], data_set[1], data_set[2], data_set[3], data_set[4])


##
# @brief Compare all input files.
#
# @param file_list File list which want to check.
# @param remove_pattern The pattern of removing (Rule: regex)
# @param template The target to remove in the text contents.
#
# @return CSV string which contains comparing results.
def compare_file_list(file_list, remove_pattern, template):

    # Prepare the LIFO queue.
    data_manager.register("LifoQueue", LifoQueue)

    manager = data_manager()
    manager.start()

    lifo_queue = manager.LifoQueue()

    # Prepare the multprocssing pool
    p = multiprocessing.Pool(multiprocessing.cpu_count())

    logger.info("compare files start")
    data_set = [
        (current_name, remove_pattern, file_list, lifo_queue, template)
        for current_name in file_list
    ]
    p.map(compare_file_helper, tqdm(data_set))
    p.close()
    # Wait until compare files finish.
    p.join()

    # Generate the CSV string sequence.
    csv_result = {"all": "", "summary": {}}
    temp_list = []

    logger.info("get data from LIFO queue")
    while not lifo_queue.empty():
        temp_list += [_row for _row in lifo_queue.get()]

    logger.info("sort the data based on source file name")
    temp_list.sort(key=lambda item: item[0])

    logger.info("make an csv format string")
    csv_result["all"] = "cmp1,cmp2,similarity\n"
    for row in temp_list:
        current_name = row[0]
        compare_name = row[1]
        similarity = row[2]
        csv_result["summary"].setdefault(current_name, -1)
        csv_result["summary"][current_name] = max(
            csv_result["summary"][current_name], similarity
        )
        csv_result["all"] += "{},{},{}\n".format(current_name, compare_name, similarity)

    temp = "id,max similarity\n"
    for key in csv_result["summary"]:
        temp += "{},{}\n".format(key, csv_result["summary"][key])
    csv_result["summary"] = temp
    manager.shutdown()  # Remove LIFO queue
    return csv_result


if __name__ == "__main__":
    # Predefined setting in here
    C_COMMENT_REMOVE_PATTERN = "(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)|(//.*)"

    summary_file_name = "summary.csv"
    result_file_name = "result.csv"
    template_file_name = None
    remove_pattern = C_COMMENT_REMOVE_PATTERN
    files_path = os.getcwd()

    # Get user settings
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--template",
        metavar="<template file name>",
        type=str,
        help="set template file",
    )
    parser.add_argument(
        "-o", "--output", metavar="<output file name>", type=str, help="set output file"
    )
    parser.add_argument(
        "-p",
        "--path",
        metavar="<working path>",
        type=str,
        help="set compare files path",
    )
    parser.add_argument(
        "-r",
        "--remove",
        metavar="<remove regex pattern>",
        type=str,
        help="set remove patterns(regex) in file",
    )
    parser.add_argument(
        "-s",
        "--summary",
        metavar="<summary file name>",
        type=str,
        help="set summary file",
    )
    parser.add_argument(
        "-g",
        "--graph",
        metavar="<graph weight(0.0 ~ 1.0)>",
        type=float,
        help="show associativity graph and set weight(0.0 ~ 1.0)",
    )

    args = parser.parse_args()
    if args.template is not None:
        template_file_name = args.template
        logger.info('current template file "{}"'.format(template_file_name))
    if args.summary is not None:
        summary_file_name = args.summary
    if args.output is not None:
        result_file_name = args.output
    if args.path is not None:
        files_path = args.path
    if args.remove is not None:
        remove_pattern = args.remove

    if files_path[-1] != "/":
        files_path += "/"

    logger.info('current summary file "{}"'.format(summary_file_name))
    logger.info('current output file "{}"'.format(result_file_name))
    logger.info('current files path "{}"'.format(files_path))

    # Get file sequence
    current_file = os.path.split(__file__)[-1]
    exception_file_list = [
        current_file,
        template_file_name,
        result_file_name,
        summary_file_name,
    ]

    file_list = [
        os.path.join(files_path, _file)
        for _file in os.listdir(files_path)
        if os.path.isfile(os.path.join(files_path, _file))
    ]

    # Get template file sequence
    template = None
    if template_file_name is not None and os.path.isfile(template_file_name):
        template = load_template_text(template_file_name, remove_pattern)

    # Run plagiarism detector
    csv_result = compare_file_list(file_list, remove_pattern, template)

    # Write CSV string, contains compare results, to file.
    result_file = open(result_file_name, "w")
    result_file.write(csv_result["all"])
    result_file.close()
    logger.info('complete to save a file in "{}"'.format(result_file_name))

    result_file = open(summary_file_name, "w")
    result_file.write(csv_result["summary"])
    result_file.close()
    logger.info('complete to save a file in "{}"'.format(summary_file_name))

    # Draw the similarity graph
    if args.graph is not None:
        logger.info("graph generate start")
        node_list = [
            _value.split(",")[0]
            for _value in csv_result["summary"].split("\n")[1:]
            if _value != "" and float(_value.split(",")[1]) > args.graph
        ]
        edge_list = [
            tuple(_value.split(",")[0:2])
            for _value in csv_result["all"].split("\n")[1:]
            if _value != "" and float(_value.split(",")[2]) > args.graph
        ]

        G = nx.MultiGraph()
        G.add_nodes_from(node_list)
        G.add_edges_from(edge_list)
        nx.draw_spring(G, with_labels=True)
        plt.show()
