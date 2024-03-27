#!/usr/bin/env python

import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spoken-language', required=True, type=str, help='spoken language code')
    parser.add_argument('--signed-language', required=True, type=str, help='signed language code')
    parser.add_argument('--input', required=True, type=str, help='input text or signwriting sequence')
    return parser.parse_args()


def signwriting_to_text():
    # pylint: disable=unused-variable
    args = get_args()


def text_to_signwriting():
    # pylint: disable=unused-variable
    args = get_args()


if __name__ == '__main__':
    signwriting_to_text()
