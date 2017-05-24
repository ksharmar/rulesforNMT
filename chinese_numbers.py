#!/usr/bin/env python

# chinese-numbers.py, 29 June 2005
# David Chiang <dchiang at umiacs.umd.edu>
# Copyright (c) 2005 University of Maryland. All rights reserved.

# Reads a file on stdin, outputs to stdout
# Wraps all detected numbers in an SGML tag
#  <X feature='num' english='1 million'>yi bai wan</X> mei yuan
# This format is (I hope) compatible with both Pharaoh and Hiero

# Bugs:
#  san1 fen1 zhi1 er2 -> two-thirds
#  di4 yi1 -> 1st (esp. because tokenizer attaches di4)
#  80 qian zhao zijie = 80,000 megabytes or 80 gigabytes
#  wu shi ji -> 50-something
#  shu shi wan -> several million
#  san si bai -> three or four hundred
#  san bai qi yi -> 371
#  yi qian ling san shi er -> 1032
#  yi qian ling wu shi -> 1050
#  ba qian qi bai duo wan -> more than 8.7 million
#  years: 1997 nian -> 1997 | in 1997 | 1997 years

import sys, re, optparse
import decimal
import json

# You can change this to gb2312 but it hasn't been tested
encoding = "utf8"

def convert(x):
    if type(x) is dict:
        result = {}
        for (c,val) in x.iteritems():
            c = c.encode(encoding, 'ignore') 
            if c != '':
                result[c] = val
        return result
    else:
        x = [c.encode(encoding, 'ignore') for c in x]
        return [c for c in x if c != '']

def make_re(x):
    return "|".join(x)

def flip(d):
    return dict([(y,x) for (x,y) in d.iteritems()])

# lots of help from Erik Peterson's ChineseNumbers.pm

point = convert([ur"\.", u"\u00b7"]) # Big5 A1 50 -> U+00B7 doesn't get normalized
decimal_re = r"([1-9]\s*(\d\s*){0,2}(,\s*(\d\s*){3})+|[1-9]\s*(\d\s*)*|0)"
frac_re = r"((%s)(\s*\d)+)" % make_re(point)

chinese_minus = convert(u"\u8ca0\u8d1f") # trad, simp

chinese_one = convert({u"\u4e00" : 1})
chinese_zero = convert({"0" : 0, # normalized ideographic zero
                        u"\u96f6" : 0, # ling2
                        u"\u3007" : 0}) # ideographic zero

chinese_digit = convert({u"\u4e8c" : 2,
                         u"\u5169" : 2, # liang (trad)
                         u"\u4e24" : 2, # liang (simp)
                         u"\u4e09" : 3,
                         u"\u56db" : 4,
                         u"\u4e94" : 5,
                         u"\u516d" : 6,
                         u"\u4e03" : 7,
                         u"\u516b" : 8,
                         u"\u4e5d" : 9})
chinese_digit.update(chinese_one)

chinese_point = convert(u"\u9ede\u70b9") # dian (trad, simp)
chinese_decimal_re = "((%s|%s)\s*){3,}" % (make_re(chinese_digit),
                                           make_re(chinese_zero)) # two consecutive digits are usually not numbers
chinese_frac_re = r"((%s)\s*((%s|%s)\s*)+)" % (make_re(chinese_point),
                                                make_re(chinese_digit),
                                                make_re(chinese_zero))

chinese_ten = convert({u"\u5341" : 10,
                       u"\u5344" : 20, # trad
                       u"\u5eff" : 20, # simp
                       u"\u5345" : 30})
chinese_tht = convert({u"\u767e" : 100,
                       u"\u4f70" : 100, # variant
                       u"\u5343" : 1000,
                       u"\u4edf" : 1000}) # variant
chinese_tht.update(chinese_ten)

chinese_exp = convert({u"\u842c" : 1e4, u"\u4e07" : 1e4, # trad, simp
                       u"\u5104" : 1e8, u"\u4ebf" : 1e8, # trad, simp
                       u"\u5146" : 1e12})

