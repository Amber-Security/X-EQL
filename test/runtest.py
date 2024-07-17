from holmes_engine.engine import Engine


if __name__ == '__main__':
    # 何不将绕过行为做成宏？
    # 非等式关系：group增量不变，引入支配概念
    test_rule2 = '''
        test_rule: sparse sequence by pid
            [tag1] by (f4, f5):g, (f1, f2):g1, (f3):g2
            [tag2] by (f1, f2):g, (f3):g2, (f5):g3
            [tag3] by (f2, f1):g, (f3, f4):g1, (f5):g3
    '''
    test_rule = '''
        ssh_bruteforce_and_lateral_with_knownhost: sparse sequence
            [ssh_login] by (sessionid):g1
            [read_knownhost] by (sessionid):g1, (localip):g2
            [ssh_login] by (remoteip):g2
    '''
    test_rule3 = '''
        ssh_session_destroy_TO_ssh_login_TO_ssh_session_established_TO_ssh_login_TO_ssh_session_destroy_TO_ssh_login_TO_ssh_login_TO_ssh_session_established_TO_ssh_session_destroy_TO_ssh_session_established_TO_ssh_session_destroy: sparse sequence                                                               
        [ssh_session_destroy] by (sessionid):g1, (laddr):g2, (localip):g2, (remoteip):g3, (type):g4, (exe):g10, (AUID):g11, (UID):g11, (SUID):g11                                                                                                                                                            
        [ssh_login] by (sessionid):g1, (exe):g10, (laddr):g14, (localip):g14, (remoteip):g15, (type):g16, (spid):g18, (suid):g19, (rport):g20, (lport):g21, (UID):g22, (SUID):g22, (AUID):g22                                                                                                                
        [ssh_session_established] by (exe):g10, (AUID):g11, (SUID):g11, (UID):g11, (sessionid):g25, (localip):g26, (laddr):g26, (remoteip):g27, (type):g28, (spid):g30, (suid):g31, (rport):g32, (lport):g33                                                                                                 
        [ssh_login] by (type):g4, (exe):g10, (rport):g20, (lport):g21, (sessionid):g36, (localip):g37, (laddr):g37, (remoteip):g38, (spid):g40, (suid):g41, (AUID):g42, (UID):g42, (SUID):g42                                                                                                                
        [ssh_session_destroy] by (exe):g10, (UID):g22, (AUID):g22, (SUID):g22, (sessionid):g25, (laddr):g26, (localip):g26, (remoteip):g27, (type):g28, (rport):g32, (lport):g33, (pid):g44                                                                                                                  
        [ssh_login] by (exe):g10, (AUID):g11, (UID):g11, (SUID):g11, (sessionid):g25, (laddr):g26, (localip):g26, (remoteip):g27, (type):g28, (spid):g30, (suid):g31, (rport):g32, (lport):g33, (pid):g44                                                                                                    
        [ssh_login] by (type):g4, (exe):g10, (rport):g20, (lport):g21, (sessionid):g36, (localip):g37, (laddr):g37, (remoteip):g38, (spid):g40, (suid):g41, (SUID):g42, (AUID):g42, (UID):g42                                                                                                                
        [ssh_session_established] by (sessionid):g1, (exe):g10, (localip):g14, (laddr):g14, (remoteip):g15, (type):g16, (spid):g18, (suid):g19, (rport):g20, (lport):g21, (SUID):g22, (UID):g22, (AUID):g22                                                                                                  
        [ssh_session_destroy] by (sessionid):g1, (localip):g2, (remoteip):g3, (type):g4, (exe):g10, (laddr):g14, (spid):g18, (suid):g19, (rport):g20, (lport):g21, (SUID):g22, (UID):g22, (AUID):g22                                                                                                         
        [ssh_session_established] by (type):g4, (exe):g10, (rport):g20, (lport):g21, (sessionid):g36, (laddr):g37, (localip):g37, (remoteip):g38, (spid):g40, (suid):g41, (UID):g42, (SUID):g42, (AUID):g42                                                                                                  
        [ssh_session_destroy] by (exe):g10, (AUID):g11, (UID):g11, (SUID):g11, (sessionid):g25, (localip):g26, (laddr):g26, (remoteip):g27, (type):g28, (spid):g30, (suid):g31, (rport):g32, (lport):g33
    '''
    from holmes_rule.rule import load_rule
    from holmes_rule.parser import Parser
    parser = Parser()
    rule = load_rule(parser.parse(rule=test_rule3))
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
    test_events_without_noise4 = [
    {
        "holmes-tag": "ssh_session_destroy",
        "pid": 3480917,
        "sessionid": "9876",
        "localip": "172.25.17.133",
        "remoteip": "192.168.23.4",
        "type": "CRYPTO_KEY_USER",
        "msg": "audit(1720876383.299:219783)",
        "spid": 3481017,
        "suid": 0,
        "rport": 64767,
        "laddr": "172.25.17.133",
        "lport": 22,
        "exe": "/usr/sbin/sshd",
        "UID": "root",
        "AUID": "root",
        "SUID": "root",
        "time": 1720876383
    },
    {
        "holmes-tag": "ssh_login",
        "pid": 1234567,
        "sessionid": "9876",
        "localip": "192.168.1.1",
        "remoteip": "10.0.0.1",
        "type": "CRYPTO_KEY_SERVER",
        "msg": "audit(1720876400.123:456789)",
        "spid": 7654321,
        "suid": 1,
        "rport": 54321,
        "laddr": "192.168.1.1",
        "lport": 2222,
        "exe": "/usr/sbin/sshd",
        "UID": "admin",
        "AUID": "admin",
        "SUID": "admin",
        "time": 1720876400
    },
    {
        "holmes-tag": "ssh_session_established",
        "pid": 987654,
        "sessionid": "5432",
        "localip": "10.0.0.2",
        "remoteip": "192.168.0.1",
        "type": "CRYPTO_KEY_ADMIN",
        "msg": "audit(1720876500.987:654321)",
        "spid": 2468013,
        "suid": 2,
        "rport": 12345,
        "laddr": "10.0.0.2",
        "lport": 22222,
        "exe": "/usr/sbin/sshd",
        "UID": "root",
        "AUID": "root",
        "SUID": "root",
        "time": 1720876500
    },
    {
        "holmes-tag": "ssh_login",
        "pid": 789012,
        "sessionid": "8765",
        "localip": "192.168.2.1",
        "remoteip": "172.16.0.1",
        "type": "CRYPTO_KEY_USER",
        "msg": "audit(1720876600.456:789012)",
        "spid": 5432109,
        "suid": 3,
        "rport": 54321,
        "laddr": "192.168.2.1",
        "lport": 2222,
        "exe": "/usr/sbin/sshd",
        "UID": "user",
        "AUID": "user",
        "SUID": "user",
        "time": 1720876600
    },
    {
        "holmes-tag": "ssh_session_destroy",
        "pid": 9876543,
        "sessionid": "5432",
        "localip": "10.0.0.2",
        "remoteip": "192.168.0.1",
        "type": "CRYPTO_KEY_ADMIN",
        "msg": "audit(1720876700.789:987654)",
        "spid": 1357924,
        "suid": 4,
        "rport": 12345,
        "laddr": "10.0.0.2",
        "lport": 22222,
        "exe": "/usr/sbin/sshd",
        "UID": "admin",
        "AUID": "admin",
        "SUID": "admin",
        "time": 1720876700
    },
    {
        "holmes-tag": "ssh_login",
        "pid": 9876543,
        "sessionid": "5432",
        "localip": "10.0.0.2",
        "remoteip": "192.168.0.1",
        "type": "CRYPTO_KEY_ADMIN",
        "msg": "audit(1720876800.987:654321)",
        "spid": 2468013,
        "suid": 2,
        "rport": 12345,
        "laddr": "10.0.0.2",
        "lport": 22222,
        "exe": "/usr/sbin/sshd",
        "UID": "root",
        "AUID": "root",
        "SUID": "root",
        "time": 1720876800
    },
    {
        "holmes-tag": "ssh_login",
        "pid": 7890123,
        "sessionid": "8765",
        "localip": "192.168.2.1",
        "remoteip": "172.16.0.1",
        "type": "CRYPTO_KEY_USER",
        "msg": "audit(1720876900.456:789012)",
        "spid": 5432109,
        "suid": 3,
        "rport": 54321,
        "laddr": "192.168.2.1",
        "lport": 2222,
        "exe": "/usr/sbin/sshd",
        "UID": "user",
        "AUID": "user",
        "SUID": "user",
        "time": 1720876900
    },
    {
        "holmes-tag": "ssh_session_established",
        "pid": 123456,
        "sessionid": "9876",
        "localip": "192.168.1.1",
        "remoteip": "10.0.0.1",
        "type": "CRYPTO_KEY_SERVER",
        "msg": "audit(1720877000.123:456789)",
        "spid": 7654321,
        "suid": 1,
        "rport": 54321,
        "laddr": "192.168.1.1",
        "lport": 2222,
        "exe": "/usr/sbin/sshd",
        "UID": "admin",
        "AUID": "admin",
        "SUID": "admin",
        "time": 1720877000
    },
    {
        "holmes-tag": "ssh_session_destroy",
        "pid": 34809172,
        "sessionid": "9876",
        "localip": "172.25.17.133",
        "remoteip": "192.168.23.4",
        "type": "CRYPTO_KEY_USER",
        "msg": "audit(1720877100.123:456789)",
        "spid": 7654321,
        "suid": 1,
        "rport": 54321,
        "laddr": "192.168.1.1",
        "lport": 2222,
        "exe": "/usr/sbin/sshd",
        "UID": "admin",
        "AUID": "admin",
        "SUID": "admin",
        "time": 1720877100
    },
    {
        "holmes-tag": "ssh_session_established",
        "pid": 78901234,
        "sessionid": "8765",
        "localip": "192.168.2.1",
        "remoteip": "172.16.0.1",
        "type": "CRYPTO_KEY_USER",
        "msg": "audit(1720877200.456:789012)",
        "spid": 5432109,
        "suid": 3,
        "rport": 54321,
        "laddr": "192.168.2.1",
        "lport": 2222,
        "exe": "/usr/sbin/sshd",
        "UID": "user",
        "AUID": "user",
        "SUID": "user",
        "time": 1720877200
    },
    {
        "holmes-tag": "ssh_session_destroy",
        "pid": 987654321,
        "sessionid": "5432",
        "localip": "10.0.0.2",
        "remoteip": "192.168.0.1",
        "type": "CRYPTO_KEY_ADMIN",
        "msg": "audit(1720877300.987:654321)",
        "spid": 2468013,
        "suid": 2,
        "rport": 12345,
        "laddr": "10.0.0.2",
        "lport": 22222,
        "exe": "/usr/sbin/sshd",
        "UID": "root",
        "AUID": "root",
        "SUID": "root",
        "time": 1720877300
    }
    ]
    for event in test_events_without_noise4:
        engine.process_event(event=event)
    for r in engine.fetch_results():
        print([(r['holmes-tag'], r['time']) for r in r['output']])
