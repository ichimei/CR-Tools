import pandas as pd
import util

class CRStation:
    def __init__(self, name, pinyin, tele, conn):
        self.name = name
        self.pinyin = pinyin
        self.tele = tele
        self.conn = conn

    def __str__(self):
        return f'{self.name}, {self.pinyin}, {self.tele}, {self.conn}'

    def __repr__(self):
        return self.__str__()

class CRStations:
    def __init__(self, infos=None, line=None, lazyMap=True):
        self.db = {}
        self.nmMap = util.MultiDict()
        self.pyMap = util.MultiDict()
        if infos is not None:
            for index, station in infos.iterrows():
                content = (CRStation(*station), {line})
                self.db[station.tele] = content
        if not lazyMap:
            self._genMap()

    def _genMap(self):
        for tele, content in self.db.items():
            self.nmMap.add(content[0].name, content)
            self.pyMap.add(content[0].pinyin, content)

    def _mergeIn(self, crs):
        for tele, (station, lines) in crs.db.items():
            if tele in self.db:
                self.db[tele][1].update(lines)
            else:
                self.db[tele] = (station, lines)

    def getName(self, tele):
        return self.db[tele][0].name

    def findTele(self, tele):
        try:
            return self.db[tele]
        except KeyError:
            return None

    def findPinyin(self, pinyin):
        return self.pyMap[pinyin]

    def findName(self, name):
        return self.nmMap[name]

    def teleToName(self, tele):
        try:
            return self.db[tele][0].name
        except KeyError:
            return None

class CRLine:
    def __init__(self, line, num, info):
        self.line = line
        self.num = num
        self.info = info
        self.t2r = {}
        for index, station in info.iterrows():
            self.t2r[station.tele] = index

    def dist(self, tele1, tele2):
        mile1 = self.info.loc[self.t2r[tele1], 'mile']
        mile2 = self.info.loc[self.t2r[tele2], 'mile']
        return abs(mile1 - mile2)

    def getNodes(self, *teleps):
        last = len(self.info) - 1
        for index, station in self.info.iterrows():
            if station.conn or index in (0, last) \
                or station.tele in teleps:
                yield station.tele

    def getEdges(self, *teleps):
        last = len(self.info) - 1
        prev_tele = self.info.loc[0, 'tele']
        prev_mile = 0
        it = self.info.iterrows()
        next(it)
        for index, station in it:
            if not station.conn and index not in (0, last) \
                and station.tele not in teleps:
                continue
            tele = station.tele
            mile = station.mile
            yield (prev_tele, tele, self.line, mile - prev_mile)
            prev_tele, prev_mile = tele, mile

    @classmethod
    def readLine(cls, filename, line, crs=False):
        info = pd.read_excel(filename, header=1, usecols='B,C,D,H,J')
        info.drop(len(info) - 1, inplace=True)
        assert len(info) > 1
        info.columns = ['name', 'pinyin', 'tele', 'mile', 'conn']
        info.mile = info.mile.apply(lambda x: int(x[:-2].replace(',', '')))
        info.conn = info.conn.apply(lambda x: x[0] == 'Y')
        infos = info[['name', 'pinyin', 'tele', 'conn']]
        infol = info[['tele', 'mile', 'conn']]
        if crs:
            return cls(line, len(infol), infol), \
                CRStations(infos, line)
        else:
            return cls(line, len(infol), infol)

class CRNetwork:
    def __init__(self, network, stations):
        self.network = network
        self.stations = stations

    @classmethod
    def readLines(cls, lines):
        network = {}
        stations = CRStations()
        for line in lines:
            crline, crs = CRLine.readLine(line + '.xls', line, crs=True)
            network[line] = crline
            stations._mergeIn(crs)
        stations._genMap()
        return cls(network, stations)

    @classmethod
    def myInit(cls, name, lines=None):
        if lines is None:
            with open('lines.txt') as f:
                lines = f.read().split()
            lines.remove('广肇城际线佛肇线')
            lines = [line for line in lines if '高速' not in line and '城际' not in line]

        ret = cls.readLines(lines)
        return ret

if __name__ == '__main__':
    # CRLine.readLine('京沪线.xls', '京沪线')
    with open('lines.txt') as f:
        lines = f.read().split()
    lines.remove('广肇城际线佛肇线')
    # lines = ['京沪线']
    crnet = CRNetwork.readLines(lines)
    print(crnet.stations.findPinyin('NTO'))
    # print(list(crnet.network['京沪线'].getNodes('-KSH', '-XXX')))
    # print(list(crnet.network['京沪线'].getEdges('-KSH', '-XXX')))