chinese_time = convert({u"\u65e5" : 'day', # ri
                        #u"\u865f" : 'day', # hao (trad)
                        #u"\u53f7" : 'day', # hao (simp)
                        u"\u6708" : 'month',
                        #u"\u5e74" : 'year', # too hard to distinguish cardinals and ordinals, but not problematic for TM anyway.
                        })

english_exp = flip({"million" : 1e6, "billion" : 1e9, "trillion" : 1e12})

english_months = flip({'january' : 1, 'february' : 2, 'march' : 3, 'april' : 4,
                      'may' : 5, 'june' : 6, 'july' : 7,'august' : 8,
                      'september' : 9, 'october' : 10, 'november' : 11, 'december' : 12})

english_nums = flip({'one' : 1, 'two' : 2, 'three' : 3, 'four' : 4, 'five' : 5, 'six' : 6, 'seven': 7, 'eight' : 8, 'nine' : 9, 'ten' : 10})

def english_ordinal(i):
    i = int(i)
    if i in [11,12,13] or i % 10 not in [1,2,3]:
        return str(i)+"th"
    else:
        return str(i)+['st','nd','rd'][i%10-1]

# Build the giant regexp used to detect Chinese numbers
n1000_re = make_re([decimal_re,
                    chinese_decimal_re,
                    ("(((%s)\s*(%s)|%s)\s*)+" % (make_re(chinese_digit),
                                                 make_re(chinese_tht),
                                                 make_re(chinese_ten))
                     +
                     "((%s)?\s*(%s)\s*)?" % (make_re(chinese_zero), make_re(chinese_digit))),
                    make_re(chinese_digit),
                    make_re(chinese_tht)])

number_re = make_re([r"(%s)\s*(%s|%s)(\s*(%s))?" % (n1000_re, frac_re, chinese_frac_re, make_re(chinese_exp)),
                     r"((%s)\s*(%s)\s*)*(%s)\s*(%s)" % (n1000_re, make_re(chinese_time),
                                                          n1000_re, make_re(chinese_time)),
                     r"((%s)\s*(%s)\s*)*(%s)(\s*(%s))?" % (n1000_re, make_re(chinese_exp),
                                                           n1000_re, make_re(chinese_exp)),
                     make_re(chinese_exp)])
number_re = r"(^|(?<=\s))(%s)($|(?=\s))" % number_re # only match whole tokens

# Simpler regexp used to segment number into parts
point_re = make_re([make_re(point), make_re(chinese_point)])

scan_re = make_re([make_re("0123456789"),
                   make_re(chinese_zero),
                   make_re(chinese_digit),
                   point_re,
                   make_re(chinese_tht),
                   make_re(chinese_exp),
                   make_re(chinese_time)])

number_re = re.compile(number_re)
scan_re = re.compile(scan_re)
point_re = re.compile(point_re)

def float_to_str(n):
    ctx = decimal.Context()
    ctx.prec = 10
    s = format(ctx.create_decimal(repr(n)), "f")
    s = s.split(".")
    intpart = s[0]
    try:
        fracpart = s[1]
    except IndexError:
        fracpart = "0"

    # don't put commas in four-digit numbers
    # not only is it optional for cardinals, we don't want to mess up
    # years and military times
    if len(intpart) > 4:
        k = len(intpart)%3
        if k > 0:
            accum = [intpart[:k]]
        else:
            accum = []
        for i in xrange(k,len(intpart),3):
            accum.append(intpart[i:i+3])
        intpart = ",".join(accum)

    if fracpart == "0":
        return intpart
    else:
        return "%s.%s" % (intpart, fracpart)

