'''
Copilot可逆性测试
'''

from holmes_copilot.copilot import Copilot

if __name__ == "__main__":
    test_events_without_noise2 = [
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
    rule = Copilot.generate_rule(test_events_without_noise2)
    from holmes_rule.rule import load_rule
    from holmes_rule.parser import Parser
    from holmes_engine.engine import Engine
    parser = Parser()
    print(rule)
    rule = load_rule(parser.parse(rule=rule))
    rule.max_span = 666666666666
    engine = Engine()
    engine.add_holmes_rule(rule=rule)
    for event in test_events_without_noise2:
        engine.process_event(event=event)
    for r in engine.fetch_results():
        print([(r['holmes-tag'], r['time']) for r in r['output']])
