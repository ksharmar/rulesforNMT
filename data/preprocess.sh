#!/bin/bash

BASE=$1

digits() { 
  perl -ne 's/(\d)/ $1 /g; s/\s+/ /g; s/^ //; s/ $//; print "$_\n";' 
}

mkdir -p tok/digits

$HOME/nlp/software/stanford-segmenter/3.6.0/segment-nd.sh $BASE.zh tok/$BASE.zh
digits < tok/$BASE.zh > tok/digits/$BASE.zh
$HOME/nlp/software/moses/3.0/mosesdecoder/scripts/tokenizer/tokenizer.perl -l en < $BASE.en > tok/$BASE.en
digits < tok/$BASE.en > tok/digits/$BASE.en