def process_chinese(s, translate_yi=True):
    result = []
    pos = 0
    for m in number_re.finditer(s):
        try:
            french = m.group()
            
            parts = scan_re.findall(french)

            n = 0.0
            t = {}

            # a1000 and a1 hold numbers (0<=a1000<10000 and 0<=a1<10)
            # waiting for their place value to be determined
            # by a power-of-ten word or a succeeding digit

            # we make a subtle distinction here between 0 and 0.0
            # 0 means unset, 0.0 means set to zero
            a1000 = a1 = 0

            # indicates the presumed place value of a1 in a1000
            # we distinguish between 1 and 1.0
            # 1 means that a1000 can be shifted
            placevalue = 1

            for p in parts:
                if chinese_tht.has_key(p):
                    if a1 is 0:
                        a1 = 1.0
                    placevalue = chinese_tht[p]

                a1000 += a1*placevalue

                if chinese_digit.has_key(p) or p.isdigit() and int(p)>0:
                    if chinese_digit.has_key(p):
                        d = chinese_digit[p]
                    else:
                        d = int(p)

                    if a1 is not 0: # is, not ==
                        # two digits in a row: make the right one
                        # ten times smaller or make everything to the
                        # left ten times bigger
                        if placevalue is 1: # is, not ==
                            a1000 *= 10
                        else:
                            placevalue /= 10
                    a1 = float(d)

                elif chinese_zero.has_key(p):
                    if a1 is not 0: # is, not ==
                        if placevalue is 1: # is, not ==
                            a1000 *= 10
                        else:
                            placevalue /= 10
                        a1 = 0.0
                    else: # zero following place-value number means don't prejudice next placevalue
                        placevalue = 1.0
                        a1 = 0
                else:
                    a1 = 0

                    if point_re.match(p):
                        placevalue = 0.1
                    elif chinese_tht.has_key(p):
                        placevalue = chinese_tht[p]/10

                    elif chinese_exp.has_key(p):
                        if a1000 is 0:
                            a1000 = 1.0
                        n += chinese_exp[p] * a1000
                        a1000 = 0
                        placevalue = chinese_exp[p]/10

                    elif chinese_time.has_key(p):
                        t[chinese_time[p]] = int(a1000)
                        a1000 = 0
                        placevalue = 1

            n += a1000 + a1*placevalue
        except:
            sys.stderr.write("warning: couldn't decode number %s\n" % french)
            continue

        try:
            if t != {}: # encode time
                english = []
                e = []
                if t.has_key('month'):
                    e.append(english_months[t['month']])
                if t.has_key('day'):
                    if len(t) == 1: # lone day
                        english += ["the %s" % english_ordinal(t['day']),
                                    "on the %s" % english_ordinal(t['day'])]
                    else:
                        e.append(str(t['day']))
                if t.has_key('day') and t.has_key('year'):
                    e.append(',')
                if t.has_key('year'):
                    e.append(str(t['year']))
                if len(e) > 0:
                    english.append(" ".join(e))
            else: # encode number
                for e in sorted(english_exp.keys(), reverse=True):
                    if n >= e:
                        english = ["%s %s" % (float_to_str(n/e), english_exp[e])]
                        break
                    else:
                        english = [float_to_str(n)]
                if n == int(n) and 1 <= n <= 10:
                    english.append(english_nums[n])
        except:
            sys.stderr.write("warning: couldn't encode number %s or time %s (original: %s)\n" % (repr(n), repr(t), french))
            raise
            continue

        if french in chinese_one and not translate_yi:
            continue
        if len(english) == 0:
            continue

        start = m.start()
        while s[start].isspace():
            start += 1
        end = m.end()
        while s[end-1].isspace():
            end -= 1
        result.append((start, end, english))
        pos = end
    return result

def tokenize_digits(s):
    return re.sub(r"(\d)", r" \1 ", s)

if __name__ == "__main__":
    optparser = optparse.OptionParser()
    optparser.add_option("-1", "--translate-yi", dest="translate_yi", action="store_true", default=False, help="translate yi1 as 1")
    (opts,args) = optparser.parse_args()

    for line in sys.stdin:
        line = line.rstrip()
        spans = process_chinese(line, translate_yi=opts.translate_yi)
        print(json.dumps([tokenize_digits(e[0]).split() for (_,_,e) in spans]))

