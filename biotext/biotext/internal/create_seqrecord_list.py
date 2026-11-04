from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import re


def create_seqrecord_list(seq_list, header_list=None):
    if header_list is None:
        header_list = list(range(1, len(seq_list) + 1))

    seqrecord_list = []
    for i in range(len(seq_list)):
        description = str(header_list[i])
        ident = re.split("\s+", description)[0]
        record = SeqRecord(Seq(seq_list[i]), description=description, id=ident)
        seqrecord_list.append(record)

    return seqrecord_list
