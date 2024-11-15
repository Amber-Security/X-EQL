'''
pk Flink CEP
'''

from holmes_engine.engine import Engine
from time import time


if __name__ == '__main__':
    test_rule = '''
        ssh_bruteforce_and_lateral_with_knownhost: sequence
            [ssh_login] by (proc_sid):g1
            [read_knownhost] by (proc_sid):g1
            [ping_scan] by (proc_sid):g1, (proc_args):g2
            [ssh_logout] by (proc_sid):g1, (fd_sip):g2
    '''
    from holmes_rule.rule import load_rule
    from holmes_rule.parser import Parser
    parser = Parser()
    engine = Engine()
    engine.add_holmes_rule(rule=load_rule(parser.parse(rule=test_rule)))

    base_events = [
        {"holmes-tag": "ssh_login", "proc_sid": "", "proc_args": "", "fd_sip": "", "time": 1},
        {"holmes-tag": "read_knownhost", "proc_sid": "", "proc_args": "", "fd_sip": "", "time": 2},
        {"holmes-tag": "ping_scan", "proc_sid": "", "proc_args": "127.0.0.1", "fd_sip": "", "time": 3},
        {"holmes-tag": "ssh_logout", "proc_sid": "", "proc_args": "", "fd_sip": "127.0.0.1", "time": 4},
    ]
    
    testcase = []
    for i in range(10000):
        testcase.append({"holmes-tag": "ssh_login",      "proc_sid": str(i), "proc_args": "",          "fd_sip": "",          "time": 1 + i*4})
        testcase.append({"holmes-tag": "read_knownhost", "proc_sid": str(i), "proc_args": "",          "fd_sip": "",          "time": 2 + i*4})
        testcase.append({"holmes-tag": "ping_scan",      "proc_sid": str(i), "proc_args": "127.0.0.1", "fd_sip": "",          "time": 3 + i*4})
        testcase.append({"holmes-tag": "ssh_logout",     "proc_sid": str(i), "proc_args": "",          "fd_sip": "127.0.0.1", "time": 4 + i*4})

    s = time()
    for event in testcase:
        engine.process_event(event=event)
    print(time() - s)
    # for r in engine.fetch_results():
    #     print([(r['holmes-tag'], r['time']) for r in r['output']])
    print(len(engine.fetch_results()))
