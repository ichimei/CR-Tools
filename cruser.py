import crroute as crr
import crerror as cre
import util

class CRRouteUser(crr.CRRoute):
    def teleToName(self, tele):
        return self.stations.teleToName(tele)

    def teleWithName(self, tele):
        return (self.stations.teleToName(tele), tele)

    def parse(self, stname):
        if not isinstance(stname, str):
            raise TypeError('输入必须是 str 类型')

        # tele code
        if stname.startswith('-'):
            if len(stname) != 4 or not stname[1:].isalpha():
                raise CRInputError('电报码格式错误')
            ret = self.stations.findTele(stname)
            if ret is None:
                raise cre.CRNotFoundError(f'找不到电报码为 {stname} 的车站')
            return ret

        # pinyin code
        elif stname.isascii() and stname.isalpha():
            if len(stname) != 3:
                raise cre.CRInputError('拼音码格式错误')
            ret = self.stations.findPinyin(stname)
            if not ret:
                raise cre.CRNotFoundError(f'找不到拼音码为 {stname} 的车站')
            if len(ret) > 1:
                raise cre.CRMultiResultsError(ret, f'拼音码为 {stname} 的车站共有 {len(ret)} 个, 请选择')
            return ret[0]

        # station name
        else:
            ret = self.stations.findName(stname)
            if not ret:
                raise cre.CRNotFoundError(f'找不到名为 {stname} 的车站')
            if len(ret) > 1:
                raise cre.CRMultiResultsError(ret, f'名为 {stname} 的车站共有 {len(ret)} 个, 请选择')
            return ret[0]

    def parseAndChoose(self, stname):
        try:
            return self.parse(stname)
        except cre.CRMultiResultsError as crmre:
            print(crmre.msg)
            results = crmre.results
            print('[序号]: 车站名, 拼音码, 电报码, 是否接算站')
            for i, (crs, _) in enumerate(results):
                crsconn = '是' if crs.conn else '否'
                print(f'[{i}]: {crs.name}, {crs.pinyin}, {crs.tele}, {crsconn}')
            print('[C]: 取消')
            print('你的选择: ', end='')

            while True:
                inp = input().lower()
                if inp == 'c':
                    raise cre.CRCancelError()
                try:
                    num = int(inp)
                    assert num in range(len(results))
                except:
                    print('输入错误, 请重试: ', end='')
                else:
                    return results[num]

    def printPath(self, path, verbose=False):
        prevld = None
        newnodes = []
        newedges = []
        prevEdge = [None, None, 0]
        curmile = 0
        for i in range(len(path.edges)):
            edge = path.edges[i]
            line, mile, dire = edge
            ld = (line, dire)
            if ld == prevld:
                prevEdge[1] += mile
                continue
            else:
                newnodes.append(self.teleWithName(path.nodes[i]))
                prevEdge = [line, mile, dire]
                newedges.append(prevEdge)
                prevld = ld
        newnodes.append(self.teleWithName(path.nodes[-1]))

        print('总里程:', path.dist)
        routename = ''.join(node[0][0] for node in newnodes[1:-1])
        print('经由名:', routename)
        routecode = ''.join(node[1][1:] for node in newnodes[1:-1])
        print('经由略码:', routecode)
        print('经由: ', end='')
        for i in range(len(newedges)):
            print(f'{newnodes[i][0]}', end='')
            print(f'-[{newedges[i][0]}]-', end='')
        print(f'{newnodes[-1][0]}')

        if verbose:
            print()
            print('经由详情:')
            for i in range(len(newedges)):
                name, tele = newnodes[i]
                print(f'{name}, 电报码 {tele}')
                line, mile, dire = newedges[i]
                dire = '下行' if dire else '上行'
                print(f'  ↓')
                print(f'  ↓ {line} ({dire}), 里程 {mile}')
                print(f'  ↓')
            name, tele = newnodes[-1]
            print(f'{name}, 电报码 {tele}')

    def findRouteF(self, start, end, K=1, via=()):
        try:
            start = self.parseAndChoose(start)
            end = self.parseAndChoose(end)
            via = tuple(self.parseAndChoose(v) for v in via)
        except cre.CRCancelError:
            print('操作已取消')
            return

        print()
        print('经由查询确认:')
        print(f'发站: {start[0].name}')
        print(f'到站: {end[0].name}')
        strvia = ', '.join(v[0].name for v in via)
        televia = tuple(v[0].tele for v in via)
        print(f'途经: {strvia}')
        print('正在查询经由......')
        print()

        if K == 1:
            path = super().findRoute(start[0].tele, end[0].tele, televia)
            if path is None:
                print('找不到经由')
            else:
                print('经由信息如下:')
                self.printPath(path, verbose=True)
        else:
            it = super().findRouteK(start[0].tele, end[0].tele, K, televia)
            for i, path in enumerate(it):
                print('=' * 32)
                print()
                print(f'第 {i+1} 条:')
                self.printPath(path)
                print()

if __name__ == '__main__':
    lines = None
    # lines = ['京沪线', '宁启线林南段(南京)']
    cr = CRRouteUser.myInit('lines.txt', lines)
    # crru.findRouteKF('上海', '南通', 5, via=('徐州', '新沂', '海安县'))
    cr.findRouteF('上海', '和田', K=1)
