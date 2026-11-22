
from __future__ import print_function

cdef inline int letterlike(Py_UNICODE c):
    if u'a' <= c <= u'z':
        return 1

    if u'A' <= c <= u'Z':
        return 1

    if u'0' <= c <= u'9':
        return 1

    if u'_' == c:
        return 1

    return 0



def match_logical_word(unicode s, int pos):

    cdef int start = pos
    cdef int len_s = len(s)
    cdef Py_UNICODE c = s[pos]

    if c == u' ':

        pos += 1

        while pos < len_s:
            if not (s[pos] == u' '):
                break

            pos += 1

    elif letterlike(c):

        pos += 1

        while pos < len_s:
            if not letterlike(s[pos]):
                break

            pos += 1

    else:

        pos += 1

    word = s[start:pos]

    if (pos - start) >= 3 and (word[0] == u'_') and (word[1] == u'_'):
        magic = True
    else:
        magic = False


    return s[start:pos], magic, pos







