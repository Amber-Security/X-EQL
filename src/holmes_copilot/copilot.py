from typing import Set, List, Dict, Any

from holmes_rule.parser import Parser


class Copilot:
    def __init__(self) -> None:
        pass

    def generate_rule(events:List[Dict]) -> str:
        repeated_tag_cache = {}
        lines = []
        tag_seq = []
        for event in events:
            holmes_tag = event["holmes-tag"]
            if holmes_tag not in repeated_tag_cache: repeated_tag_cache[holmes_tag] = holmes_tag
            repeated_tag_cache[holmes_tag] += '#'
            holmes_tag = repeated_tag_cache[holmes_tag]
            tag_seq.append(holmes_tag)
        default_rule_name = "_TO_".join(tag_seq).replace("#", "")
        head = default_rule_name + ": sparse sequence "
        repeated_tag_cache = {}
        # calc
        value2fields:Dict[Any, Set[str]] = {}
        for event in events:
            holmes_tag = event["holmes-tag"]
            if holmes_tag not in repeated_tag_cache: repeated_tag_cache[holmes_tag] = holmes_tag
            repeated_tag_cache[holmes_tag] += '#'
            holmes_tag = repeated_tag_cache[holmes_tag]
            for field_name in event:
                if field_name == "holmes-tag": continue
                field_value = event[field_name]
                if field_value not in value2fields: value2fields[field_value] = set()
                value2fields[field_value].add('@'.join([holmes_tag, field_name]))
        # generate groups
        event_groups:Dict[str, List] = {}
        for i, v in enumerate(value2fields):
            # gen one group
            fields = value2fields[v]
            gid = 'g' + str(i)
            if len(set([f.split('@')[0] for f in fields])) == 1: continue
            for f in fields:
                holmes_tag, field_name = f.split('@')
                if holmes_tag not in event_groups: event_groups[holmes_tag] = []
                event_groups[holmes_tag].append((gid, field_name))
        # for
        for tag in tag_seq:
            if tag not in event_groups:
                lines.append('\t[' + tag.replace("#", "") + ']')
                continue
            groups = event_groups[tag]
            constraint = ', '.join(['(' + f + '):' + gid for gid, f in groups])
            lines.append('\t[' + tag.replace("#", "") + '] by ' + constraint)
        lines.insert(0, head)
        return '\n'.join(lines)

if __name__ == "__main__":
    test_events_without_noise2 = [
        {"holmes-tag": "tag1", "pid": 111, "f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e", "time": 1},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 10},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "y", "time": 11},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 12},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 20},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "x", "time": 21},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 22},
    ]
    test_events_without_noise = [
        {"holmes-tag": "ssh_login", "pid": 112, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": " ", "f5": "x", "time": 10},
        {"holmes-tag": "read_knownhost", "pid": 113, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": "-", "f5": "z", "time": 12},
        {"holmes-tag": "ssh_login", "pid": 111, "sessionid": "3398", "localip": "10.2.3.5", "remoteip": "10.2.3.4", "f4": "b", "f5": "y", "time": 22},
    ]
    test_events_without_noise3 = [
          {"holmes-tag": "ssh_session_destroy", "pid": 3480917, "sessionid": "9876", "localip": "172.25.17.133", "remoteip": "192.168.23.4", "type": "CRYPTO_KEY_USER", "msg": "audit(1720876383.299:219783)", "spid":3481017, "suid":0 ,"rport":64767 ,"laddr":"172.25.17.133", "lport":22 , "exe":"/usr/sbin/sshd" , "UID": "root", "AUID": "root", "SUID": "root", "time": 1720876383},
    ]

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
    rule = Copilot.generate_rule(test_events_without_noise4)
    print(rule)
