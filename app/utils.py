# -*- coding:utf-8 -*-


def keywords_split(keywords):
    return keywords.replace(u',', ' ') \
        .replace(u';', ' ') \
        .replace(u'+', ' ') \
        .replace(u'，', ' ') \
        .replace(u'；', ' ') \
        .replace(' ', ' ') \
.split(' ')