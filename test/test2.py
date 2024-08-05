'''
清体力测试
'''

from holmes_engine.engine import Engine


if __name__ == '__main__':
    # 何不将绕过行为做成宏？
    # 非等式关系：group增量不变，引入支配概念
    test_rule2 = '''
        test_rule: sequence by pid
            [tag1] by (f4, f5):g, (f1, f2):g1, (f3):g2
            [tag2] by (f1, f2):g, (f3):g2, (f5):g3
            [tag3] by (f2, f1):g, (f3, f4):g1, (f5):g3
    '''
    test_rule = '''
        ssh_bruteforce_and_lateral_with_knownhost: sequence
            [ssh_login] by (sessionid):g1
            [read_knownhost] by (sessionid):g1, (localip):g2
            [ssh_login] by (remoteip):g2
    '''
    from holmes_rule.rule import load_rule
    from holmes_rule.parser import Parser
    parser = Parser()
    rule = load_rule(parser.parse(rule=test_rule2))
    engine = Engine()
    engine.add_holmes_rule(rule=rule)

    test_events_without_noise = [
        {"holmes-tag": "ssh_login", "pid": 111, "sessionid": "aaaa", "localip": "10.2.3.4", "remoteip": "c", "f4": "d", "f5": "e", "time": 1},
        {"holmes-tag": "ssh_login", "pid": 112, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": " ", "f5": "x", "time": 10},
        {"holmes-tag": "tag2-----", "pid": 111, "sessionid": "dddd", "localip": "10.2.3.4", "remoteip": "c", "f4": " ", "f5": "y", "time": 11},
        {"holmes-tag": "read_knownhost", "pid": 112, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": " ", "f5": "x", "time": 12},
        {"holmes-tag": "tag3----------", "pid": 113, "sessionid": "eeee", "localip": "d", "remoteip": "a", "f4": "b", "f5": "y", "time": 20},
        {"holmes-tag": "ssh_login", "pid": 114, "sessionid": "eeee", "localip": "10.2.3.5", "remoteip": "10.2.3.9", "f4": "b", "f5": "x", "time": 21},
        {"holmes-tag": "ssh_login", "pid": 111, "sessionid": "3398", "localip": "10.2.3.5", "remoteip": "10.2.3.4", "f4": "b", "f5": "y", "time": 22},
    ]
    test_events_without_noise2 = [
        {"holmes-tag": "tag1", "pid": 111, "f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e", "time": 1},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 10},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "y", "time": 11},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 12},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 20},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "x", "time": 21},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 22},
    ]

    # test_events_without_noise = [
    #     {"holmes-tag": "tag1", "pid": 111, "f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e", "time": 1},
    #     {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 10},
    #     {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 11},
    #     {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "x", "time": 21},
    # ]
    i = 0
    ts = 0
    while True:
        i += 1
        for event in test_events_without_noise2:
            event["time"] += i * 61
            engine.process_event(event=event)
            ts += 1
        results = engine.fetch_results()
        if i % 10000 != 0: continue
        print("***")
        #print("+++", i, ts, len(engine.fetch_results()))
        #input("pause")
        #continue
        for r in results:
            print(str(i), [(r['holmes-tag'], r['time']) for r in r['output']])