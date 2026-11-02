from .step import Step


class Transform_(Step):
    def process(self, data, inputs, utils):
        data["布種規格"] = data["布種規格"].astype(str)
        data["OP"] = data["布種規格"]
        for op in range(len(data)):
            if ("OP") in data["OP"][op]:
                data["OP"][op] = "1"
            else:
                data["OP"][op] = "0"
        op, _noop = self.trans_op(data)
        _PD, _FD = self.trans_PDFD(data)
        return data

    def trans_op(self, data):
        op = data[(data["OP"] == "1")]
        op = op.reset_index(drop=True)
        noop = data[(data["OP"] == "0")]
        noop = noop.reset_index(drop=True)
        return op, noop

    def trans_PDFD(self, data):
        PD = data[(data["Process"] == 1) | (data["Process"] == 2)]
        PD = PD.reset_index(drop=True)
        FD = data[(data["Process"] != 1) & (data["Process"] != 2)]
        FD = FD.reset_index(drop=True)
        return PD, FD
